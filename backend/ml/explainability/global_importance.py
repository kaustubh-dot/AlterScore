"""Offline global-importance report generation for AlterScore."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Final

import numpy as np

from backend.app.core.paths import MODEL_REPORTS_DIR
from backend.ml.evaluation.metrics import select_best_test_auc_model
from backend.ml.preprocessing.feature_registry import ALL_MODEL_FEATURES

DEFAULT_GLOBAL_IMPORTANCE_PATH: Final[Path] = (
    MODEL_REPORTS_DIR / "global_importance.json"
)
GLOBAL_IMPORTANCE_DECIMALS: Final[int] = 4
EXACT_LINEAR_IMPORTANCE_PREFERENCE: Final[tuple[str, ...]] = (
    "logistic_regression",
)
NATIVE_IMPORTANCE_PREFERENCE: Final[tuple[str, ...]] = (
    "xgboost",
    "lightgbm",
    "random_forest",
)
GLOBAL_IMPORTANCE_SOURCE_PREFERENCE: Final[tuple[str, ...]] = (
    *NATIVE_IMPORTANCE_PREFERENCE,
    *EXACT_LINEAR_IMPORTANCE_PREFERENCE,
)
PSYCHOMETRIC_FEATURES: Final[tuple[str, ...]] = (
    "numeracy_score",
    "CRT_score",
    "financial_literacy_score",
    "future_orientation",
    "delay_discounting_rate",
    "risk_attitude",
    "risk_consistency_flag",
    "loss_aversion_score",
    "locus_of_control",
    "conscientiousness_score",
    "social_capital_score",
    "honesty_score",
    "resilience_score",
    "reciprocity_norm",
)
BEHAVIORAL_FEATURES: Final[tuple[str, ...]] = (
    "avg_response_time_ms",
    "answer_change_rate",
    "session_duration_sec",
    "dropout_count",
    "scroll_hesitation_score",
    "risk_response_speed_ratio",
    "typing_speed_wpm",
    "device_type",
    "time_of_day",
)
NLP_FEATURES: Final[tuple[str, ...]] = (
    "text_sentiment_compound",
    "text_agency_score",
    "text_problem_solving_flag",
    "text_semantic_dim1",
    "text_semantic_dim2",
)
DERIVED_FEATURES: Final[tuple[str, ...]] = (
    "psychological_credit_index",
    "cognitive_consistency_index",
    "repayment_intention_score",
    "impulsivity_index",
    "cognitive_load_index",
    "engagement_score",
    "behavioral_trust_score",
)
FEATURE_CATEGORY_LOOKUP: Final[dict[str, str]] = {
    **{feature_name: "psychometric" for feature_name in PSYCHOMETRIC_FEATURES},
    **{feature_name: "behavioral" for feature_name in BEHAVIORAL_FEATURES},
    **{feature_name: "nlp" for feature_name in NLP_FEATURES},
    **{feature_name: "derived" for feature_name in DERIVED_FEATURES},
}
FEATURE_DISPLAY_NAMES: Final[dict[str, str]] = {
    "numeracy_score": "Numeracy Score",
    "CRT_score": "CRT Score",
    "financial_literacy_score": "Financial Literacy Score",
    "future_orientation": "Future Orientation",
    "delay_discounting_rate": "Delay Discounting Rate",
    "risk_attitude": "Risk Attitude",
    "risk_consistency_flag": "Risk Consistency Flag",
    "loss_aversion_score": "Loss Aversion Score",
    "locus_of_control": "Locus Of Control",
    "conscientiousness_score": "Conscientiousness Score",
    "social_capital_score": "Social Capital Score",
    "honesty_score": "Honesty Score",
    "resilience_score": "Resilience Score",
    "reciprocity_norm": "Reciprocity Norm",
    "avg_response_time_ms": "Average Response Time (ms)",
    "answer_change_rate": "Answer Change Rate",
    "session_duration_sec": "Session Duration (sec)",
    "dropout_count": "Dropout Count",
    "scroll_hesitation_score": "Scroll Hesitation Score",
    "risk_response_speed_ratio": "Risk Response Speed Ratio",
    "typing_speed_wpm": "Typing Speed (WPM)",
    "device_type": "Device Type",
    "time_of_day": "Time Of Day",
    "text_sentiment_compound": "Text Sentiment Compound",
    "text_agency_score": "Text Agency Score",
    "text_problem_solving_flag": "Text Problem Solving Flag",
    "text_semantic_dim1": "Text Semantic Dimension 1",
    "text_semantic_dim2": "Text Semantic Dimension 2",
    "psychological_credit_index": "Psychological Credit Index",
    "cognitive_consistency_index": "Cognitive Consistency Index",
    "repayment_intention_score": "Repayment Intention Score",
    "impulsivity_index": "Impulsivity Index",
    "cognitive_load_index": "Cognitive Load Index",
    "engagement_score": "Engagement Score",
    "behavioral_trust_score": "Behavioral Trust Score",
}


def build_global_importance_report_for_candidate_models(
    candidate_models: dict[str, Any],
    *,
    train_processed_features: np.ndarray,
    test_processed_features: np.ndarray,
    model_stats: list[dict[str, Any]],
    candidate_model_types: dict[str, str] | None = None,
    feature_names: list[str] | tuple[str, ...] = tuple(ALL_MODEL_FEATURES),
) -> tuple[dict[str, Any], str]:
    """Build the dashboard-ready global-importance payload for the best source model."""

    if not candidate_models:
        raise ValueError("At least one candidate model is required for global importance.")

    resolved_feature_names = list(feature_names)
    resolved_model_types = candidate_model_types or {}
    selected_model_name = _select_importance_source_model(
        candidate_models,
        model_stats=model_stats,
    )
    importance_values = _extract_importance_values(
        candidate_models[selected_model_name],
        train_processed_features=train_processed_features,
        test_processed_features=test_processed_features,
        feature_count=len(resolved_feature_names),
    )

    report_rows = [
        {
            "feature": feature_name,
            "display_name": FEATURE_DISPLAY_NAMES[feature_name],
            "mean_abs_shap": round(float(importance_value), GLOBAL_IMPORTANCE_DECIMALS),
            "category": FEATURE_CATEGORY_LOOKUP[feature_name],
        }
        for feature_name, importance_value in zip(
            resolved_feature_names,
            importance_values.tolist(),
            strict=True,
        )
    ]
    report_rows = sorted(
        report_rows,
        key=lambda item: (-float(item["mean_abs_shap"]), str(item["feature"])),
    )
    for rank, report_row in enumerate(report_rows, start=1):
        report_row["rank"] = rank

    return (
        {
            "model_name": selected_model_name,
            "model_type": resolved_model_types.get(selected_model_name, "unknown"),
            "items": report_rows,
        },
        selected_model_name,
    )


def save_global_importance_report(
    report: dict[str, Any],
    path: str | Path,
) -> None:
    """Persist a global-importance report payload as JSON."""

    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2), encoding="utf-8")


def normalize_global_importance_payload(
    payload: Any,
    *,
    default_model_name: str | None = None,
    default_model_type: str | None = None,
) -> Any:
    """Normalize legacy global-importance payloads to the active API shape."""

    if isinstance(payload, list):
        return {
            "model_name": default_model_name or "unknown",
            "model_type": default_model_type or "unknown",
            "items": payload,
        }

    if isinstance(payload, dict) and isinstance(payload.get("items"), list):
        normalized_payload = dict(payload)
        normalized_payload.setdefault("model_name", default_model_name or "unknown")
        normalized_payload.setdefault("model_type", default_model_type or "unknown")
        return normalized_payload

    return payload


def _select_importance_source_model(
    candidate_models: dict[str, Any],
    *,
    model_stats: list[dict[str, Any]],
) -> str:
    supported_candidates = {
        model_name: model
        for model_name, model in candidate_models.items()
        if _supports_exact_linear_importance(model)
        or _supports_native_feature_importance(model)
    }
    if supported_candidates:
        return _select_best_candidate_name(
            supported_candidates,
            model_stats=model_stats,
            preferred_order=GLOBAL_IMPORTANCE_SOURCE_PREFERENCE,
        )

    raise ValueError(
        "No supplied candidate model exposes a supported global-importance interface."
    )


def _select_best_candidate_name(
    candidate_models: dict[str, Any],
    *,
    model_stats: list[dict[str, Any]],
    preferred_order: tuple[str, ...],
) -> str:
    selected_model_name = select_best_test_auc_model(
        model_stats,
        candidate_model_names=set(candidate_models),
    )
    if selected_model_name is not None and selected_model_name in candidate_models:
        return selected_model_name

    for model_name in preferred_order:
        if model_name in candidate_models:
            return model_name

    return sorted(candidate_models)[0]


def _extract_importance_values(
    model: Any,
    *,
    train_processed_features: np.ndarray,
    test_processed_features: np.ndarray,
    feature_count: int,
) -> np.ndarray:
    if _supports_exact_linear_importance(model):
        return _compute_exact_linear_importance(
            model,
            train_processed_features=train_processed_features,
            test_processed_features=test_processed_features,
            feature_count=feature_count,
        )
    if _supports_native_feature_importance(model):
        return _extract_native_feature_importance(
            model,
            feature_count=feature_count,
        )
    raise ValueError("Model does not expose a supported global-importance interface.")


def _compute_exact_linear_importance(
    model: Any,
    *,
    train_processed_features: np.ndarray,
    test_processed_features: np.ndarray,
    feature_count: int,
) -> np.ndarray:
    coefficients = np.asarray(getattr(model, "coef_"), dtype=float)
    if coefficients.ndim == 2:
        coefficients = coefficients[-1]
    if coefficients.ndim != 1:
        raise ValueError("Linear global-importance model coefficients must be one-dimensional.")
    if len(coefficients) != feature_count:
        raise ValueError(
            "Linear global-importance coefficients do not match the canonical feature count."
        )

    train_array = _as_feature_matrix(train_processed_features, feature_count=feature_count)
    test_array = _as_feature_matrix(test_processed_features, feature_count=feature_count)
    background_reference = train_array.mean(axis=0)
    local_contributions = (test_array - background_reference) * coefficients
    importance_values = np.mean(np.abs(local_contributions), axis=0)
    return _validate_importance_values(importance_values, feature_count=feature_count)


def _extract_native_feature_importance(
    model: Any,
    *,
    feature_count: int,
) -> np.ndarray:
    importance_values = np.asarray(getattr(model, "feature_importances_"), dtype=float)
    return _validate_importance_values(importance_values, feature_count=feature_count)


def _as_feature_matrix(
    values: np.ndarray,
    *,
    feature_count: int,
) -> np.ndarray:
    array = np.asarray(values, dtype=float)
    if array.ndim != 2:
        raise ValueError("Processed feature matrices must be two-dimensional.")
    if array.shape[1] != feature_count:
        raise ValueError(
            "Processed feature matrices do not match the canonical feature count."
        )
    return array


def _validate_importance_values(
    values: np.ndarray,
    *,
    feature_count: int,
) -> np.ndarray:
    importance_values = np.asarray(values, dtype=float)
    if importance_values.ndim != 1:
        raise ValueError("Global-importance values must be one-dimensional.")
    if len(importance_values) != feature_count:
        raise ValueError(
            "Global-importance values do not match the canonical feature count."
        )
    if not np.isfinite(importance_values).all():
        raise ValueError("Global-importance values must be finite.")
    if (importance_values < 0.0).any():
        raise ValueError("Global-importance values must be non-negative.")
    return importance_values


def _supports_exact_linear_importance(model: Any) -> bool:
    return hasattr(model, "coef_")


def _supports_native_feature_importance(model: Any) -> bool:
    return hasattr(model, "feature_importances_")


__all__ = [
    "DEFAULT_GLOBAL_IMPORTANCE_PATH",
    "FEATURE_CATEGORY_LOOKUP",
    "FEATURE_DISPLAY_NAMES",
    "build_global_importance_report_for_candidate_models",
    "normalize_global_importance_payload",
    "save_global_importance_report",
]
