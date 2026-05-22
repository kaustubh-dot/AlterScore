import numpy as np
import pytest
import torch
import torch.nn as nn

from backend.ml.inference.ensemble_adapter import (
    EnsembleInferenceBundle,
    WrappedEnsembleModel,
    build_ensemble_meta_features,
    predict_ensemble_proba,
    _predict_base_model_proba,
)

class MockSklearnModel:
    def predict_proba(self, X):
        X = np.asarray(X)
        n = X.shape[0]
        # Return deterministic mock probabilities: [0.3, 0.7]
        return np.tile([0.3, 0.7], (n, 1))

class MockTorchModel(nn.Module):
    def forward(self, x):
        n = x.shape[0]
        # Return deterministic mock probabilities: [0.4, 0.6]
        return torch.tensor([[0.4, 0.6]] * n, dtype=torch.float32)

class MockStackingModel:
    def predict_proba(self, meta_X):
        # meta_X should be shape (n, 2) in this test
        self.last_meta_X = meta_X
        n = meta_X.shape[0]
        # Return deterministic mock predictions based on the sum of meta features
        sums = np.sum(meta_X, axis=1)
        prob_1 = np.clip(sums / 2.0, 0.0, 1.0) # normalize roughly
        prob_0 = 1.0 - prob_1
        return np.column_stack((prob_0, prob_1))


class ConstantProbabilityModel:
    def __init__(self, positive_probability: float) -> None:
        self.positive_probability = positive_probability

    def predict_proba(self, X):
        X = np.asarray(X)
        n = X.shape[0]
        positive = np.full(n, self.positive_probability, dtype=float)
        negative = 1.0 - positive
        return np.column_stack((negative, positive))

def test_predict_base_model_proba_sklearn():
    model = MockSklearnModel()
    X = np.random.rand(5, 35)
    probas = _predict_base_model_proba(model, X)
    assert probas.shape == (5, 2)
    assert np.allclose(probas[:, 1], 0.7)

def test_predict_base_model_proba_torch():
    model = MockTorchModel()
    X = np.random.rand(3, 35)
    probas = _predict_base_model_proba(model, X)
    assert probas.shape == (3, 2)
    assert np.allclose(probas[:, 1], 0.6)

def test_predict_ensemble_proba_valid_bundle():
    stacking_model = MockStackingModel()
    base_models = {
        "model_a": MockSklearnModel(),
        "model_b": MockTorchModel(),
    }
    
    bundle = EnsembleInferenceBundle(
        stacking_model=stacking_model,
        base_models=base_models,
        base_model_order=("model_a", "model_b"),
        preprocessor=None,
        stacking_config={}
    )
    
    X = np.random.rand(4, 35)
    result = predict_ensemble_proba(bundle, X)
    
    assert result.shape == (4, 2)
    
    # Check meta_features shape and content
    meta_X = stacking_model.last_meta_X
    assert meta_X.shape == (4, 2)
    assert np.allclose(meta_X[:, 0], 0.7)  # from model_a
    assert np.allclose(meta_X[:, 1], 0.6)  # from model_b

def test_predict_ensemble_proba_missing_model():
    bundle = EnsembleInferenceBundle(
        stacking_model=MockStackingModel(),
        base_models={"model_a": MockSklearnModel()},
        base_model_order=("model_a", "model_b"),
        preprocessor=None,
        stacking_config={}
    )
    
    X = np.random.rand(1, 35)
    with pytest.raises(ValueError, match="missing required base models"):
        predict_ensemble_proba(bundle, X)

def test_wrapped_ensemble_model():
    bundle = EnsembleInferenceBundle(
        stacking_model=MockStackingModel(),
        base_models={"model_a": MockSklearnModel()},
        base_model_order=("model_a",),
        preprocessor=None,
        stacking_config={}
    )
    wrapped = WrappedEnsembleModel(bundle)
    
    X = np.random.rand(2, 35)
    result = wrapped.predict_proba(X)
    assert result.shape == (2, 2)


