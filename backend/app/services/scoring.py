"""Backend scoring service stubs for AlterScore runtime inference."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import numpy as np

from backend.app.core.artifact_loader import LoadedArtifactBundle
from backend.app.schemas.score import (
    CounterfactualAction,
    ExplanationItem,
    ImprovementTip,
    ScoreRequest,
    ScoreResponse,
)
from backend.ml.explainability.dice_explainer import (
    build_default_persisted_dice_explainer,
)
from backend.ml.explainability.global_importance import FEATURE_DISPLAY_NAMES
from backend.ml.inference.feature_assembly import assemble_request_features
from backend.ml.inference.score_mapper import (
    compute_percentile,
    get_loan_eligibility,
    get_risk_band,
    probability_to_score,
)
from backend.ml.inference.ensemble_adapter import (
    EnsembleInferenceBundle,
    WrappedEnsembleModel,
    predict_ensemble_proba,
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

_MAX_EXPLANATION_ITEMS = 6


class ScoringService:
    """Runtime score service backed by the current loaded artifact bundle."""

    def __init__(self, artifacts: LoadedArtifactBundle) -> None:
        self.artifacts = artifacts
        self.ensemble_bundle: EnsembleInferenceBundle | None = None
        
        if artifacts.report.runtime_model_type == "ensemble" and artifacts.base_models and artifacts.stacking_config:
            self.ensemble_bundle = EnsembleInferenceBundle(
                stacking_model=artifacts.model,
                base_models=artifacts.base_models,
                base_model_order=tuple(artifacts.stacking_config.get("base_model_order", [])),
                preprocessor=artifacts.preprocessor,
                stacking_config=artifacts.stacking_config,
            )

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
            ensemble_bundle=self.ensemble_bundle,
        )
        credit_score = probability_to_score(repayment_probability)
        risk_band = get_risk_band(credit_score)
        percentile = compute_percentile(
            credit_score,
            self.artifacts.population_percentiles,
        )
        shap_contributions = _compute_shap_contributions(
            self.artifacts.shap_explainer,
            processed_features[0],
        )
        explanation_items = _build_explanation_items(
            assembled.feature_row,
            shap_contributions,
        )
        # Use WrappedEnsembleModel for DICE if ensemble is active
        dice_model = (
            WrappedEnsembleModel(self.ensemble_bundle)
            if self.ensemble_bundle is not None
            else self.artifacts.model
        )
        
        counterfactual_actions = _build_counterfactual_actions(
            dice_explainer=self.artifacts.dice_explainer,
            runtime_model_name=self.artifacts.report.runtime_model_name,
            model=dice_model,
            preprocessor=self.artifacts.preprocessor,
            feature_row=assembled.feature_row,
            feature_frame=assembled.feature_frame,
            current_credit_score=credit_score,
            current_probability=repayment_probability,
            shap_contributions=shap_contributions,
        )

        return ScoreResponse.model_validate(
            {
                "session_id": score_request.session_id,
                "credit_score": credit_score,
                "risk_band": risk_band,
                "repayment_probability": round(repayment_probability, 4),
                "percentile": percentile,
                "explanation": [
                    explanation.model_dump(mode="json") for explanation in explanation_items
                ],
                "counterfactual_actions": [
                    action.model_dump(mode="json") for action in counterfactual_actions
                ],
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


def _predict_repayment_probability(
    model: Any,
    processed_features: np.ndarray,
    *,
    ensemble_bundle: EnsembleInferenceBundle | None = None,
) -> float:
    if ensemble_bundle is not None:
        probabilities = predict_ensemble_proba(ensemble_bundle, processed_features)
    else:
        probabilities = np.asarray(model.predict_proba(processed_features), dtype=float)
    if probabilities.ndim != 2 or probabilities.shape[1] < 2:
        raise ValueError("Runtime model predict_proba output must have at least two columns.")

    repayment_probability = float(np.clip(probabilities[0, 1], 0.0, 1.0))
    if np.isnan(repayment_probability):
        raise ValueError("Runtime model produced a NaN repayment probability.")
    return repayment_probability


def _compute_shap_contributions(
    shap_explainer: Any | None,
    processed_row: np.ndarray,
) -> dict[str, float]:
    if shap_explainer is None:
        return {}

    contributions = np.asarray(
        shap_explainer.explain_processed_row(processed_row),
        dtype=float,
    )
    if contributions.ndim != 1:
        return {}

    return {
        feature_name: float(shap_value)
        for feature_name, shap_value in zip(
            tuple(shap_explainer.feature_names),
            contributions.tolist(),
            strict=True,
        )
    }


def _build_explanation_items(
    feature_row: dict[str, Any],
    shap_contributions: dict[str, float],
) -> list[ExplanationItem]:
    if not shap_contributions:
        return []

    explanation_candidates: list[ExplanationItem] = []
    for feature_name, shap_value in sorted(
        shap_contributions.items(),
        key=lambda item: (-abs(item[1]), item[0]),
    ):
        if abs(shap_value) < 1e-6:
            continue

        feature_value = _coerce_numeric_feature_value(feature_row.get(feature_name))
        if feature_value is None:
            continue

        direction = "positive" if shap_value >= 0.0 else "negative"
        display_name = FEATURE_DISPLAY_NAMES.get(
            feature_name,
            feature_name.replace("_", " ").title(),
        )
        explanation_candidates.append(
            ExplanationItem(
                feature=feature_name,
                display_name=display_name,
                shap_value=round(float(shap_value), 4),
                direction=direction,
                feature_value=round(feature_value, 4),
                plain_language=_build_explanation_plain_language(
                    display_name=display_name,
                    direction=direction,
                ),
            )
        )
        if len(explanation_candidates) == _MAX_EXPLANATION_ITEMS:
            break

    return explanation_candidates


def _build_counterfactual_actions(
    *,
    dice_explainer: Any | None,
    runtime_model_name: str | None,
    model: Any,
    preprocessor: Any,
    feature_row: dict[str, Any],
    feature_frame: Any,
    current_credit_score: int,
    current_probability: float,
    shap_contributions: dict[str, float],
) -> list[CounterfactualAction]:
    explainer = dice_explainer or build_default_persisted_dice_explainer(
        model_name=runtime_model_name or "logistic_regression",
    )
    raw_actions = explainer.generate_actions(
        feature_row=feature_row,
        feature_frame=feature_frame,
        model=model,
        preprocessor=preprocessor,
        current_probability=current_probability,
        current_credit_score=current_credit_score,
        shap_contributions=shap_contributions,
    )
    return [
        CounterfactualAction.model_validate(action)
        for action in raw_actions
    ]


def _coerce_numeric_feature_value(value: Any) -> float | None:
    try:
        numeric_value = float(value)
    except (TypeError, ValueError):
        return None

    if not np.isfinite(numeric_value):
        return None
    return numeric_value


def _build_explanation_plain_language(*, display_name: str, direction: str) -> str:
    if direction == "positive":
        return f"{display_name} is supporting the current score."
    return f"{display_name} is pulling the current score down."


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
