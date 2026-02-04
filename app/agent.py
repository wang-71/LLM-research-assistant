import time
from typing import Any, Dict, List

from app.schemas import OUTPUT_SCHEMA_V1
from app.tools.tracing import write_trace, new_trace_id
from app.tools.json_validate import validate_json
from app.tools.paper_search_arxiv import arxiv_search
from app.tools.llm_openai import llm_json

"""
Research Assistant Agent with two modes:
topic mode and PDF mode
"""

# system prompt
SYSTEM = """You are a research assistant agent.
You must produce useful, actionable outputs for reproducing research.
Always output STRICT JSON. Do not include markdown.
If evidence is required and not available, be explicit and keep claims conservative.
"""

# prompt hint for schema (what will the result look like)
SCHEMA_HINT = """Return a JSON object with keys:
trace_id, input, related_works (3-5), reproduction_checklist (5-10), action_items (exactly 5), quality.
For PDF mode, include target_paper with experiment_setup evidence (page, span) whenever possible.
"""

# build user prompt for "topic mode"
def _build_topic_user_prompt(topic: str, papers: List[Dict[str, Any]], trace_id: str) -> str:
    ctx = []
    for p in papers:
        ctx.append(
            f"- Title: {p.get('title','')}\n"
            f"  Year: {p.get('year',0)}\n"
            f"  URL: {p.get('url','')}\n"
            f"  Abstract: {(p.get('abstract','') or '')[:1200]}"
        )
    joined = "\n\n".join(ctx)
    # tell LLM what to do
    return f"""TASK: Given the topic, produce 3-5 related works (from the provided candidates), a reproduction checklist, and exactly 5 action items.

TOPIC: {topic}

CANDIDATE PAPERS (arXiv):
{joined}

Rules:
- Choose the 3–5 MOST RELEVANT papers to the TOPIC from the candidates.
- Rank the selected papers by relevance (most relevant first).
- Each paper: title, year, url, key_contribution (1-2 sentences), relevance_reason (optional).
- Provide a reproduction_checklist of 5-10 items.
- Provide exactly 5 action_items with priority.
"""

# return an empty dict if the output is not a dict
def _force_dict(obj: Any) -> Dict[str, Any]:
    return obj if isinstance(obj, dict) else {}


def _ensure_output_hardened(
    out: Any,
    trace_id: str,
    mode: str,
    topic: str = "",
    pdf_name: str = "",
) -> Dict[str, Any]:
    """
    Defensive normalization to prevent 500s if the model returns wrong types.
    Ensures: out is dict, trace_id exists, input is dict, quality is dict.
    """
    out = _force_dict(out)
    out["trace_id"] = trace_id

    # input must be dict
    inp = out.get("input")
    if not isinstance(inp, dict):
        if mode == "topic":
            out["input"] = {"mode": "topic", "topic": topic}
        else:
            out["input"] = {"mode": "pdf", "pdf_name": pdf_name}
    else:
        out["input"].setdefault("mode", mode)
        if mode == "topic":
            out["input"].setdefault("topic", topic)
        else:
            out["input"].setdefault("pdf_name", pdf_name)

    # quality must be dict
    if not isinstance(out.get("quality"), dict):
        out["quality"] = {}
    out["quality"].setdefault("self_checks", [])
    if not isinstance(out["quality"].get("self_checks"), list):
        out["quality"]["self_checks"] = []

    return out


