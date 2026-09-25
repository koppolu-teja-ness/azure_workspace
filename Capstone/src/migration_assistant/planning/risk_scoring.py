"""Risk scoring utilities for the planning agent."""
from __future__ import annotations

from migration_assistant.graph.state import MappingRecord, RiskAssessment, RiskLevel


def assess_risks(
	mappings: list[MappingRecord],
	min_auto_migratable_confidence: float = 0.85,
) -> list[RiskAssessment]:
	"""Classify each mapping into a risk bucket based on confidence and gaps."""
	results: list[RiskAssessment] = []
	for mapping in mappings:
		reasons: list[str] = []
		if mapping.target_logical_id is None:
			reasons.append("No mapped target resource.")
		if mapping.unmapped_properties:
			reasons.append("Unmapped properties present.")

		if mapping.target_logical_id is None:
			level = RiskLevel.HIGH_RISK
		elif mapping.unmapped_properties:
			level = RiskLevel.NEEDS_REVIEW
		elif mapping.confidence < min_auto_migratable_confidence:
			level = RiskLevel.NEEDS_REVIEW
			reasons.append(
				"Mapping confidence below threshold "
				f"{min_auto_migratable_confidence:.2f}."
			)
		else:
			level = RiskLevel.AUTO_MIGRATABLE

		results.append(
			RiskAssessment(
				resource_id=mapping.source_resource_id,
				risk_level=level,
				reasons=reasons,
			)
		)
	return results
