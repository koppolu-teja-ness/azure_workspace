"""Static Validation Agent — owner: saurav

Runs cfn-lint, checkov/cfn_nag policy scans, and schema validation on the
generated CloudFormation templates, producing ValidationResult entries
(stage="static").

Phase 0: stub. Real implementation lives in validation/static/
(cfn_lint_runner.py, checkov_runner.py, schema_validator.py).
"""
from __future__ import annotations

import logging
import tempfile
from pathlib import Path
from typing import Any

from migration_assistant.cfn_generation.template_builder import build_template
from migration_assistant.cfn_generation.yaml_writer import to_yaml
from migration_assistant.graph.state import GraphState, MigrationStatus
from migration_assistant.graph.state import ValidationResult, ValidationStage, ValidationStatus
from migration_assistant.validation.static.cfn_lint_runner import run_cfn_lint
from migration_assistant.validation.static.checkov_runner import run_checkov
from migration_assistant.validation.static.schema_validator import validate_template_schema

logger = logging.getLogger(__name__)


def run(state: GraphState) -> dict[str, Any]:
    target_resources = state.get("target_resources", [])
    run_id = state.get("run_id", "unknown-run")
    if not target_resources:
        logger.warning("static_validation_agent: no target resources to validate")
        return {
            "validation_results": [
                ValidationResult(
                    stage=ValidationStage.STATIC,
                    resource_id=run_id,
                    check_name="static-validation",
                    status=ValidationStatus.WARNING,
                    details="No target resources were generated for static validation.",
                )
            ],
            "status": MigrationStatus.STATIC_VALIDATED,
        }

    template = build_template(target_resources)

    results = []
    results.extend(validate_template_schema(template, run_id=run_id))

    with tempfile.TemporaryDirectory(prefix="migration-assistant-") as temp_dir:
        template_path = Path(temp_dir) / "template.yaml"
        template_path.write_text(to_yaml(template), encoding="utf-8")
        results.extend(run_cfn_lint(template_path, run_id=run_id))
        results.extend(run_checkov(template_path, run_id=run_id))

    logger.info("static_validation_agent: produced %d validation results", len(results))
    return {
        "validation_results": results,
        "status": MigrationStatus.STATIC_VALIDATED,
    }
