"""Post-Deployment Validation Agent — owner: saurav

Compares live AWS resource state against the Azure source: resource counts,
property parity, functional smoke tests (invoke Lambdas, fetch secrets,
check network reachability), and security-posture diffing. Produces
ValidationResult entries (stage="post_deploy").

Phase 0: stub. Real implementation lives in validation/post_deploy/
(resource_comparator.py, smoke_tests.py, security_posture_diff.py).
"""
from __future__ import annotations

import logging
from typing import Any

from migration_assistant.graph.state import (
    GraphState,
    MigrationStatus,
    ValidationResult,
    ValidationStage,
    ValidationStatus,
)
from migration_assistant.validation.post_deploy.resource_comparator import (
    compare_property_parity,
    compare_resource_counts,
)
from migration_assistant.validation.post_deploy.security_posture_diff import (
    run_security_posture_diff,
)
from migration_assistant.validation.post_deploy.smoke_tests import run_smoke_tests

logger = logging.getLogger(__name__)


def run(state: GraphState) -> dict[str, Any]:
    run_id = state.get("run_id", "unknown-run")
    source_resources = state.get("source_resources", [])
    target_resources = state.get("target_resources", [])
    mappings = state.get("mappings", [])

    if not mappings:
        logger.warning("post_deploy_validation_agent: no mappings available for comparison")
        warning = ValidationResult(
            stage=ValidationStage.POST_DEPLOY,
            resource_id=run_id,
            check_name="post-deploy-validation",
            status=ValidationStatus.WARNING,
            details="No mappings available; skipping structural equivalence checks.",
        )
        return {
            "validation_results": [warning],
            "status": MigrationStatus.VERIFIED,
        }

    results = [
        compare_resource_counts(
            run_id=run_id,
            source_resources=source_resources,
            target_resources=target_resources,
            mappings=mappings,
        )
    ]
    results.extend(
        compare_property_parity(
            run_id=run_id,
            source_resources=source_resources,
            target_resources=target_resources,
            mappings=mappings,
        )
    )
    results.extend(
        run_smoke_tests(
            run_id=run_id,
            source_resources=source_resources,
            target_resources=target_resources,
            mappings=mappings,
        )
    )
    results.extend(
        run_security_posture_diff(
            run_id=run_id,
            target_resources=target_resources,
        )
    )

    has_failures = any(item.status == ValidationStatus.FAIL for item in results)
    status = MigrationStatus.FAILED if has_failures else MigrationStatus.VERIFIED
    logger.info(
        "post_deploy_validation_agent: produced %d checks (%s)",
        len(results),
        status.value,
    )

    return {
        "validation_results": results,
        "status": status,
    }
