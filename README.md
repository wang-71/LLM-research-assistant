# LLM research assistant

An LLM-powered research assistant designed to support systematic literature review, paper analysis, and research planning.
The system is exposed as a FastAPI service and emphasizes structured outputs, schema validation, reproducibility, and traceability.

## Key Features

- Two operating modes

  Topic mode: Literature review driven by a research topic

  PDF mode: Paper-centric analysis using uploaded PDFs

- Schema-first design

  All LLM outputs are validated against a strict JSON schema

  Automatic output coercion and correction to prevent invalid responses

- Reproducibility-oriented outputs

  Explicit reproduction checklists

  Conservative claims when evidence is unclear

- Observability & traceability

  Each run is assigned a unique trace_id

  Execution traces can be retrieved for inspection and debugging

- FastAPI-based service

  Simple REST API

  Interactive Swagger UI for testing

## Running the Service Locally

1. Install Dependencies
```bash
pip install fastapi uvicorn pydantic python-multipart
```

2. Set Environment Variables
```bash
$env:OPENAI_API_KEY="your_api_key"
```

3. Start the FastAPI Server
```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

4. Open Swagger UI
```bash
http://127.0.0.1:8000/docs
```

## Using the Topic Mode via Swagger UI (`/docs`)

After starting the server, open the interactive Swagger UI:

```text
http://127.0.0.1:8000/docs
```

### Step-by-step

1. In Swagger UI, locate **POST `/run/topic`**.
2. Click **POST `/run/topic`** to expand it.
3. Click **Try it out**.
4. In the request body, enter your research topic:

```json
{
  "topic": "reinforcement learning for combinatorial optimization"
}
```

5. Click **Execute**.

### What you will get

The API returns a **strict JSON** object (validated against a schema). The response includes:

- `trace_id`: unique run identifier for debugging and trace retrieval
- `input`: the input payload (mode + topic)
- `related_works` (3–5): ranked papers with `title`, `year`, `url`, and brief contributions
- `reproduction_checklist` (5–10): steps needed to reproduce or re-implement related work
- `action_items` (exactly 5): prioritized next steps (`high` / `medium` / `low`)
- `quality`: schema validation status and self-check metadata

### Example response (schema shape)

```json
{
  "trace_id": "trace_20260204_123456",
  "input": {
    "mode": "topic",
    "topic": "reinforcement learning for combinatorial optimization"
  },
  "related_works": [
    {
      "title": "Example Paper Title",
      "year": 2020,
      "url": "https://arxiv.org/abs/xxxx.xxxxx",
      "key_contribution": "1–2 sentence summary of the key contribution.",
      "relevance_reason": "Why this paper is relevant to the topic."
    }
  ],
  "reproduction_checklist": [
    {
      "task": "Identify datasets / benchmarks used in the paper(s)",
      "why": "Required to reproduce results"
    }
  ],
  "action_items": [
    { "action": "Define the target problem setting and evaluation metrics", "priority": "high" },
    { "action": "Collect and preprocess representative datasets", "priority": "high" },
    { "action": "Re-implement or adapt a strong baseline", "priority": "medium" },
    { "action": "Run ablations and sensitivity analyses", "priority": "medium" },
    { "action": "Document results and draft the related work section", "priority": "low" }
  ],
  "quality": {
    "schema_valid": true,
    "self_checks": ["json_schema_v1"]
  }
}
```

### View execution trace (optional)

Each response contains a `trace_id`. You can retrieve the full execution trace:

```bash
curl http://127.0.0.1:8000/trace/trace_20260204_123456
```


