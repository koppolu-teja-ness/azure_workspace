"""Deployment Agent - owner: saurav.

Builds a dry-run CloudFormation deployment preview using the boto3 wrapper.
No live deployment occurs in Phase 1.
"""
from __future__ import annotations

import logging
from typing import Any

from migration_assistant.cfn_generation.template_builder import build_template
from migration_assistant.cfn_generation.yaml_writer import to_yaml
from migration_assistant.deployment.boto3_client import Boto3ClientFactory
from migration_assistant.deployment.cloudformation_deployer import CloudFormationDeployer
from migration_assistant.graph.state import GraphState, MigrationStatus

logger = logging.getLogger(__name__)


def run(state: GraphState) -> dict[str, Any]:
    config = dict(state.get("config", {}))
    target_resources = state.get("target_resources", [])
    deployment_cfg = config.get("deployment", {})
    if not isinstance(deployment_cfg, dict):
        deployment_cfg = {}

    if not target_resources:
        config["deployment_preview"] = {
            "mode": "dry_run",
            "resource_count": 0,
            "ordered_logical_ids": [],
            "details": "No target resources available for deployment.",
            "live_deploy_requested": bool(deployment_cfg.get("live_deploy", False)),
            "live_deploy_supported": False,
        }
        logger.warning("deployment_agent: no target resources to deploy")
        return {
            "config": config,
            "status": MigrationStatus.DEPLOYED,
        }

    template = build_template(target_resources)
    template_body = to_yaml(template)

    client_factory = Boto3ClientFactory.from_state_config(config)
    deployer = CloudFormationDeployer(
        client_factory=client_factory,
        live_deploy_enabled=False,
    )

    live_deploy_requested = bool(deployment_cfg.get("live_deploy", False))
    preview = deployer.preview_deployment(
        run_id=state.get("run_id", "unknown-run"),
        target_resources=target_resources,
        template_body=template_body,
        stack_name=deployment_cfg.get("stack_name"),
        live_deploy_requested=live_deploy_requested,
    )
    if live_deploy_requested:
        preview["note"] = (
            "Live deployment requested but not supported yet. "
            "Dry-run preview generated only."
        )

    config["deployment_preview"] = preview
    logger.info(
        "deployment_agent: generated dry-run deployment preview for %d resources",
        len(target_resources),
    )

    return {
        "config": config,
        "status": MigrationStatus.DEPLOYED,
    }