def _coerce_to_schema_shape(out: Dict[str, Any], mode: str = "topic") -> Dict[str, Any]:
    """
    Convert common 'lazy' model outputs into the object shapes required by OUTPUT_SCHEMA_V1.

    Key fixes:
    1) Promote fields accidentally placed under input.* to top-level.
    2) action_items: list[str] -> list[{"action": str, "priority": "..."}] and ensure exactly 5.
    3) reproduction_checklist: list[str] -> list[{"task": str, "why": "..."}] and ensure 5-10.
    4) related_works: ensure list[dict] with required keys; if missing derive from input.candidate_papers; ensure 3-5.
    5) priority must be one of high/medium/low.
    """
    # ---------- 1) Promote from input.* ----------
    inp = out.get("input")
    if isinstance(inp, dict):
        if "reproduction_checklist" not in out and "reproduction_checklist" in inp:
            out["reproduction_checklist"] = inp.get("reproduction_checklist")
        if "action_items" not in out and "action_items" in inp:
            out["action_items"] = inp.get("action_items")
        if "related_works" not in out and "related_works" in inp:
            out["related_works"] = inp.get("related_works")

    # ---------- 2) action_items ----------
    ai = out.get("action_items")

    if isinstance(ai, str):
        ai = [ai]
        out["action_items"] = ai

    # Convert list[str] -> list[dict]
    if isinstance(ai, list) and (len(ai) == 0 or all(isinstance(x, str) for x in ai)):
        fixed = [{"action": s, "priority": "medium"} for s in ai[:5]]
        while len(fixed) < 5:
            fixed.append({"action": "Define next action item", "priority": "low"})
        out["action_items"] = fixed[:5]

    # Normalize list[dict] and enforce exactly 5
    ai2 = out.get("action_items")
    if isinstance(ai2, list) and all(isinstance(x, dict) for x in ai2):
        fixed2 = []
        for item in ai2[:5]:
            item = dict(item)
            item.setdefault("action", "Define next action item")
            pr = str(item.get("priority", "medium")).lower()
            if pr not in ("high", "medium", "low"):
                pr = "medium"
            item["priority"] = pr
            fixed2.append(item)
        while len(fixed2) < 5:
            fixed2.append({"action": "Define next action item", "priority": "low"})
        out["action_items"] = fixed2[:5]

    # ---------- 3) reproduction_checklist ----------
    rc = out.get("reproduction_checklist")

    if isinstance(rc, str):
        rc = [rc]
        out["reproduction_checklist"] = rc

    # Convert list[str] -> list[dict]
    if isinstance(rc, list) and (len(rc) == 0 or all(isinstance(x, str) for x in rc)):
        fixed = [{"task": s, "why": "Required to reproduce results"} for s in rc[:10]]
        while len(fixed) < 5:
            fixed.append({"task": "Add missing reproduction step", "why": "Required to reproduce results"})
        out["reproduction_checklist"] = fixed[:10]

    # Normalize list[dict] and enforce 5-10
    rc2 = out.get("reproduction_checklist")
    if isinstance(rc2, list) and all(isinstance(x, dict) for x in rc2):
        fixed2 = []
        for item in rc2[:10]:
            item = dict(item)
            item.setdefault("task", "Add reproduction step")
            item.setdefault("why", "Required to reproduce results")
            fixed2.append(item)
        while len(fixed2) < 5:
            fixed2.append({"task": "Add missing reproduction step", "why": "Required to reproduce results"})
        out["reproduction_checklist"] = fixed2[:10]

    # ---------- 4) related_works ----------
    rw = out.get("related_works")

    if isinstance(rw, str):
        rw = [{"title": rw, "year": 0, "url": "", "key_contribution": "Key contribution not provided."}]
        out["related_works"] = rw

    if isinstance(rw, list):
        fixed_rw: List[Dict[str, Any]] = []
        for item in rw[:5]:
            if isinstance(item, dict):
                item = dict(item)
                item.setdefault("title", "Unknown title")

                y = item.get("year", 0)
                if isinstance(y, (int, float)) and y >= 0:
                    item["year"] = int(y)
                elif isinstance(y, str) and y.isdigit():
                    item["year"] = int(y)
                else:
                    item["year"] = 0

                item.setdefault("url", "")
                item.setdefault(
                    "key_contribution",
                    item.get("relevance_reason", "") or "Key contribution not provided.",
                )
                item.setdefault("relevance_reason", "")
                fixed_rw.append(item)
        if fixed_rw:
            out["related_works"] = fixed_rw[:5]

    # If missing/empty, derive from input.candidate_papers
    if (
        "related_works" not in out
        or not isinstance(out.get("related_works"), list)
        or len(out.get("related_works", [])) == 0
    ):
        cand = None
        inp2 = out.get("input")
        if isinstance(inp2, dict):
            cand = inp2.get("candidate_papers")

        if isinstance(cand, list) and len(cand) > 0:
            fixed_rw = []
            for p in cand[:5]:
                if isinstance(p, dict):
                    year = p.get("year", 0)
                    if isinstance(year, (int, float)):
                        year_int = int(year)
                    elif isinstance(year, str) and year.isdigit():
                        year_int = int(year)
                    else:
                        year_int = 0

                    fixed_rw.append(
                        {
                            "title": p.get("title", "Unknown title"),
                            "year": year_int,
                            "url": p.get("url", ""),
                            "key_contribution": p.get("key_contribution") or "Key contribution not provided.",
                            "relevance_reason": p.get("relevance_reason", ""),
                        }
                    )
            out["related_works"] = fixed_rw[:5]

    # Ensure related_works has 3-5 dict items
    rw3 = out.get("related_works")
    if not isinstance(rw3, list):
        out["related_works"] = []
        rw3 = out["related_works"]

    if isinstance(rw3, list):
        rw3 = [x for x in rw3 if isinstance(x, dict)]
        out["related_works"] = rw3[:5]
        while len(out["related_works"]) < 3:
            out["related_works"].append(
                {
                    "title": "Additional related work needed",
                    "year": 0,
                    "url": "",
                    "key_contribution": "Not provided.",
                    "relevance_reason": "",
                }
            )

    # Keep input consistent
    if not isinstance(out.get("input"), dict):
        out["input"] = {"mode": mode}

    return out


def _ensure_quality_required_fields_before_validate(out: Dict[str, Any]) -> None:
    """
    OUTPUT_SCHEMA_V1 requires quality.schema_valid and quality.self_checks.
    These MUST exist before validate_json() is called.
    """
    if not isinstance(out.get("quality"), dict):
        out["quality"] = {}
    out["quality"].setdefault("self_checks", [])
    if not isinstance(out["quality"].get("self_checks"), list):
        out["quality"]["self_checks"] = []
    out["quality"].setdefault("schema_valid", False)  # placeholder


