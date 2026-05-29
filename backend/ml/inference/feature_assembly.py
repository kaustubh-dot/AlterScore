"""Runtime feature assembly helpers for AlterScore score requests."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd

from backend.ml.features.answer_parser import parse_answers
from backend.ml.features.behavioral_parser import parse_behavioral
from backend.ml.features.derived_features import build_model_feature_row
from backend.ml.features.scenario_analyzer import compute_scenario_enriched_features
from backend.ml.nlp.extractor import extract_nlp_features
from backend.ml.preprocessing.feature_registry import ALL_MODEL_FEATURES
from backend.ml.preprocessing.pipeline import TEXT_PCA_FEATURES


@dataclass(frozen=True)
class AssembledRequestFeatures:
    psychometric_features: dict[str, float]
    raw_behavioral_features: dict[str, float | int | str]
    behavioral_features: dict[str, float | int | str]
    nlp_features: dict[str, float]
    raw_embedding: np.ndarray
    feature_row: dict[str, Any]
    feature_frame: pd.DataFrame


NEUTRAL_DEVICE_TYPE = "mobile"
NEUTRAL_TIME_OF_DAY = "afternoon"


def assemble_request_features(
    request: Mapping[str, Any] | Any,
    *,
    text_pca: Any | None = None,
    require_text_pca: bool = False,
) -> AssembledRequestFeatures:
    """Assemble one score request into the canonical ordered model feature row.

    Pipeline:
    1. parse_answers()          → base psychometric features (objective questions)
    2. compute_scenario_enriched_features() → blend scenario signals into psychometric
    3. parse_behavioral()       → behavioral telemetry features
    4. extract_nlp_features()   → NLP + text embedding features
    5. build_model_feature_row() → merge all + derived features → ordered 35-feature row
    """
    answers_payload, behavioral_payload = _extract_request_components(request)

    # Step 1: Base psychometric features from objective questions
    base_psychometric = parse_answers(answers_payload)

    # Step 2: Enrich with scenario-derived feature contributions
    # This blends scenario option values (60% existing / 40% scenario) and
    # adds scenario_consistency_score + scenario_fast_gaming to the dict.
    answers_dict = _coerce_mapping(answers_payload, component_name="answers")
    psychometric_features = compute_scenario_enriched_features(
        base_psychometric, answers_dict
    )

    # Remove scenario-specific auxiliary signals before passing to model
    # (they're used only in governance logic, not in the 35-feature ML space)
    scenario_consistency_score = psychometric_features.pop(
        "scenario_consistency_score", 0.5
    )
    scenario_fast_gaming = psychometric_features.pop("scenario_fast_gaming", 0.0)

    # Step 3: Behavioral telemetry
    raw_behavioral_features = parse_behavioral(behavioral_payload)
    behavioral_features = _neutralize_contextual_behavioral_features(
        raw_behavioral_features
    )
    # Bypassed U-shape timing transforms at inference to eliminate serving-serving skew
    # behavioral_features = _apply_timing_realism_transforms(behavioral_features)

    # Inject scenario governance signals into behavioral features for downstream use
    behavioral_features["scenario_consistency_score"] = scenario_consistency_score
    behavioral_features["scenario_fast_gaming"] = scenario_fast_gaming

    # Step 4: NLP features from open-text response
    nlp_output = extract_nlp_features(str(answers_dict.get("open_response_text", "")))
    raw_embedding = np.asarray(nlp_output.pop("_embedding_raw"), dtype=float)
    nlp_features = {key: float(value) for key, value in nlp_output.items()}
    nlp_features.update(
        _project_text_embedding(
            raw_embedding,
            text_pca=text_pca,
            require_text_pca=require_text_pca,
        )
    )

    # Step 5: Merge into canonical feature row
    feature_row = build_model_feature_row(
        psychometric_features=psychometric_features,
        behavioral_features=behavioral_features,
        nlp_features=nlp_features,
    )

    feature_frame = pd.DataFrame([feature_row], columns=ALL_MODEL_FEATURES)

    return AssembledRequestFeatures(
        psychometric_features=psychometric_features,
        raw_behavioral_features=raw_behavioral_features,
        behavioral_features=behavioral_features,
        nlp_features=nlp_features,
        raw_embedding=raw_embedding,
        feature_row=feature_row,
        feature_frame=feature_frame,
    )


def assemble_feature_frame(
    requests: Sequence[Mapping[str, Any] | Any],
    *,
    text_pca: Any | None = None,
    require_text_pca: bool = False,
) -> pd.DataFrame:
    """Assemble many score requests into one canonical model feature frame."""

    rows = [
        assemble_request_features(
            request,
            text_pca=text_pca,
            require_text_pca=require_text_pca,
        ).feature_row
        for request in requests
    ]
    return pd.DataFrame(rows, columns=ALL_MODEL_FEATURES)


def _extract_request_components(
    request: Mapping[str, Any] | Any,
) -> tuple[Any, Any]:
    if hasattr(request, "answers") and hasattr(request, "behavioral"):
        return request.answers, request.behavioral
    if hasattr(request, "model_dump"):
        request_values = request.model_dump()
        try:
            return request_values["answers"], request_values["behavioral"]
        except KeyError as exc:
            raise ValueError(
                "request model_dump() payload must contain 'answers' and 'behavioral'."
            ) from exc
    if isinstance(request, Mapping):
        try:
            return request["answers"], request["behavioral"]
        except KeyError as exc:
            raise ValueError(
                "request mapping must contain 'answers' and 'behavioral'."
            ) from exc
    raise TypeError(
        "request must be a mapping or expose answers/behavioral attributes."
    )


def _coerce_mapping(
    component: Mapping[str, Any] | Any, *, component_name: str
) -> dict[str, Any]:
    if hasattr(component, "model_dump"):
        return dict(component.model_dump())
    if isinstance(component, Mapping):
        return dict(component)
    raise TypeError(f"{component_name} must be a mapping or expose model_dump().")


def _project_text_embedding(
    raw_embedding: np.ndarray,
    *,
    text_pca: Any | None,
    require_text_pca: bool,
) -> dict[str, float]:
    if text_pca is None:
        if require_text_pca:
            raise ValueError(
                "A train-fitted text_pca artifact is required for semantic features."
            )
        return {
            TEXT_PCA_FEATURES[0]: 0.0,
            TEXT_PCA_FEATURES[1]: 0.0,
        }

    projected_embedding = np.asarray(
        text_pca.transform(raw_embedding.reshape(1, -1))[0],
        dtype=float,
    )
    if projected_embedding.ndim != 1 or projected_embedding.shape[0] != len(
        TEXT_PCA_FEATURES
    ):
        raise ValueError(
            "text_pca transform output must match the two canonical semantic dimensions."
        )
    if not np.isfinite(projected_embedding).all():
        raise ValueError("text_pca transform produced non-finite semantic features.")

    return {
        TEXT_PCA_FEATURES[0]: float(projected_embedding[0]),
        TEXT_PCA_FEATURES[1]: float(projected_embedding[1]),
    }


def _neutralize_contextual_behavioral_features(
    behavioral_features: dict[str, float | int | str],
) -> dict[str, float | int | str]:
    """Remove non-financial score variation from device and time context."""

    neutralized_features = dict(behavioral_features)
    neutralized_features["device_type"] = NEUTRAL_DEVICE_TYPE
    neutralized_features["time_of_day"] = NEUTRAL_TIME_OF_DAY
    return neutralized_features


def _apply_timing_realism_transforms(
    behavioral_features: dict[str, float | int | str],
) -> dict[str, float | int | str]:
    """Apply safe non-monotonic transformations to detect extreme fast/slow pacing and copy-pasting."""

    transformed = dict(behavioral_features)

    # 1. avg_response_time_ms (U-Shaped pacing curve)
    # Healthy thoughtful window is 4000ms - 15000ms.
    # If < 4000ms, apply a smooth quadratic penalty by inflating the response time.
    raw_time = float(transformed.get("avg_response_time_ms", 5200.0))
    if raw_time < 4000.0:
        transformed["avg_response_time_ms"] = raw_time + ((4000.0 - raw_time) ** 2) / 100.0

    # 2. session_duration_sec (U-Shaped session pacing curve)
    # Healthy thoughtful session is at least 120 seconds.
    # If < 120s, inflate the session duration to apply the negative monotonic constraint.
    raw_duration = float(transformed.get("session_duration_sec", 180.0))
    if raw_duration < 120.0:
        transformed["session_duration_sec"] = raw_duration + ((120.0 - raw_duration) ** 2) / 2.0

    # 3. typing_speed_wpm (U-Shaped physical typing limit check)
    # Human typing limit is around 85 WPM. If higher (e.g. copy-pasting / bot typing),
    # reverse the value to scale WPM down, penalizing the positive WPM constraint.
    raw_wpm = float(transformed.get("typing_speed_wpm", 0.0))
    if raw_wpm > 85.0:
        transformed["typing_speed_wpm"] = max(0.0, 85.0 - (raw_wpm - 85.0) * 2.0)

    return transformed


__all__ = [
    "AssembledRequestFeatures",
    "assemble_feature_frame",
    "assemble_request_features",
]
