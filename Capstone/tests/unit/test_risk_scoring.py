from migration_assistant.graph.state import MappingRecord, RiskLevel
from migration_assistant.planning.risk_scoring import assess_risks


def test_assess_risks_marks_low_confidence_as_needs_review() -> None:
	risks = assess_risks(
		mappings=[
			MappingRecord(
				source_resource_id="/r/1",
				target_logical_id="Kv1Secret",
				mapping_rule_id="rule-1",
				confidence=0.7,
			)
		],
		min_auto_migratable_confidence=0.85,
	)

	assert len(risks) == 1
	assert risks[0].risk_level == RiskLevel.NEEDS_REVIEW


def test_assess_risks_marks_unmapped_as_high_risk() -> None:
	risks = assess_risks(
		mappings=[
			MappingRecord(
				source_resource_id="/r/2",
				target_logical_id=None,
				confidence=0.0,
				unmapped_properties=["*"],
			)
		]
	)

	assert len(risks) == 1
	assert risks[0].risk_level == RiskLevel.HIGH_RISK


def test_assess_risks_marks_high_confidence_as_auto_migratable() -> None:
	risks = assess_risks(
		mappings=[
			MappingRecord(
				source_resource_id="/r/3",
				target_logical_id="VpcMain",
				confidence=0.92,
			)
		],
		min_auto_migratable_confidence=0.85,
	)

	assert len(risks) == 1
	assert risks[0].risk_level == RiskLevel.AUTO_MIGRATABLE
