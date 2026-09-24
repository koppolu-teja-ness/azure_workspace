from __future__ import annotations

from pathlib import Path

import pytest

from shared.contracts.rules import validate_rule_file, validate_rules_in_directory


def test_seed_rules_count_and_schema() -> None:
    rules_dir = Path("knowledgebase/rules")
    count = validate_rules_in_directory(rules_dir)
    assert count >= 10


def test_service_area_rule_coverage() -> None:
    rules_dir = Path("knowledgebase/rules")
    names = [p.name for p in rules_dir.glob("*.yaml")]
    kv = sum(name.startswith("keyvault-") for name in names)
    fn = sum(name.startswith("functions-") for name in names)
    vn = sum(name.startswith("vnet-") for name in names)

    assert kv >= 2
    assert fn >= 2
    assert vn >= 2


def test_rule_linter_rejects_missing_required_fields() -> None:
    with pytest.raises(ValueError, match="Rule schema validation failed"):
        validate_rule_file(Path("tests/fixtures/invalid-rule-missing-field.yaml"))


def test_rule_linter_rejects_invalid_mapping_quality() -> None:
    with pytest.raises(ValueError, match="mappingQuality"):
        validate_rule_file(Path("tests/fixtures/invalid-rule-bad-quality.yaml"))
