"""Runtime feature assembly for the answer-only synthetic-demo model."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

import pandas as pd

from backend.ml.features.answer_parser import parse_answers
from backend.ml.features.behavioral_parser import parse_behavioral
from backend.ml.features.derived_features import build_model_feature_row
from backend.ml.features.scenario_analyzer import compute_scenario_enriched_features
from backend.ml.inference.text_quality import (
    TextQualityAssessment,
    assess_text_response_quality,
)
from backend.ml.preprocessing.feature_registry import ALL_MODEL_FEATURES


@dataclass(frozen=True)
class AssembledRequestFeatures:
    """Score-relevant features plus score-inert diagnostics for one request."""

    psychometric_features: dict[str, float]
    raw_behavioral_features: dict[str, float | int | str]
    behavioral_features: dict[str, float | int | str]
    text_quality: TextQualityAssessment
    feature_row: dict[str, Any]
    feature_frame: pd.DataFrame


def assemble_request_features(
    request: Mapping[str, Any] | Any,
    *,
    text_pca: Any | None = None,
    require_text_pca: bool = False,
) -> AssembledRequestFeatures:
    """Build canonical answer-derived model features for a score request.

    Browser telemetry remains available in ``raw_behavioral_features`` for
    diagnostics but is never merged into model features or score adjustments.
    The legacy PCA parameters are intentionally ignored for source
    compatibility: opaque text embeddings are not part of this scorer.
    """

    del text_pca, require_text_pca
    answers_payload, behavioral_payload = _extract_request_components(request)
    answers_dict = _coerce_mapping(answers_payload, component_name="answers")

    base_psychometric = parse_answers(answers_payload)
    enriched = compute_scenario_enriched_features(base_psychometric, answers_dict)
    psychometric_features = {
        feature_name: float(value)
        for feature_name, value in enriched.items()
        if not feature_name.startswith("scenario_")
    }

    raw_behavioral_features = parse_behavioral(behavioral_payload)
    # Keep diagnostic telemetry verbatim after schema validation. It has no
    # pathway into ``feature_row`` or the final score.
    behavioral_features = dict(raw_behavioral_features)
    text_quality = assess_text_response_quality(
        str(answers_dict.get("open_response_text", ""))
    )

    feature_row = build_model_feature_row(
        psychometric_features=psychometric_features,
        behavioral_features={},
        nlp_features={},
    )
    feature_frame = pd.DataFrame([feature_row], columns=ALL_MODEL_FEATURES)

    return AssembledRequestFeatures(
        psychometric_features=psychometric_features,
        raw_behavioral_features=raw_behavioral_features,
        behavioral_features=behavioral_features,
        text_quality=text_quality,
        feature_row=feature_row,
        feature_frame=feature_frame,
    )


def assemble_feature_frame(
    requests: Sequence[Mapping[str, Any] | Any],
    *,
    text_pca: Any | None = None,
    require_text_pca: bool = False,
) -> pd.DataFrame:
    """Assemble many requests into the canonical model feature frame."""

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


__all__ = [
    "AssembledRequestFeatures",
    "assemble_feature_frame",
    "assemble_request_features",
]
