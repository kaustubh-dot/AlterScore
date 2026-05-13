"""Backend scoring service stubs for AlterScore runtime inference."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import numpy as np

from backend.app.core.artifact_loader import LoadedArtifactBundle
from backend.app.schemas.score import ImprovementTip, ScoreRequest, ScoreResponse
from backend.ml.inference.feature_assembly import assemble_request_features
from backend.ml.inference.score_mapper import (
    compute_percentile,
    get_loan_eligibility,
    get_risk_band,
    probability_to_score,
)
from backend.ml.preprocessing.pipeline import transform_features

_TIP_LIBRARY: dict[str, tuple[str, str]] = {
    "numeracy_score": (
        "Strengthen financial math",
        "Practice interest, discount, and savings calculations before applying again.",
    ),
    "financial_literacy_score": (
        "Review money basics",
        "Refreshing savings, borrowing, and inflation concepts can improve future applications.",
    ),
    "future_orientation": (
        "Show long-term planning",
        "Consistent future-oriented choices usually support stronger repayment signals.",
    ),
    "conscientiousness_score": (
        "Build repayment habits",
        "Small routines around planning and follow-through can improve creditworthiness signals.",
    ),
    "social_capital_score": (
        "Highlight support systems",
        "Documenting community or family repayment support can strengthen future applications.",
    ),
    "text_agency_score": (
        "Use action-oriented explanations",
        "Describe concrete steps you take to manage setbacks and repayment plans.",
    ),
}


class ScoringService:
    """Runtime score service backed by the current loaded artifact bundle."""

    def __init__(self, artifacts: LoadedArtifactBundle) -> None:
        self.artifacts = artifacts

    def score_request(self, request: ScoreRequest | dict[str, Any]) -> ScoreResponse:
        if self.artifacts.model is None or self.artifacts.preprocessor is None:
            raise ValueError(
                "Scoring requires both a loaded runtime model and preprocessor artifact."
            )

        score_request = (
            request if isinstance(request, ScoreRequest) else ScoreRequest.model_validate(request)
        )
        assembled = assemble_request_features(
            score_request,
            text_pca=self.artifacts.text_pca,
            require_text_pca=True,
        )
        processed_features = transform_features(
            self.artifacts.preprocessor,
            assembled.feature_frame,
        )
        repayment_probability = _predict_repayment_probability(
            self.artifacts.model,
            processed_features,
        )
        credit_score = probability_to_score(repayment_probability)
        risk_band = get_risk_band(credit_score)
        percentile = compute_percentile(
            credit_score,
            self.artifacts.population_percentiles,
        )

        return ScoreResponse.model_validate(
            {
                "session_id": score_request.session_id,
                "credit_score": credit_score,
                "risk_band": risk_band,
                "repayment_probability": round(repayment_probability, 4),
                "percentile": percentile,
                "explanation": [],
                "counterfactual_actions": [],
                "loan_eligibility": get_loan_eligibility(credit_score),
                "improvement_tips": [
                    tip.model_dump(mode="json")
                    for tip in _build_stub_improvement_tips(assembled.feature_row)
                ],
                "timestamp": datetime.now(timezone.utc),
            }
        )


def score_request_with_bundle(
    request: ScoreRequest | dict[str, Any],
    artifacts: LoadedArtifactBundle,
) -> ScoreResponse:
    """Convenience wrapper for one-off scoring calls in tests and future routes."""

    return ScoringService(artifacts).score_request(request)


def _predict_repayment_probability(model: Any, processed_features: np.ndarray) -> float:
    probabilities = np.asarray(model.predict_proba(processed_features), dtype=float)
    if probabilities.ndim != 2 or probabilities.shape[1] < 2:
        raise ValueError("Runtime model predict_proba output must have at least two columns.")

    repayment_probability = float(np.clip(probabilities[0, 1], 0.0, 1.0))
    if np.isnan(repayment_probability):
        raise ValueError("Runtime model produced a NaN repayment probability.")
    return repayment_probability


def _build_stub_improvement_tips(feature_row: dict[str, Any]) -> list[ImprovementTip]:
    tips: list[ImprovementTip] = []
    for feature_name, (title, body) in _TIP_LIBRARY.items():
        feature_value = float(feature_row.get(feature_name, 0.0))
        if feature_value >= 0.6:
            continue
        tips.append(
            ImprovementTip(
                feature=feature_name,
                title=title,
                body=body,
            )
        )
        if len(tips) == 3:
            return tips

    if tips:
        return tips

    return [
        ImprovementTip(
            feature="engagement_score",
            title="Maintain consistent responses",
            body="Clear, consistent answers and careful completion patterns help preserve strong scoring signals.",
        )
    ]


__all__ = [
    "ScoringService",
    "score_request_with_bundle",
]
