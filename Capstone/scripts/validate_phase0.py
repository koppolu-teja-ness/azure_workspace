from __future__ import annotations

from pathlib import Path

from shared.contracts.rules import validate_rules_in_directory
from shared.contracts.spec import validate_migration_spec_file


def main() -> None:
    valid_specs = [
        Path("fixtures/specs/happy-path.json"),
        Path("fixtures/specs/security-edge.json"),
        Path("fixtures/specs/unsupported-construct.json"),
    ]

    for spec_file in valid_specs:
        validate_migration_spec_file(spec_file)

    count = validate_rules_in_directory(Path("knowledgebase/rules"))
    if count < 10:
        raise RuntimeError(f"Expected at least 10 rules, found {count}")

    print("Phase 0 schema gates passed.")


if __name__ == "__main__":
    main()