def test_build_ensemble_meta_features_triggers_tabnet_disagreement_mitigation() -> None:
    stacking_model = MockStackingModel()
    base_models = {
        "logistic_regression": ConstantProbabilityModel(0.95),
        "random_forest": ConstantProbabilityModel(0.90),
        "xgboost": ConstantProbabilityModel(0.94),
        "lightgbm": ConstantProbabilityModel(0.96),
        "tabnet": ConstantProbabilityModel(0.03),
        "residual_mlp": ConstantProbabilityModel(0.93),
    }
    bundle = EnsembleInferenceBundle(
        stacking_model=stacking_model,
        base_models=base_models,
        base_model_order=(
            "logistic_regression",
            "random_forest",
            "xgboost",
            "lightgbm",
            "tabnet",
            "residual_mlp",
        ),
        preprocessor=None,
        stacking_config={
            "tabnet_mitigation": {
                "enabled": True,
                "min_peer_confidence": 0.8,
                "disagreement_threshold": 0.25,
                "max_blend_weight": 0.75,
            }
        },
    )

    meta_features = build_ensemble_meta_features(bundle, np.random.rand(1, 35))

    assert meta_features.mitigation_debug["trigger_mask"][0]
    assert meta_features.mitigation_debug["raw_tabnet_probability"][0] == pytest.approx(0.03)
    assert meta_features.mitigation_debug["peer_mean_probability"][0] > 0.9
    assert meta_features.mitigation_debug["adjusted_tabnet_probability"][0] > 0.03
    assert meta_features.mitigation_debug["adjusted_tabnet_probability"][0] < meta_features.mitigation_debug["peer_mean_probability"][0]


def test_build_ensemble_meta_features_does_not_trigger_when_tabnet_agrees_with_peers() -> None:
    stacking_model = MockStackingModel()
    base_models = {
        "logistic_regression": ConstantProbabilityModel(0.82),
        "random_forest": ConstantProbabilityModel(0.80),
        "xgboost": ConstantProbabilityModel(0.83),
        "lightgbm": ConstantProbabilityModel(0.84),
        "tabnet": ConstantProbabilityModel(0.79),
        "residual_mlp": ConstantProbabilityModel(0.81),
    }
    bundle = EnsembleInferenceBundle(
        stacking_model=stacking_model,
        base_models=base_models,
        base_model_order=(
            "logistic_regression",
            "random_forest",
            "xgboost",
            "lightgbm",
            "tabnet",
            "residual_mlp",
        ),
        preprocessor=None,
        stacking_config={},
    )

    meta_features = build_ensemble_meta_features(bundle, np.random.rand(1, 35))

    assert not meta_features.mitigation_debug["trigger_mask"][0]
    assert meta_features.mitigation_debug["adjusted_tabnet_probability"][0] == pytest.approx(
        meta_features.mitigation_debug["raw_tabnet_probability"][0]
    )


def test_predict_ensemble_proba_softens_tabnet_pathology_without_removing_it() -> None:
    stacking_model = MockStackingModel()
    base_models = {
        "logistic_regression": ConstantProbabilityModel(0.95),
        "random_forest": ConstantProbabilityModel(0.90),
        "xgboost": ConstantProbabilityModel(0.94),
        "lightgbm": ConstantProbabilityModel(0.96),
        "tabnet": ConstantProbabilityModel(0.03),
        "residual_mlp": ConstantProbabilityModel(0.93),
    }
    bundle = EnsembleInferenceBundle(
        stacking_model=stacking_model,
        base_models=base_models,
        base_model_order=(
            "logistic_regression",
            "random_forest",
            "xgboost",
            "lightgbm",
            "tabnet",
            "residual_mlp",
        ),
        preprocessor=None,
        stacking_config={},
    )

    result = predict_ensemble_proba(bundle, np.random.rand(1, 35))
    adjusted_meta = stacking_model.last_meta_X

    assert result.shape == (1, 2)
    assert adjusted_meta.shape == (1, 6)
    assert adjusted_meta[0, 4] > 0.03
    assert adjusted_meta[0, 4] < 0.95
