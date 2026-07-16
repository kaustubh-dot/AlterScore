"""Persisted SHAP explainer compatibility helpers for AlterScore."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Sequence

import joblib
import numpy as np


@dataclass
class PersistedShapExplainer:
    """Minimal persisted SHAP payload used by the current runtime bundle.

    The checked-in explainer artifact stores a lightweight exact-linear SHAP
    surrogate for the current logistic-regression runtime bundle rather than a
    direct dependency on the full `shap` package. Recreating this class restores
    deserialization compatibility for the saved artifact and provides a small
    validation surface for health/readiness checks.
    """

    model_name: str = ""
    algorithm: str = "exact_linear_shap"
    feature_names: tuple[str, ...] = ()
    background_mean: np.ndarray = field(
        default_factory=lambda: np.asarray([], dtype=float)
    )
    background_size: int = 0
    coefficients: np.ndarray = field(
        default_factory=lambda: np.asarray([], dtype=float)
    )
    shap_explainer: Any | None = None

    def validate(
        self,
        *,
        expected_feature_names: Sequence[str] | None = None,
    ) -> None:
        """Raise ``ValueError`` if the persisted payload is not runtime-usable."""

        if not isinstance(self.model_name, str) or not self.model_name:
            raise ValueError(
                "Persisted SHAP explainer must define a non-empty model_name."
            )
        if not isinstance(self.algorithm, str) or not self.algorithm:
            raise ValueError(
                "Persisted SHAP explainer must define a non-empty algorithm."
            )

        resolved_feature_names = tuple(self.feature_names)
        if not resolved_feature_names:
            raise ValueError("Persisted SHAP explainer must contain feature names.")
        if any(
            not isinstance(feature_name, str) or not feature_name
            for feature_name in resolved_feature_names
        ):
            raise ValueError(
                "Persisted SHAP explainer feature names must be non-empty strings."
            )

        if (
            expected_feature_names is not None
            and tuple(expected_feature_names) != resolved_feature_names
        ):
            raise ValueError(
                "Persisted SHAP explainer feature names do not match the canonical feature order."
            )

        background_mean = np.asarray(self.background_mean, dtype=float)
        coefficients = np.asarray(self.coefficients, dtype=float)
        feature_count = len(resolved_feature_names)

        if background_mean.ndim != 1 or len(background_mean) != feature_count:
            raise ValueError(
                "Persisted SHAP explainer background_mean must be a one-dimensional vector "
                "matching the feature count."
            )
        if coefficients.ndim != 1 or len(coefficients) != feature_count:
            raise ValueError(
                "Persisted SHAP explainer coefficients must be a one-dimensional vector "
                "matching the feature count."
            )
        if not np.isfinite(background_mean).all():
            raise ValueError("Persisted SHAP explainer background_mean must be finite.")
        if not np.isfinite(coefficients).all():
            raise ValueError("Persisted SHAP explainer coefficients must be finite.")
        if int(self.background_size) < 1:
            raise ValueError(
                "Persisted SHAP explainer background_size must be at least 1."
            )

        if self.algorithm == "exact_linear_shap":
            return

        if self.shap_explainer is None:
            raise ValueError(
                "Unsupported persisted SHAP algorithm without a backing explainer object."
            )

    def explain_processed_row(
        self, processed_row: Sequence[float] | np.ndarray
    ) -> np.ndarray:
        """Return per-feature SHAP-like contributions for one processed row."""

        self.validate()
        processed = np.asarray(processed_row, dtype=float)
        if processed.ndim != 1:
            raise ValueError(
                "Processed SHAP explanation input must be one-dimensional."
            )
        if len(processed) != len(self.feature_names):
            raise ValueError(
                "Processed SHAP explanation input does not match the persisted feature count."
            )
        if not np.isfinite(processed).all():
            raise ValueError("Processed SHAP explanation input must be finite.")

        return (processed - np.asarray(self.background_mean, dtype=float)) * np.asarray(
            self.coefficients,
            dtype=float,
        )

    def explain_processed_matrix(
        self,
        processed_features: Sequence[Sequence[float]] | np.ndarray,
    ) -> np.ndarray:
        """Return per-feature contributions for a batch of processed rows."""

        self.validate()
        processed = np.asarray(processed_features, dtype=float)
        if processed.ndim != 2:
            raise ValueError(
                "Processed SHAP explanation input must be two-dimensional."
            )
        if processed.shape[1] != len(self.feature_names):
            raise ValueError(
                "Processed SHAP explanation matrix does not match the persisted feature count."
            )
        if not np.isfinite(processed).all():
            raise ValueError("Processed SHAP explanation matrix must be finite.")

        return (processed - np.asarray(self.background_mean, dtype=float)) * np.asarray(
            self.coefficients, dtype=float
        )


def load_persisted_shap_explainer(
    path: str | Path,
    *,
    expected_feature_names: Sequence[str] | None = None,
) -> PersistedShapExplainer:
    """Load and validate the persisted SHAP explainer artifact."""

    explainer = joblib.load(Path(path))
    if not isinstance(explainer, PersistedShapExplainer):
        raise TypeError(
            "Persisted SHAP explainer artifact did not deserialize to PersistedShapExplainer."
        )
    explainer.validate(expected_feature_names=expected_feature_names)
    return explainer


__all__ = [
    "PersistedShapExplainer",
    "load_persisted_shap_explainer",
]
