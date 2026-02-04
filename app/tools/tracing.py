import json
import os
import time
import uuid
from typing import Any, Dict, Optional

TRACE_DIR = os.environ.get("TRACE_DIR", "/tmp/traces")

def new_trace_id() -> str:
    return uuid.uuid4().hex

def trace_path(trace_id: str) -> str:
    os.makedirs(TRACE_DIR, exist_ok=True)
    return os.path.join(TRACE_DIR, f"{trace_id}.jsonl")

def write_trace(trace_id: str, event: Dict[str, Any]) -> None:
    event = dict(event)
    event.setdefault("ts", time.time())
    with open(trace_path(trace_id), "a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")

def read_trace(trace_id: str, max_lines: int = 2000) -> str:
    p = trace_path(trace_id)
    if not os.path.exists(p):
        return ""
    lines = []
    with open(p, "r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            if i >= max_lines:
                break
            lines.append(line.rstrip("\n"))
    return "\n".join(lines)
