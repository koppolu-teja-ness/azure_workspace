"""Deployment Agent — owner: saurav

Deploys approved CloudFormation templates via boto3, in dependency order,
updating per-resource DeploymentCheckpoints (see graph/checkpoints.py) as it
goes.

Phase 0: stub, no live deployment. Real implementation lives in deployment/
(boto3_client.py, cloudformation_deployer.py, rollback.py). Build this
first against the sandbox AWS account from scripts/provision_sandbox.md.
"""
from __future__ import annotations

import logging
from typing import Any

from migration_assistant.graph.state import GraphState, MigrationStatus

logger = logging.getLogger(__name__)


def run(state: GraphState) -> dict[str, Any]:
    logger.info("deployment_agent: stub — no live deployment performed")
    return {
        "status": MigrationStatus.DEPLOYED,
    }
