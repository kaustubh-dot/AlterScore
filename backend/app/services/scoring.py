"""Backend scoring service for AlterScore runtime inference."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
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
from backend.ml.inference.ensemble_adapter import (
    EnsembleInferenceBundle,
    WrappedEnsembleModel,
    build_ensemble_meta_features,
    predict_base_model_proba,
    predict_ensemble_proba,
)
from backend.ml.inference.feature_assembly import assemble_request_features
from backend.ml.inference.score_mapper import (
    compute_percentile,
    get_loan_eligibility,
    get_risk_band,
)
from backend.ml.preprocessing.pipeline import transform_features

from backend.app.core.constants import MAX_EXPLANATION_ITEMS, TIP_LIBRARY

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ScoringPipelineResult:
    response: ScoreResponse
    debug_trace: dict[str, Any]


class ScoringService:
    """Runtime score service backed by the current loaded artifact bundle."""

    def __init__(self, artifacts: LoadedArtifactBundle) -> None:
        self.artifacts = artifacts
        self.ensemble_bundle: EnsembleInferenceBundle | None = None

        if (
            artifacts.report.runtime_model_type == "ensemble"
            and artifacts.base_models
            and artifacts.stacking_config
        ):
            self.ensemble_bundle = EnsembleInferenceBundle(
                stacking_model=artifacts.model,
                base_models=artifacts.base_models,
                base_model_order=tuple(artifacts.stacking_config.get("base_model_order", [])),
                preprocessor=artifacts.preprocessor,
                stacking_config=artifacts.stacking_config,
            )

    def score_request(self, request: ScoreRequest | dict[str, Any]) -> ScoreResponse:
        pipeline_result = self._run_scoring_pipeline(request)
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(
                "AlterScore scoring trace: %s",
                json.dumps(pipeline_result.debug_trace, default=str),
            )
        return pipeline_result.response

    def score_request_debug(self, request: ScoreRequest | dict[str, Any]) -> dict[str, Any]:
        pipeline_result = self._run_scoring_pipeline(request)
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(
                "AlterScore debug-score trace: %s",
                json.dumps(pipeline_result.debug_trace, default=str),
            )
        return pipeline_result.debug_trace

    def _run_scoring_pipeline(
        self,
        request: ScoreRequest | dict[str, Any],
    ) -> ScoringPipelineResult:
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
        preprocessor_debug = _build_preprocessor_debug(
            self.artifacts.preprocessor,
            assembled.feature_frame,
        )
        processed_features = transform_features(
            self.artifacts.preprocessor,
            assembled.feature_frame,
        )
        model_debug = _build_model_debug(
            model=self.artifacts.model,
            processed_features=processed_features,
            ensemble_bundle=self.ensemble_bundle,
        )
        repayment_probability = float(model_debug["repayment_probability"])
        score_mapping_debug = _build_score_mapping_debug(repayment_probability)
        credit_score = int(score_mapping_debug["final_credit_score"])
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
        improvement_tips = _build_improvement_tips(assembled.feature_row)
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

        response = ScoreResponse.model_validate(
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
                    for tip in improvement_tips
                ],
                "timestamp": datetime.now(timezone.utc),
            }
        )
        debug_trace = {
            "raw_input": _to_jsonable(
                request if isinstance(request, dict) else request.model_dump(mode="json")
            ),
            "validated_request": score_request.model_dump(mode="json"),
            "psychometric_features": _to_jsonable(assembled.psychometric_features),
            "raw_behavioral_features": _to_jsonable(assembled.raw_behavioral_features),
            "behavioral_features": _to_jsonable(assembled.behavioral_features),
            "nlp_features": _to_jsonable(assembled.nlp_features),
            "raw_embedding_preview": _to_jsonable(assembled.raw_embedding[:12]),
            "feature_names": list(assembled.feature_frame.columns),
            "feature_row": _to_jsonable(assembled.feature_row),
            "preprocessing": preprocessor_debug,
            "model_debug": model_debug,
            "score_mapping": score_mapping_debug,
            "final_score": {
                "credit_score": credit_score,
                "risk_band": risk_band,
                "percentile": percentile,
                "loan_eligibility": get_loan_eligibility(credit_score),
            },
            "explanation_generation_inputs": {
                "feature_row": _to_jsonable(assembled.feature_row),
                "shap_contributions": _to_jsonable(shap_contributions),
            },
            "explanation": [item.model_dump(mode="json") for item in explanation_items],
            "counterfactual_generation_inputs": {
                "current_probability": round(repayment_probability, 6),
                "current_credit_score": credit_score,
                "feature_row": _to_jsonable(assembled.feature_row),
                "shap_contributions": _to_jsonable(shap_contributions),
            },
            "counterfactual_actions": [
                action.model_dump(mode="json") for action in counterfactual_actions
            ],
            "improvement_tip_inputs": {
                "feature_row": _to_jsonable(assembled.feature_row),
            },
            "improvement_tips": [
                tip.model_dump(mode="json") for tip in improvement_tips
            ],
        }
        return ScoringPipelineResult(response=response, debug_trace=debug_trace)


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


def _build_preprocessor_debug(preprocessor: Any, feature_frame: Any) -> dict[str, Any]:
    numeric_pipeline = preprocessor.named_transformers_["num"]
    categorical_pipeline = preprocessor.named_transformers_["cat"]
    numeric_features = list(preprocessor.transformers_[0][2])
    categorical_features = list(preprocessor.transformers_[1][2])

    numeric_input = feature_frame.loc[:, numeric_features]
    categorical_input = feature_frame.loc[:, categorical_features]
    numeric_imputed = numeric_pipeline.named_steps["imputer"].transform(numeric_input)
    numeric_scaled = numeric_pipeline.named_steps["scaler"].transform(numeric_imputed)
    categorical_imputed = categorical_pipeline.named_steps["imputer"].transform(categorical_input)
    categorical_encoded = categorical_pipeline.named_steps["encoder"].transform(categorical_imputed)
    transformed = preprocessor.transform(feature_frame)

    return {
        "numeric_features": numeric_features,
        "categorical_features": categorical_features,
        "numeric_input": _row_mapping(numeric_features, numeric_input.to_numpy(dtype=float)[0]),
        "numeric_imputed": _row_mapping(numeric_features, numeric_imputed[0]),
        "numeric_scaled": _row_mapping(numeric_features, numeric_scaled[0]),
        "categorical_input": _row_mapping(categorical_features, categorical_input.iloc[0].tolist()),
        "categorical_imputed": _row_mapping(categorical_features, categorical_imputed[0]),
        "categorical_encoded": _row_mapping(categorical_features, categorical_encoded[0]),
        "categorical_encoder_categories": {
            feature_name: list(categories)
            for feature_name, categories in zip(
                categorical_features,
                categorical_pipeline.named_steps["encoder"].categories_,
                strict=True,
            )
        },
        "transformed_feature_vector": _to_jsonable(np.asarray(transformed, dtype=float)[0]),
        "transformed_feature_names": [*numeric_features, *categorical_features],
    }


def _build_model_debug(
    *,
    model: Any,
    processed_features: np.ndarray,
    ensemble_bundle: EnsembleInferenceBundle | None,
) -> dict[str, Any]:
    if ensemble_bundle is None:
        probabilities = np.asarray(model.predict_proba(processed_features), dtype=float)
        repayment_probability = float(np.clip(probabilities[0, 1], 0.0, 1.0))
        return {
            "model_type": "single_model",
            "processed_features_shape": list(processed_features.shape),
            "model_probabilities": _to_jsonable(probabilities),
            "repayment_probability": repayment_probability,
        }

    meta_features = build_ensemble_meta_features(ensemble_bundle, processed_features)
    base_model_outputs: dict[str, Any] = {}
    for model_name in ensemble_bundle.base_model_order:
        raw_output = np.asarray(
            predict_base_model_proba(
                ensemble_bundle.base_models[model_name],
                processed_features,
            ),
            dtype=float,
        )
        base_model_outputs[model_name] = {
            "raw_output": _to_jsonable(raw_output),
            "positive_probability": float(meta_features.raw_base_probabilities[model_name][0]),
        }

    raw_meta_features = np.asarray(meta_features.raw_meta_features_matrix, dtype=float)
    adjusted_meta_features = np.asarray(meta_features.adjusted_meta_features_matrix, dtype=float)
    raw_probabilities = np.asarray(
        ensemble_bundle.stacking_model.predict_proba(raw_meta_features),
        dtype=float,
    )
    calibrated_probabilities = np.asarray(
        ensemble_bundle.stacking_model.predict_proba(adjusted_meta_features),
        dtype=float,
    )
    calibrated_probability = float(np.clip(calibrated_probabilities[0, 1], 0.0, 1.0))
    raw_meta_probability = None
    calibration_details: dict[str, Any] = {
        "stacking_model_type": type(ensemble_bundle.stacking_model).__name__,
    }
    calibrated_classifiers = getattr(ensemble_bundle.stacking_model, "calibrated_classifiers_", None)
    if calibrated_classifiers:
        calibrated_classifier = calibrated_classifiers[0]
        estimator = getattr(calibrated_classifier, "estimator", None)
        if estimator is not None and hasattr(estimator, "predict_proba"):
            raw_meta_probability = float(estimator.predict_proba(adjusted_meta_features)[0, 1])
        calibrators = getattr(calibrated_classifier, "calibrators", None)
        if calibrators is not None:
            calibration_details["calibrators"] = [
                type(calibrator).__name__ for calibrator in calibrators
            ]

    return {
        "model_type": "ensemble",
        "processed_features_shape": list(processed_features.shape),
        "base_model_order": list(ensemble_bundle.base_model_order),
        "base_model_outputs": base_model_outputs,
        "meta_feature_vector": {
            model_name: float(raw_meta_features[0, index])
            for index, model_name in enumerate(ensemble_bundle.base_model_order)
        },
        "adjusted_meta_feature_vector": {
            model_name: float(adjusted_meta_features[0, index])
            for index, model_name in enumerate(ensemble_bundle.base_model_order)
        },
        "meta_feature_matrix": _to_jsonable(raw_meta_features),
        "adjusted_meta_feature_matrix": _to_jsonable(adjusted_meta_features),
        "runtime_mitigation": _to_jsonable(meta_features.mitigation_debug),
        "ensemble_probabilities_before_mitigation": _to_jsonable(raw_probabilities),
        "raw_meta_probability": raw_meta_probability,
        "calibrated_probabilities": _to_jsonable(calibrated_probabilities),
        "repayment_probability": calibrated_probability,
        "calibration_details": calibration_details,
    }


def _build_score_mapping_debug(repayment_probability: float) -> dict[str, Any]:
    clipped_probability = float(np.clip(repayment_probability, 0.01, 0.99))
    log_odds = float(np.log(clipped_probability / (1.0 - clipped_probability)))
    raw_score = 560.0 + (log_odds * 85.0)
    final_credit_score = int(np.clip(raw_score, 300, 850))
    return {
        "raw_repayment_probability": float(repayment_probability),
        "clipped_probability_for_score_mapping": clipped_probability,
        "log_odds": log_odds,
        "raw_score_before_clamp": raw_score,
        "final_credit_score": final_credit_score,
    }


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
        if len(explanation_candidates) == MAX_EXPLANATION_ITEMS:
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


def _row_mapping(feature_names: list[str], values: Any) -> dict[str, Any]:
    return {
        feature_name: _to_jsonable(value)
        for feature_name, value in zip(feature_names, list(values), strict=True)
    }


def _to_jsonable(value: Any) -> Any:
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, np.ndarray):
        return [_to_jsonable(item) for item in value.tolist()]
    if isinstance(value, dict):
        return {str(key): _to_jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_to_jsonable(item) for item in value]
    return value


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


def _build_improvement_tips(feature_row: dict[str, Any]) -> list[ImprovementTip]:
    tips: list[ImprovementTip] = []
    for feature_name, (title, body) in TIP_LIBRARY.items():
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
