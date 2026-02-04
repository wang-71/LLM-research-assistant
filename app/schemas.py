OUTPUT_SCHEMA_V1 = {
    "type": "object",
    "required": ["trace_id", "input", "related_works", "reproduction_checklist", "action_items", "quality"],
    "properties": {
        "trace_id": {"type": "string"},
        "input": {
            "type": "object",
            "required": ["mode"],
            "properties": {
                "mode": {"type": "string", "enum": ["topic", "pdf"]},
                "topic": {"type": "string"},
                "pdf_name": {"type": "string"}
            },
            "additionalProperties": True
        },
        "related_works": {
            "type": "array",
            "minItems": 3,
            "maxItems": 5,
            "items": {
                "type": "object",
                "required": ["title", "year", "url", "key_contribution"],
                "properties": {
                    "title": {"type": "string"},
                    "year": {"type": "integer"},
                    "venue": {"type": "string"},
                    "url": {"type": "string"},
                    "key_contribution": {"type": "string"},
                    "relevance_reason": {"type": "string"},
                    "citation": {"type": "string"},
                },
                "additionalProperties": True
            }
        },
        "target_paper": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "main_idea": {"type": "string"},
                "method": {"type": "string"},
                "experiment_setup": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["item", "value", "evidence"],
                        "properties": {
                            "item": {"type": "string"},
                            "value": {"type": "string"},
                            "evidence": {
                                "type": "object",
                                "required": ["page", "span"],
                                "properties": {"page": {"type": "integer"}, "span": {"type": "string"}}
                            }
                        }
                    }
                },
                "limitations": {"type": "array", "items": {"type": "string"}},
            },
            "additionalProperties": True
        },
        "reproduction_checklist": {
            "type": "array",
            "minItems": 5,
            "maxItems": 10,
            "items": {
                "type": "object",
                "required": ["task", "why"],
                "properties": {
                    "task": {"type": "string"},
                    "why": {"type": "string"},
                    "evidence": {
                        "type": "object",
                        "properties": {"page": {"type": "integer"}, "span": {"type": "string"}}
                    }
                },
                "additionalProperties": True
            }
        },
        "action_items": {
            "type": "array",
            "minItems": 5,
            "maxItems": 5,
            "items": {
                "type": "object",
                "required": ["action", "priority"],
                "properties": {
                    "action": {"type": "string"},
                    "priority": {"type": "string", "enum": ["high", "medium", "low"]},
                    "owner": {"type": "string"},
                },
                "additionalProperties": True
            }
        },
        "quality": {
            "type": "object",
            "required": ["schema_valid", "self_checks"],
            "properties": {
                "schema_valid": {"type": "boolean"},
                "self_checks": {"type": "array", "items": {"type": "string"}},
                "notes": {"type": "string"},
            },
            "additionalProperties": True
        }
    },
    "additionalProperties": True
}
