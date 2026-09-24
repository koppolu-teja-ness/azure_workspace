from __future__ import annotations

import json
from pathlib import Path

import pytest

from shared.contracts.consumer import parse_and_build_intermediate
from shared.contracts.spec import (
    UnsupportedSpecVersionError,
    validate_migration_spec_file,
    validate_migration_spec_payload,
)

FIXTURES_PATH = Path("fixtures/specs")


def _load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def test_valid_fixtures_pass_schema_validation() -> None:
    files = [
        FIXTURES_PATH / "happy-path.json",
        FIXTURES_PATH / "security-edge.json",
        FIXTURES_PATH / "unsupported-construct.json",
    ]
    for file in files:
        warnings = validate_migration_spec_file(file)
        assert warnings == []


def test_invalid_fixtures_fail_with_clear_errors() -> None:
    invalid_files = [
        FIXTURES_PATH / "invalid" / "invalid-missing-required.json",
        FIXTURES_PATH / "invalid" / "invalid-decision.json",
    ]
    for file in invalid_files:
        with pytest.raises(ValueError, match="Schema validation failed"):
            validate_migration_spec_file(file)


def test_unsupported_major_version_fails_fast() -> None:
    with pytest.raises(UnsupportedSpecVersionError, match="Unsupported major version"):
        validate_migration_spec_file(FIXTURES_PATH / "invalid" / "invalid-major-version.json")


def test_target_pipeline_parses_all_canonical_fixtures() -> None:
    files = [
        FIXTURES_PATH / "happy-path.json",
        FIXTURES_PATH / "security-edge.json",
        FIXTURES_PATH / "unsupported-construct.json",
    ]
    for file in files:
        payload = _load_json(file)
        out = parse_and_build_intermediate(payload)
        assert out["resourceCount"] >= 1
        assert isinstance(out["fingerprint"], str)
        assert len(out["fingerprint"]) == 64


def test_intermediate_output_is_deterministic() -> None:
    payload = _load_json(FIXTURES_PATH / "happy-path.json")
    first = parse_and_build_intermediate(payload)
    second = parse_and_build_intermediate(payload)
    assert first == second


def test_optional_new_field_compatibility() -> None:
    payload = _load_json(FIXTURES_PATH / "happy-path.json")
    payload["newMinorField"] = "2026.09.24.1"
    warnings = validate_migration_spec_payload(payload)
    assert any("Unknown field" in warning for warning in warnings)
