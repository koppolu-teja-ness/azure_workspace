"""Checkpoint key contract for the Phase 0 workflow."""

from __future__ import annotations


CP_DISCOVERY = "discovery_done"
CP_PARSE_ANALYZE = "parse_analyze_done"
CP_MAPPING = "mapping_done"
CP_CFN_GENERATION = "cfn_generation_done"
CP_STATIC_VALIDATION = "static_validation_done"
CP_REPORTING = "reporting_done"


def checkpoint_key(run_id: str, stage: str) -> str:
	"""Create deterministic checkpoint key used by async orchestration backends."""

	return f"{run_id}:{stage}"
