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
    """Assemble one score request into the canonical ordered model feature row."""

    answers_payload, behavioral_payload = _extract_request_components(request)
    psychometric_features = parse_answers(answers_payload)
    raw_behavioral_features = parse_behavioral(behavioral_payload)
    behavioral_features = _neutralize_contextual_behavioral_features(raw_behavioral_features)

    answer_values = _coerce_mapping(answers_payload, component_name="answers")
    nlp_output = extract_nlp_features(str(answer_values.get("q27_resilience_text", "")))
    raw_embedding = np.asarray(nlp_output.pop("_embedding_raw"), dtype=float)

    nlp_features = {key: float(value) for key, value in nlp_output.items()}
    nlp_features.update(
        _project_text_embedding(
            raw_embedding,
            text_pca=text_pca,
            require_text_pca=require_text_pca,
        )
    )

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
            raise ValueError("request mapping must contain 'answers' and 'behavioral'.") from exc
    raise TypeError("request must be a mapping or expose answers/behavioral attributes.")


def _coerce_mapping(component: Mapping[str, Any] | Any, *, component_name: str) -> dict[str, Any]:
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
            raise ValueError("A train-fitted text_pca artifact is required for semantic features.")
        return {
            TEXT_PCA_FEATURES[0]: 0.0,
            TEXT_PCA_FEATURES[1]: 0.0,
        }

    projected_embedding = np.asarray(
        text_pca.transform(raw_embedding.reshape(1, -1))[0],
        dtype=float,
    )
    if projected_embedding.ndim != 1 or projected_embedding.shape[0] != len(TEXT_PCA_FEATURES):
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


__all__ = [
    "AssembledRequestFeatures",
    "assemble_feature_frame",
    "assemble_request_features",
]
