"""Static Validation Agent - owner: saurav.

Runs deterministic static checks on generated CloudFormation templates:
- schema-validator for fast structural checks
- cfn-lint for CloudFormation syntax/schema validation
- checkov for policy/security checks
"""
from __future__ import annotations

import logging
import tempfile
from pathlib import Path
from typing import Any

from migration_assistant.cfn_generation.template_builder import build_template
from migration_assistant.cfn_generation.yaml_writer import to_yaml
from migration_assistant.graph.state import GraphState, MigrationStatus
from migration_assistant.graph.state import (
    ValidationResult,
    ValidationStage,
    ValidationStatus,
)
from migration_assistant.validation.static.cfn_lint_runner import run_cfn_lint
from migration_assistant.validation.static.checkov_runner import run_checkov
from migration_assistant.validation.static.schema_validator import validate_template_schema

logger = logging.getLogger(__name__)


def run(state: GraphState) -> dict[str, Any]:
    run_id = state.get("run_id", "unknown-run")
    target_resources = state.get("target_resources", [])

    if not target_resources:
        logger.warning("static_validation_agent: no target resources available")
        return {
            "validation_results": [
                ValidationResult(
                    stage=ValidationStage.STATIC,
                    resource_id=run_id,
                    check_name="static-validation",
                    status=ValidationStatus.WARNING,
                    details="No target resources found; static validation skipped.",
                )
            ],
            "status": MigrationStatus.STATIC_VALIDATED,
        }

    template = build_template(target_resources)
    validation_results = validate_template_schema(template, run_id=run_id)

    temp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".yaml",
            encoding="utf-8",
            delete=False,
        ) as handle:
            handle.write(to_yaml(template))
            temp_path = Path(handle.name)

        validation_results.extend(run_cfn_lint(temp_path, run_id=run_id))
        validation_results.extend(run_checkov(temp_path, run_id=run_id))
    except Exception as exc:  # pragma: no cover - defensive path
        logger.exception("static_validation_agent: validation execution failed (%s)", exc)
        validation_results.append(
            ValidationResult(
                stage=ValidationStage.STATIC,
                resource_id=run_id,
                check_name="static-validation",
                status=ValidationStatus.FAIL,
                details=f"Static validation failed: {exc}",
            )
        )
    finally:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)

    fail_count = sum(1 for result in validation_results if result.status == ValidationStatus.FAIL)
    warning_count = sum(
        1 for result in validation_results if result.status == ValidationStatus.WARNING
    )
    logger.info(
        "static_validation_agent: produced %d validation results (%d fail, %d warning)",
        len(validation_results),
        fail_count,
        warning_count,
    )

    return {
        "validation_results": validation_results,
        "status": MigrationStatus.STATIC_VALIDATED,
    }
