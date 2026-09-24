from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import yaml


@dataclass(frozen=True)
class RiskThresholds:
    auto_migratable_max: float
    needs_review_max: float


@dataclass(frozen=True)
class RiskWeights:
    identity_exposure: float
    network_exposure: float
    unsupported_mapping_risk: float
    blast_radius: float


@dataclass(frozen=True)
class RiskRubric:
    weights: RiskWeights
    thresholds: RiskThresholds


def load_rubric(path: str = "config/risk-rubric.yaml") -> RiskRubric:
    payload = yaml.safe_load(open(path, encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Invalid risk rubric format")

    weights_map = _expect_dict(payload, "weights")
    thresholds_map = _expect_dict(payload, "thresholds")

    weights = RiskWeights(
        identity_exposure=float(weights_map["identityExposure"]),
        network_exposure=float(weights_map["networkExposure"]),
        unsupported_mapping_risk=float(weights_map["unsupportedMappingRisk"]),
        blast_radius=float(weights_map["blastRadius"]),
    )
    total_weight = (
        weights.identity_exposure
        + weights.network_exposure
        + weights.unsupported_mapping_risk
        + weights.blast_radius
    )
    if abs(total_weight - 1.0) > 1e-9:
        raise ValueError(f"Weights must sum to 1.0, found {total_weight}")

    thresholds = RiskThresholds(
        auto_migratable_max=float(thresholds_map["autoMigratableMax"]),
        needs_review_max=float(thresholds_map["needsReviewMax"]),
    )
    return RiskRubric(weights=weights, thresholds=thresholds)


def compute_weighted_score(dimensions: dict[str, float], rubric: RiskRubric) -> float:
    score = (
        dimensions["identityExposure"] * rubric.weights.identity_exposure
        + dimensions["networkExposure"] * rubric.weights.network_exposure
        + dimensions["unsupportedMappingRisk"] * rubric.weights.unsupported_mapping_risk
        + dimensions["blastRadius"] * rubric.weights.blast_radius
    )
    return round(score, 2)


def classify_risk(score: float, rubric: RiskRubric) -> str:
    if score <= rubric.thresholds.auto_migratable_max:
        return "auto-migratable"
    if score <= rubric.thresholds.needs_review_max:
        return "needs-review"
    return "high-risk"


def score_and_classify(
    dimensions: dict[str, float], rubric: RiskRubric | None = None
) -> dict[str, Any]:
    active_rubric = rubric or load_rubric()
    score = compute_weighted_score(dimensions, active_rubric)
    return {
        "overallScore": score,
        "classification": classify_risk(score, active_rubric),
    }


def _expect_dict(payload: dict[str, Any], key: str) -> dict[str, Any]:
    value = payload.get(key)
    if not isinstance(value, dict):
        raise ValueError(f"Expected map at '{key}'")
    return value
