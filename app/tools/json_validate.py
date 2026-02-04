from jsonschema import Draft202012Validator
from typing import Any, Dict, Tuple, List

def validate_json(payload: Dict[str, Any], schema: Dict[str, Any]) -> Tuple[bool, List[str]]:
    v = Draft202012Validator(schema)
    errors = sorted(v.iter_errors(payload), key=lambda e: e.path)
    msgs = []
    for e in errors[:20]:
        path = ".".join([str(x) for x in e.path]) if e.path else "<root>"
        msgs.append(f"{path}: {e.message}")
    return (len(errors) == 0, msgs)
