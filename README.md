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
