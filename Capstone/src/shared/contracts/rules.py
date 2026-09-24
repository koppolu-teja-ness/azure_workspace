from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

import yaml
from jsonschema import Draft202012Validator

RULE_SCHEMA_PATH = Path("schemas/rag-rules/v1.0.0.schema.json")


def _load_rule_schema() -> dict[str, Any]:
    payload = json.loads(RULE_SCHEMA_PATH.read_text(encoding="utf-8"))
    return cast(dict[str, Any], payload)


def validate_rule_payload(payload: dict[str, Any]) -> None:
    validator = Draft202012Validator(_load_rule_schema())
    errors = sorted(validator.iter_errors(payload), key=lambda err: err.path)
    if errors:
        messages: list[str] = []
        for err in errors:
            location = ".".join(str(part) for part in err.path) or "$"
            messages.append(f"{location}: {err.message}")
        raise ValueError("Rule schema validation failed: " + " | ".join(messages))


def validate_rule_file(rule_path: Path) -> None:
    payload = yaml.safe_load(rule_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Rule file is not a YAML object: {rule_path}")
    validate_rule_payload(payload)


def validate_rules_in_directory(rules_path: Path) -> int:
    count = 0
    for rule_file in sorted(rules_path.glob("*.yaml")):
        validate_rule_file(rule_file)
        count += 1
    return count
