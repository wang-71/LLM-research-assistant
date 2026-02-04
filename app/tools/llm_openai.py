# app/tools/llm_openai.py
import os
from typing import Any, Dict, Optional
from openai import OpenAI

OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")

_client: Optional[OpenAI] = None

def get_client() -> OpenAI:
    global _client
    if _client is None:
        key = os.environ.get("OPENAI_API_KEY")
        if not key:
            raise RuntimeError("OPENAI_API_KEY is not set")
        _client = OpenAI(api_key=key)
    return _client

def llm_json(system: str, user: str, schema_hint: str = "") -> Dict[str, Any]:
    """
    Ask OpenAI to return strict JSON and parse it into a dict.
    Compatible across openai SDK versions (no .parsed dependency).
    """
    import json

    client = get_client()
    prompt = user
    if schema_hint:
        prompt += "\n\nJSON FORMAT REQUIREMENTS:\n" + schema_hint

    resp = client.chat.completions.create(
        model=OPENAI_MODEL,
        temperature=0.2,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
        response_format={"type": "json_object"},
    )

    content = resp.choices[0].message.content
    return json.loads(content)

