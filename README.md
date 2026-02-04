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

### View execution trace

Each response contains a `trace_id`. You can retrieve the full execution trace:

```bash
curl http://127.0.0.1:8000/trace/trace_20260204_123456
```

## Using the PDF Mode via Swagger UI (`/docs`)

The PDF mode allows you to analyze a specific research paper by uploading a PDF file.  
The agent will extract text from the paper and generate structured outputs similar to the topic mode.

After starting the server, open the interactive Swagger UI:

```text
http://127.0.0.1:8000/docs
```

### Step-by-step

1. In Swagger UI, locate **POST `/run/pdf`**.
2. Click **POST `/run/pdf`** to expand it.
3. Click **Try it out**.
4. Upload a research paper in **PDF format** using the file selector.
5. Click **Execute**.

### What you will get

The API returns a **strict JSON** object (validated against a schema).  
The response structure is similar to the topic mode, with additional information extracted directly from the uploaded paper.

The response includes:

- `trace_id`: unique run identifier for debugging and trace retrieval
- `input`: the input payload (mode + pdf file name)
- `related_works` (3–5): related or thematically similar papers
- `target_paper`: structured summary of the uploaded paper, including:
  - main idea and method
  - experimental setup with page-level evidence when available
- `reproduction_checklist` (5–10): steps required to reproduce the reported results
- `action_items` (exactly 5): prioritized next steps for follow-up research
- `quality`: schema validation status and self-check metadata

### Example response (schema shape)

```json
{
  "trace_id": "trace_20260204_234567",
  "input": {
    "mode": "pdf",
    "pdf_name": "example_paper.pdf"
  },
  "related_works": [
    {
      "title": "Related Work Example",
      "year": 2021,
      "url": "https://arxiv.org/abs/yyyy.yyyyy",
      "key_contribution": "Brief summary of the related work.",
      "relevance_reason": "Topically related to the uploaded paper."
    }
  ],
  "target_paper": {
    "title": "Example Paper Title",
    "main_idea": "Concise description of the paper's main idea.",
    "method": "Summary of the proposed method.",
    "experiment_setup": [
      {
        "page": 4,
        "evidence": "Short quoted span describing the experimental setup."
      }
    ]
  },
  "reproduction_checklist": [
    {
      "task": "Reconstruct the experimental environment",
      "why": "Required to reproduce the reported results"
    }
  ],
  "action_items": [
    { "action": "Reproduce baseline experiments", "priority": "high" },
    { "action": "Re-implement the proposed method", "priority": "high" },
    { "action": "Compare against additional baselines", "priority": "medium" },
    { "action": "Run ablation studies", "priority": "medium" },
    { "action": "Document findings and limitations", "priority": "low" }
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
curl http://127.0.0.1:8000/trace/trace_20260204_234567
```

