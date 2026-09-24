from __future__ import annotations

from shared.risk import classify_risk, compute_weighted_score, load_rubric


def test_threshold_boundaries() -> None:
    rubric = load_rubric()
    assert classify_risk(30.0, rubric) == "auto-migratable"
    assert classify_risk(65.0, rubric) == "needs-review"
    assert classify_risk(65.1, rubric) == "high-risk"


def test_sample_scenarios_scored_consistently() -> None:
    rubric = load_rubric()
    scenarios = [
        {
            "identityExposure": 10,
            "networkExposure": 15,
            "unsupportedMappingRisk": 20,
            "blastRadius": 10,
        },
        {
            "identityExposure": 25,
            "networkExposure": 20,
            "unsupportedMappingRisk": 30,
            "blastRadius": 25,
        },
        {
            "identityExposure": 45,
            "networkExposure": 50,
            "unsupportedMappingRisk": 55,
            "blastRadius": 40,
        },
        {
            "identityExposure": 60,
            "networkExposure": 70,
            "unsupportedMappingRisk": 65,
            "blastRadius": 60,
        },
        {
            "identityExposure": 80,
            "networkExposure": 90,
            "unsupportedMappingRisk": 85,
            "blastRadius": 88,
        },
    ]

    first_pass = [compute_weighted_score(item, rubric) for item in scenarios]
    second_pass = [compute_weighted_score(item, rubric) for item in scenarios]

    assert first_pass == second_pass
    assert first_pass[0] < first_pass[-1]
