"""Persisted counterfactual explainer helpers for AlterScore."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Final, Mapping, Sequence

import joblib
import numpy as np

from backend.app.core.paths import MODEL_EXPLAINERS_DIR
from backend.ml.explainability.global_importance import FEATURE_DISPLAY_NAMES
from backend.ml.features.derived_features import compute_derived_features
from backend.ml.inference.score_mapper import probability_to_score
from backend.ml.preprocessing.feature_registry import (
    ACTIONABLE_FEATURES,
    ALL_MODEL_FEATURES,
    IMMUTABLE_FEATURES,
)
from backend.ml.preprocessing.pipeline import transform_features

DEFAULT_DICE_EXPLAINER_PATH: Final[Path] = MODEL_EXPLAINERS_DIR / "dice_explainer.pkl"
ProbabilityAdjuster = Callable[[float, Mapping[str, Any]], float]
ScoreMapper = Callable[[float], int]
DEFAULT_COUNTERFACTUAL_POLICIES: Final[dict[str, dict[str, Any]]] = {
    "numeracy_score": {
        "direction": "increase",
        "target": 1.0,
        "plain_language": "Improving financial-math accuracy could lift the score.",
    },
    "financial_literacy_score": {
        "direction": "increase",
        "target": 1.0,
        "plain_language": "Getting more money-basics questions right could lift the score.",
    },
    "future_orientation": {
        "direction": "increase",
        "target": 0.85,
        "plain_language": "Showing stronger long-term planning could lift the score.",
    },
    "conscientiousness_score": {
        "direction": "increase",
        "target": 0.85,
        "plain_language": "More consistent follow-through and planning could lift the score.",
    },
    "social_capital_score": {
        "direction": "increase",
        "target": 0.8,
        "plain_language": "Demonstrating stronger support systems could lift the score.",
    },
    "answer_change_rate": {
        "direction": "decrease",
        "target": 0.03,
        "plain_language": "Changing answers less often after the first response could lift the score.",
    },
    "text_agency_score": {
        "direction": "increase",
        "target": 0.8,
        "plain_language": "Using more action-oriented language in the resilience response could lift the score.",
    },
}


@dataclass(frozen=True)
class PersistedDiceExplainer:
    """Minimal persisted counterfactual explainer for the runtime bundle."""

    model_name: str = ""
    algorithm: str = "bounded_actionable_counterfactuals"
    feature_names: tuple[str, ...] = ()
    actionable_features: tuple[str, ...] = ()
    immutable_features: tuple[str, ...] = ()
    feature_policies: dict[str, dict[str, Any]] = field(default_factory=dict)
    max_actions: int = 3
    min_score_gain: int = 1
    min_probability_gain: float = 0.0025

    def validate(
        self,
        *,
        expected_feature_names: Sequence[str] | None = None,
        allowed_actionable_features: Sequence[str] | None = None,
        expected_immutable_features: Sequence[str] | None = None,
    ) -> None:
        if not isinstance(self.model_name, str) or not self.model_name:
            raise ValueError(
                "Persisted DICE explainer must define a non-empty model_name."
            )
        if not isinstance(self.algorithm, str) or not self.algorithm:
            raise ValueError(
                "Persisted DICE explainer must define a non-empty algorithm."
            )

        resolved_feature_names = tuple(self.feature_names)
        if not resolved_feature_names:
            raise ValueError("Persisted DICE explainer must contain feature names.")
        if (
            expected_feature_names is not None
            and tuple(expected_feature_names) != resolved_feature_names
        ):
            raise ValueError(
                "Persisted DICE explainer feature names do not match the canonical feature order."
            )

        actionable_features = tuple(self.actionable_features)
        if not actionable_features:
            raise ValueError(
                "Persisted DICE explainer must declare actionable features."
            )
        if allowed_actionable_features is not None:
            # Tolerate avg_response_time_ms since it was neutralized and removed from canonical ACTIONABLE_FEATURES
            tolerated_actionables = set(allowed_actionable_features) | {
                "avg_response_time_ms"
            }
            unsupported_actionables = sorted(
                set(actionable_features) - tolerated_actionables
            )
            if unsupported_actionables:
                raise ValueError(
                    "Persisted DICE explainer references unsupported actionable features: "
                    f"{unsupported_actionables}"
                )

        immutable_features = tuple(self.immutable_features)
        if expected_immutable_features is not None and set(immutable_features) != set(
            expected_immutable_features
        ):
            raise ValueError(
                "Persisted DICE explainer immutable features do not match the canonical set."
            )

        if sorted(set(actionable_features) & set(immutable_features)):
            raise ValueError(
                "Persisted DICE explainer actionable and immutable features must be disjoint."
            )

        feature_name_set = set(resolved_feature_names)
        if set(actionable_features) - feature_name_set:
            raise ValueError(
                "Persisted DICE explainer actionable features must exist in feature_names."
            )
        if int(self.max_actions) < 1:
            raise ValueError("Persisted DICE explainer max_actions must be at least 1.")
        if int(self.min_score_gain) < 0:
            raise ValueError(
                "Persisted DICE explainer min_score_gain must be non-negative."
            )
        if (
            not np.isfinite(float(self.min_probability_gain))
            or float(self.min_probability_gain) < 0.0
        ):
            raise ValueError(
                "Persisted DICE explainer min_probability_gain must be finite and non-negative."
            )

        if not isinstance(self.feature_policies, dict) or not self.feature_policies:
            raise ValueError("Persisted DICE explainer must define feature policies.")

        for feature_name, policy in self.feature_policies.items():
            if feature_name not in actionable_features:
                raise ValueError(
                    f"Persisted DICE explainer policy feature {feature_name!r} is not actionable."
                )
            if not isinstance(policy, dict):
                raise ValueError(
                    f"Persisted DICE explainer policy for {feature_name!r} must be a mapping."
                )
            direction = policy.get("direction")
            if direction not in {"increase", "decrease"}:
                raise ValueError(
                    f"Persisted DICE explainer policy for {feature_name!r} must use "
                    "'increase' or 'decrease'."
                )
            try:
                target = float(policy.get("target"))
            except (TypeError, ValueError) as exc:
                raise ValueError(
                    f"Persisted DICE explainer policy for {feature_name!r} must define a numeric target."
                ) from exc
            if not np.isfinite(target):
                raise ValueError(
                    f"Persisted DICE explainer policy for {feature_name!r} must define a finite target."
                )
            plain_language = policy.get("plain_language")
            if not isinstance(plain_language, str) or not plain_language:
                raise ValueError(
                    f"Persisted DICE explainer policy for {feature_name!r} must define plain_language."
                )

    def generate_actions(
        self,
        *,
        feature_row: Mapping[str, Any],
        feature_frame: Any,
        model: Any,
        preprocessor: Any,
        current_probability: float,
        current_credit_score: int,
        shap_contributions: Mapping[str, float] | None = None,
        candidate_probability_adjuster: ProbabilityAdjuster | None = None,
        candidate_score_mapper: ScoreMapper | None = None,
    ) -> list[dict[str, Any]]:
        self.validate(
            expected_feature_names=ALL_MODEL_FEATURES,
            allowed_actionable_features=ACTIONABLE_FEATURES,
            expected_immutable_features=IMMUTABLE_FEATURES,
        )

        candidate_actions: list[tuple[int, float, dict[str, Any]]] = []
        for feature_name in self._rank_actionable_features(shap_contributions or {}):
            policy = self.feature_policies.get(feature_name)
            if policy is None:
                continue

            current_value = _coerce_numeric_feature_value(feature_row.get(feature_name))
            if current_value is None:
                continue

            suggested_value = _resolve_counterfactual_target(current_value, policy)
            if suggested_value is None:
                continue

            candidate_frame = feature_frame.copy(deep=True)
            row_index = candidate_frame.index[0]
            candidate_frame.loc[row_index, feature_name] = suggested_value

            candidate_row = dict(feature_row)
            candidate_row[feature_name] = suggested_value
            derived_features = compute_derived_features(candidate_row)
            candidate_row.update(derived_features)
            for derived_feature_name, derived_value in derived_features.items():
                candidate_frame.loc[row_index, derived_feature_name] = derived_value

            candidate_processed = transform_features(preprocessor, candidate_frame)
            candidate_probability = _predict_repayment_probability(
                model, candidate_processed
            )
            adjusted_candidate_probability = (
                candidate_probability_adjuster(candidate_probability, candidate_row)
                if candidate_probability_adjuster is not None
                else candidate_probability
            )
            candidate_credit_score = (
                candidate_score_mapper(adjusted_candidate_probability)
                if candidate_score_mapper is not None
                else probability_to_score(adjusted_candidate_probability)
            )
            estimated_score_gain = candidate_credit_score - current_credit_score
            probability_gain = adjusted_candidate_probability - current_probability
            if estimated_score_gain < self.min_score_gain and probability_gain < float(
                self.min_probability_gain
            ):
                continue

            candidate_actions.append(
                (
                    int(estimated_score_gain),
                    float(probability_gain),
                    {
                        "feature": feature_name,
                        "current_value": round(current_value, 4),
                        "suggested_value": round(float(suggested_value), 4),
                        "estimated_score_gain": int(estimated_score_gain),
                        "plain_language": _build_counterfactual_plain_language(
                            feature_name=feature_name,
                            estimated_score_gain=int(estimated_score_gain),
                            baseline_message=str(policy["plain_language"]),
                        ),
                    },
                )
            )

        candidate_actions.sort(
            key=lambda item: (-item[0], -item[1], item[2]["feature"])
        )
        return [item[2] for item in candidate_actions[: int(self.max_actions)]]

    def _rank_actionable_features(
        self,
        shap_contributions: Mapping[str, float],
    ) -> list[str]:
        negative_actionable = [
            feature_name
            for feature_name, _ in sorted(
                (
                    (feature_name, shap_value)
                    for feature_name, shap_value in shap_contributions.items()
                    if feature_name in self.actionable_features and shap_value < 0.0
                ),
                key=lambda item: (item[1], item[0]),
            )
        ]
        remaining_actionable = [
            feature_name
            for feature_name in self.actionable_features
            if feature_name not in negative_actionable
            and feature_name in self.feature_policies
        ]
        return negative_actionable + remaining_actionable


def build_default_persisted_dice_explainer(
    *,
    model_name: str = "logistic_regression",
) -> PersistedDiceExplainer:
    explainer = PersistedDiceExplainer(
        model_name=model_name,
        feature_names=tuple(ALL_MODEL_FEATURES),
        actionable_features=tuple(DEFAULT_COUNTERFACTUAL_POLICIES),
        immutable_features=tuple(IMMUTABLE_FEATURES),
        feature_policies={
            key: dict(value) for key, value in DEFAULT_COUNTERFACTUAL_POLICIES.items()
        },
    )
    explainer.validate(
        expected_feature_names=ALL_MODEL_FEATURES,
        allowed_actionable_features=ACTIONABLE_FEATURES,
        expected_immutable_features=IMMUTABLE_FEATURES,
    )
    return explainer


def save_persisted_dice_explainer(
    explainer: PersistedDiceExplainer,
    path: str | Path,
) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(explainer, output_path)


def load_persisted_dice_explainer(
    path: str | Path,
    *,
    expected_feature_names: Sequence[str] | None = None,
    allowed_actionable_features: Sequence[str] | None = None,
    expected_immutable_features: Sequence[str] | None = None,
) -> PersistedDiceExplainer:
    explainer = joblib.load(Path(path))
    if not isinstance(explainer, PersistedDiceExplainer):
        raise TypeError(
            "Persisted DICE explainer artifact did not deserialize to PersistedDiceExplainer."
        )
    explainer.validate(
        expected_feature_names=expected_feature_names,
        allowed_actionable_features=allowed_actionable_features,
        expected_immutable_features=expected_immutable_features,
    )
    return explainer


def _resolve_counterfactual_target(
    current_value: float,
    policy: Mapping[str, Any],
) -> float | None:
    direction = str(policy["direction"])
    target = float(policy["target"])
    if direction == "increase":
        if current_value >= target:
            return None
        return target
    if direction == "decrease":
        if current_value <= target:
            return None
        return target
    raise ValueError(f"Unsupported counterfactual direction: {direction}")


def _predict_repayment_probability(model: Any, processed_features: np.ndarray) -> float:
    probabilities = np.asarray(model.predict_proba(processed_features), dtype=float)
    if probabilities.ndim != 2 or probabilities.shape[1] < 2:
        raise ValueError(
            "Runtime model predict_proba output must have at least two columns."
        )

    repayment_probability = float(np.clip(probabilities[0, 1], 0.0, 1.0))
    if np.isnan(repayment_probability):
        raise ValueError("Runtime model produced a NaN repayment probability.")
    return repayment_probability


def _coerce_numeric_feature_value(value: Any) -> float | None:
    try:
        numeric_value = float(value)
    except (TypeError, ValueError):
        return None

    if not np.isfinite(numeric_value):
        return None
    return numeric_value


def _build_counterfactual_plain_language(
    *,
    feature_name: str,
    estimated_score_gain: int,
    baseline_message: str,
) -> str:
    if estimated_score_gain > 0:
        return baseline_message

    display_name = FEATURE_DISPLAY_NAMES.get(
        feature_name,
        feature_name.replace("_", " ").title(),
    )
    return (
        f"{display_name} could strengthen already-strong repayment signals "
        "even if the score is already near the current ceiling."
    )


__all__ = [
    "DEFAULT_COUNTERFACTUAL_POLICIES",
    "DEFAULT_DICE_EXPLAINER_PATH",
    "PersistedDiceExplainer",
    "build_default_persisted_dice_explainer",
    "load_persisted_dice_explainer",
    "save_persisted_dice_explainer",
]
