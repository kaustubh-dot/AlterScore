"""Ensemble inference adapter for AlterScore runtime scoring.

Transforms raw preprocessed features into base model probabilities,
stacks them into meta-features, and runs the stacking meta-learner.
Handles prediction differences across scikit-learn, TabNet, and PyTorch base models.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np


@dataclass(frozen=True)
class EnsembleInferenceBundle:
    """Holds the fully loaded ensemble state required for inference."""

    stacking_model: Any
    base_models: dict[str, Any]
    base_model_order: tuple[str, ...]
    preprocessor: Any
    stacking_config: dict[str, Any]


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
    if not bundle.base_model_order:
        raise ValueError("Ensemble inference bundle has an empty base_model_order.")

    # Validate that all required base models are loaded
    missing_models = [m for m in bundle.base_model_order if m not in bundle.base_models]
    if missing_models:
        raise ValueError(
            f"Ensemble inference bundle is missing required base models: {missing_models}"
        )

    # 1. Generate base model probability arrays
    meta_features_list = []
    for model_name in bundle.base_model_order:
        base_model = bundle.base_models[model_name]
        probas = _predict_base_model_proba(base_model, processed_features)
        
        # We only want the positive class probability (index 1) to form the meta-feature,
        # mirroring `_build_stacking_inputs` in `train_stacking.py` where it collects
        # probas[:, 1] for the meta matrix.
        if probas.ndim == 2 and probas.shape[1] >= 2:
            positive_class_proba = probas[:, 1]
        elif probas.ndim == 1:
            positive_class_proba = probas
        else:
            raise ValueError(f"Unexpected probability shape {probas.shape} from {model_name}.")

        meta_features_list.append(positive_class_proba)

    # 2. Stack into an (n, 6) meta-feature matrix
    meta_features_matrix = np.column_stack(meta_features_list)

    # 3. Predict via the calibrated stacking model
    return np.asarray(bundle.stacking_model.predict_proba(meta_features_matrix), dtype=float)


def _predict_base_model_proba(model: Any, processed_features: np.ndarray) -> np.ndarray:
    """Handle predict_proba for sklearn, TabNet, and PyTorch MLP base models."""

    # Sklearn / XGBoost / LightGBM / TabNet path
    if hasattr(model, "predict_proba"):
        return np.asarray(model.predict_proba(processed_features), dtype=float)

    # PyTorch MLP path
    import torch
    
    if isinstance(model, torch.nn.Module):
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
    "WrappedEnsembleModel",
    "predict_ensemble_proba",
]
