"""Ensemble inference adapter for AlterScore runtime scoring.

Transforms raw preprocessed features into base model probabilities,
stacks them into meta-features, and runs the stacking meta-learner.
Handles prediction differences across scikit-learn, TabNet, and PyTorch base models.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

try:
    import torch
except ImportError:
    torch = None


@dataclass(frozen=True)
class EnsembleInferenceBundle:
    """Holds the fully loaded ensemble state required for inference."""

    stacking_model: Any
    base_models: dict[str, Any]
    base_model_order: tuple[str, ...]
    preprocessor: Any
    stacking_config: dict[str, Any]


@dataclass(frozen=True)
class TabNetMitigationConfig:
    """Runtime robustness guard for pathological TabNet disagreements.

    The defaults are intentionally conservative:
    - peer confidence must already be high (`>= 0.80`)
    - disagreement must exceed `0.25`, which is well above the observed
      99.5th-percentile validation disagreement (~0.12) and far below the
      confirmed pathological collapses (~0.77 to ~0.91)
    - the mitigation softly blends TabNet toward the peer mean rather than
      disabling it entirely
    """

    enabled: bool = True
    min_peer_confidence: float = 0.80
    disagreement_threshold: float = 0.25
    max_blend_weight: float = 0.75


@dataclass(frozen=True)
class EnsembleMetaFeatures:
    """Intermediate ensemble inputs and runtime mitigation diagnostics."""

    raw_base_probabilities: dict[str, np.ndarray]
    raw_meta_features_matrix: np.ndarray
    adjusted_meta_features_matrix: np.ndarray
    mitigation_debug: dict[str, Any]


class WrappedEnsembleModel:
    """Wraps the ensemble inference bundle to expose a standard predict_proba API.

    This enables the DICE explainer (which expects a model with a .predict_proba
    method that accepts the 35 preprocessed features) to operate transparently
    on the ensemble without knowing its internal architecture.
    """

    def __init__(self, bundle: EnsembleInferenceBundle) -> None:
        self.bundle = bundle

    def predict_proba(self, processed_features: np.ndarray) -> np.ndarray:
        return predict_ensemble_proba(self.bundle, processed_features)


def build_ensemble_meta_features(
    bundle: EnsembleInferenceBundle,
    processed_features: np.ndarray,
) -> EnsembleMetaFeatures:
    """Generate raw/adjusted meta-features and mitigation diagnostics."""

    if not bundle.base_model_order:
        raise ValueError("Ensemble inference bundle has an empty base_model_order.")

    missing_models = [m for m in bundle.base_model_order if m not in bundle.base_models]
    if missing_models:
        raise ValueError(
            f"Ensemble inference bundle is missing required base models: {missing_models}"
        )

    raw_base_probabilities: dict[str, np.ndarray] = {}
    meta_features_list = []
    for model_name in bundle.base_model_order:
        base_model = bundle.base_models[model_name]
        positive_class_probability = _extract_positive_class_probability(
            predict_base_model_proba(base_model, processed_features),
            model_name=model_name,
        )
        raw_base_probabilities[model_name] = positive_class_probability
        meta_features_list.append(positive_class_probability)

    raw_meta_features_matrix = np.column_stack(meta_features_list)
    adjusted_meta_features_matrix, mitigation_debug = _apply_tabnet_disagreement_mitigation(
        raw_meta_features_matrix,
        base_model_order=bundle.base_model_order,
        stacking_config=bundle.stacking_config,
    )
    return EnsembleMetaFeatures(
        raw_base_probabilities=raw_base_probabilities,
        raw_meta_features_matrix=raw_meta_features_matrix,
        adjusted_meta_features_matrix=adjusted_meta_features_matrix,
        mitigation_debug=mitigation_debug,
    )


def predict_ensemble_proba(
    bundle: EnsembleInferenceBundle,
    processed_features: np.ndarray,
) -> np.ndarray:
    """Transform preprocessed features -> base probabilities -> calibrated prediction.

    Args:
        bundle: The loaded ensemble artifacts and config.
        processed_features: The (n, 35) preprocessed input row/matrix.

    Returns:
        The (n, 2) probability matrix from the stacking meta-learner.
    """
    meta_features = build_ensemble_meta_features(bundle, processed_features)
    return np.asarray(
        bundle.stacking_model.predict_proba(meta_features.adjusted_meta_features_matrix),
        dtype=float,
    )


def _apply_tabnet_disagreement_mitigation(
    raw_meta_features_matrix: np.ndarray,
    *,
    base_model_order: tuple[str, ...],
    stacking_config: dict[str, Any],
) -> tuple[np.ndarray, dict[str, Any]]:
    config = _resolve_tabnet_mitigation_config(stacking_config)
    adjusted_meta_features_matrix = np.asarray(raw_meta_features_matrix, dtype=float).copy()

    if "tabnet" not in base_model_order:
        return adjusted_meta_features_matrix, {
            "enabled": False,
            "reason": "tabnet_not_present",
        }

    tabnet_index = base_model_order.index("tabnet")
    peer_indices = [index for index, name in enumerate(base_model_order) if name != "tabnet"]
    peer_meta_features = adjusted_meta_features_matrix[:, peer_indices]
    peer_mean_probability = np.mean(peer_meta_features, axis=1)
    raw_tabnet_probability = adjusted_meta_features_matrix[:, tabnet_index].copy()
    disagreement_magnitude = peer_mean_probability - raw_tabnet_probability
    peer_confidence = peer_mean_probability

    trigger_mask = (
        config.enabled
        & (peer_confidence >= config.min_peer_confidence)
        & (disagreement_magnitude >= config.disagreement_threshold)
    )
    normalized_disagreement = np.clip(
        (disagreement_magnitude - config.disagreement_threshold)
        / max(1.0 - config.disagreement_threshold, 1e-9),
        0.0,
        1.0,
    )
    blend_weight = config.max_blend_weight * np.square(normalized_disagreement)
    adjusted_tabnet_probability = raw_tabnet_probability + (
        (peer_mean_probability - raw_tabnet_probability) * blend_weight
    )
    adjusted_tabnet_probability = np.where(
        trigger_mask,
        adjusted_tabnet_probability,
        raw_tabnet_probability,
    )
    adjusted_meta_features_matrix[:, tabnet_index] = adjusted_tabnet_probability

    return adjusted_meta_features_matrix, {
        "enabled": config.enabled,
        "tabnet_index": tabnet_index,
        "peer_model_names": [base_model_order[index] for index in peer_indices],
        "config": {
            "min_peer_confidence": config.min_peer_confidence,
            "disagreement_threshold": config.disagreement_threshold,
            "max_blend_weight": config.max_blend_weight,
        },
        "raw_tabnet_probability": raw_tabnet_probability,
        "peer_mean_probability": peer_mean_probability,
        "disagreement_magnitude": disagreement_magnitude,
        "peer_confidence": peer_confidence,
        "trigger_mask": trigger_mask.astype(bool, copy=False),
        "blend_weight": blend_weight,
        "adjusted_tabnet_probability": adjusted_tabnet_probability,
    }


def _resolve_tabnet_mitigation_config(stacking_config: dict[str, Any]) -> TabNetMitigationConfig:
    mitigation_payload = stacking_config.get("tabnet_mitigation")
    if not isinstance(mitigation_payload, dict):
        return TabNetMitigationConfig()

    return TabNetMitigationConfig(
        enabled=bool(mitigation_payload.get("enabled", True)),
        min_peer_confidence=float(mitigation_payload.get("min_peer_confidence", 0.80)),
        disagreement_threshold=float(mitigation_payload.get("disagreement_threshold", 0.25)),
        max_blend_weight=float(mitigation_payload.get("max_blend_weight", 0.75)),
    )


def _extract_positive_class_probability(
    probabilities: np.ndarray,
    *,
    model_name: str,
) -> np.ndarray:
    if probabilities.ndim == 2 and probabilities.shape[1] >= 2:
        return probabilities[:, 1]
    if probabilities.ndim == 1:
        return probabilities
    raise ValueError(f"Unexpected probability shape {probabilities.shape} from {model_name}.")


def predict_base_model_proba(model: Any, processed_features: np.ndarray) -> np.ndarray:
    """Handle predict_proba for sklearn, TabNet, and PyTorch MLP base models."""

    # Sklearn / XGBoost / LightGBM / TabNet path
    if hasattr(model, "predict_proba"):
        return np.asarray(model.predict_proba(processed_features), dtype=float)

    # PyTorch MLP path
    if torch is not None and isinstance(model, torch.nn.Module):
        model.eval()
        try:
            device = next(model.parameters()).device
        except StopIteration:
            device = torch.device("cpu")
        tensor_features = torch.tensor(processed_features, dtype=torch.float32).to(device)
        with torch.no_grad():
            output = model(tensor_features)
            return output.cpu().numpy().astype(float)

    raise TypeError(
        f"Base model of type {type(model).__name__} does not expose predict_proba() "
        "and is not a PyTorch Module."
    )

__all__ = [
    "EnsembleInferenceBundle",
    "EnsembleMetaFeatures",
    "TabNetMitigationConfig",
    "WrappedEnsembleModel",
    "build_ensemble_meta_features",
    "predict_base_model_proba",
    "predict_ensemble_proba",
]
