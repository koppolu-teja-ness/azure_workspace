from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

from jsonschema import Draft202012Validator

SCHEMA_PATH = Path("schemas/migration-spec/v1.0.0.schema.json")
SUPPORTED_MAJOR_VERSION = 1


class UnsupportedSpecVersionError(ValueError):
    """Raised when a migration spec major version is not supported."""


def _load_schema(schema_path: Path = SCHEMA_PATH) -> dict[str, Any]:
    payload = json.loads(schema_path.read_text(encoding="utf-8"))
    return cast(dict[str, Any], payload)


def _parse_major(version: str) -> int:
    try:
        major_part = version.split(".", 1)[0]
        return int(major_part)
    except (ValueError, IndexError) as exc:
        raise ValueError(f"Invalid specVersion format: {version}") from exc


def validate_migration_spec_payload(payload: dict[str, Any]) -> list[str]:
    schema = _load_schema()
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(payload), key=lambda err: err.path)
    if errors:
        messages: list[str] = []
        for err in errors:
            location = ".".join(str(part) for part in err.path) or "$"
            messages.append(f"{location}: {err.message}")
        raise ValueError("Schema validation failed: " + " | ".join(messages))

    version = str(payload.get("specVersion", ""))
    major = _parse_major(version)
    if major != SUPPORTED_MAJOR_VERSION:
        raise UnsupportedSpecVersionError(
            f"Unsupported major version {major}. Supported major: {SUPPORTED_MAJOR_VERSION}."
        )

    return _warn_unknown_minor_fields(payload)


def validate_migration_spec_file(spec_path: Path) -> list[str]:
    payload = json.loads(spec_path.read_text(encoding="utf-8"))
    return validate_migration_spec_payload(payload)


def _warn_unknown_minor_fields(payload: dict[str, Any]) -> list[str]:
    allowed_top_level = {
        "specVersion",
        "source",
        "target",
        "resources",
        "dependencies",
        "risk",
        "validationHints",
        "traceability",
    }
    warnings: list[str] = []
    for key in payload:
        if key not in allowed_top_level:
            warnings.append(f"Unknown field at top level: {key}")
    return warnings
