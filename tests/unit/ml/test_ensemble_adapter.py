import numpy as np
import pytest
import torch
import torch.nn as nn

from backend.ml.inference.ensemble_adapter import (
    EnsembleInferenceBundle,
    WrappedEnsembleModel,
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