def run_topic_agent(topic: str) -> Dict[str, Any]:
    trace_id = new_trace_id()
    t0 = time.time()
    write_trace(trace_id, {"event": "start", "mode": "topic", "topic": topic})

    # Step 1: search arXiv
    s0 = time.time()
    papers = arxiv_search(topic, k=10)
    write_trace(
        trace_id,
        {"event": "tool_result", "tool": "arxiv_search", "t": time.time() - s0, "n": len(papers)},
    )

    prompt = _build_topic_user_prompt(topic, papers, trace_id)

    last_errors: List[str] = []
    out: Dict[str, Any] = {}

    for attempt in range(1, 3):
        a0 = time.time()
        write_trace(trace_id, {"event": "llm_call", "attempt": attempt})

        raw = llm_json(SYSTEM, prompt, schema_hint=SCHEMA_HINT)

        out = _ensure_output_hardened(raw, trace_id=trace_id, mode="topic", topic=topic)
        out = _coerce_to_schema_shape(out, mode="topic")

        # IMPORTANT: required quality fields must exist before schema validation
        _ensure_quality_required_fields_before_validate(out)

        ok, errs = validate_json(out, OUTPUT_SCHEMA_V1)

        out["quality"]["schema_valid"] = ok
        out["quality"]["self_checks"] = list(set(out["quality"]["self_checks"] + ["json_schema_v1"]))

        write_trace(
            trace_id,
            {"event": "validate", "attempt": attempt, "ok": ok, "errors": errs[:8], "t": time.time() - a0},
        )

        if ok:
            write_trace(trace_id, {"event": "done", "total_s": time.time() - t0})
            return out

        last_errors = errs
        prompt = (
            prompt
            + "\n\nVALIDATION ERRORS:\n"
            + "\n".join(last_errors[:12])
            + "\nFix the JSON to satisfy the schema."
        )

    # best effort return
    if not isinstance(out.get("quality"), dict):
        out["quality"] = {}
    out["quality"].setdefault("self_checks", [])
    out["quality"]["schema_valid"] = False
    out["quality"]["notes"] = "Schema validation failed after retries: " + "; ".join(last_errors[:8])
    write_trace(trace_id, {"event": "done_with_errors", "total_s": time.time() - t0})
    return out


def run_pdf_agent(pdf_name: str, pdf_text: str) -> Dict[str, Any]:
    trace_id = new_trace_id()
    t0 = time.time()
    write_trace(trace_id, {"event": "start", "mode": "pdf", "pdf_name": pdf_name, "chars": len(pdf_text)})

    prompt = f"""TASK: You are given extracted text of a paper. Produce:
- related_works: 3-5 (you may infer typical related works categories if exact citations not present; be explicit if uncertain)
- target_paper: title/main_idea/method + experiment_setup[] with evidence (page, span) when available
- reproduction_checklist: 5-10
- action_items: exactly 5

PAPER TEXT (with page tags like [PAGE 1], [PAGE 2]...):
{pdf_text[:180000]}

Rules:
- For experiment_setup evidence, quote a SHORT span (<= 200 chars) and include page number.
- Keep claims conservative if the text is unclear.
"""

    last_errors: List[str] = []
    out: Dict[str, Any] = {}

    for attempt in range(1, 3):
        a0 = time.time()
        write_trace(trace_id, {"event": "llm_call", "attempt": attempt})

        raw = llm_json(SYSTEM, prompt, schema_hint=SCHEMA_HINT)

        out = _ensure_output_hardened(raw, trace_id=trace_id, mode="pdf", pdf_name=pdf_name)
        out = _coerce_to_schema_shape(out, mode="pdf")

        # IMPORTANT: required quality fields must exist before schema validation
        _ensure_quality_required_fields_before_validate(out)

        ok, errs = validate_json(out, OUTPUT_SCHEMA_V1)

        out["quality"]["schema_valid"] = ok
        out["quality"]["self_checks"] = list(set(out["quality"]["self_checks"] + ["json_schema_v1"]))

        write_trace(
            trace_id,
            {"event": "validate", "attempt": attempt, "ok": ok, "errors": errs[:8], "t": time.time() - a0},
        )

        if ok:
            write_trace(trace_id, {"event": "done", "total_s": time.time() - t0})
            return out

        last_errors = errs
        prompt = (
            prompt
            + "\n\nVALIDATION ERRORS:\n"
            + "\n".join(last_errors[:12])
            + "\nFix the JSON to satisfy the schema."
        )

    # best effort return
    if not isinstance(out.get("quality"), dict):
        out["quality"] = {}
    out["quality"].setdefault("self_checks", [])
    out["quality"]["schema_valid"] = False
    out["quality"]["notes"] = "Schema validation failed after retries: " + "; ".join(last_errors[:8])
    write_trace(trace_id, {"event": "done_with_errors", "total_s": time.time() - t0})
    return out
