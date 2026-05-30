"""Integration / smoke tests for the stacking ensemble training pipeline.

Test structure (6 tests mirroring TabNet/MLP pattern):

1. Full pipeline smoke roundtrip — train from StackingInputs, save .pkl,
   load, verify probability round-trip.
2. Metrics merge preserves all existing base-model entries.
3. .pkl artifact is saved and loadable via load_stacking_model.
4. Temporal split integrity — validation and test sets are disjoint.
5. Missing base model probability array raises ValueError.
6. Missing .pkl artifact raises FileNotFoundError.
"""

from __future__ import annotations

import json
import numpy as np
import pytest

from backend.ml.data_generation.generator import (
    TEMPORAL_SPLIT_MONTHS,
    generate_synthetic_dataset,
)
from backend.ml.training.ensemble.train_stacking import (
    BASE_MODEL_ORDER,
    ENSEMBLE_MODEL_NAME,
    StackingInputs,
    load_stacking_model,
    predict_stacking_proba,
    train_stacking,
)

pytestmark = pytest.mark.slow

_SMALL_ROW_COUNT = 1_800
_SEED = 7


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_fake_stacking_inputs(n_val: int = 400, n_test: int = 200) -> StackingInputs:
    """Generate deterministic random probability arrays for all base models."""
    rng = np.random.default_rng(_SEED)
    val_probs = {name: rng.uniform(0.2, 0.9, size=n_val) for name in BASE_MODEL_ORDER}
    test_probs = {name: rng.uniform(0.2, 0.9, size=n_test) for name in BASE_MODEL_ORDER}
    y_val = rng.integers(0, 2, size=n_val)
    y_test = rng.integers(0, 2, size=n_test)
    return StackingInputs(
        validation_probabilities=val_probs,
        test_probabilities=test_probs,
        y_validation=y_val.astype(int),
        y_test=y_test.astype(int),
    )


def _patch_base_epochs(monkeypatch: pytest.MonkeyPatch) -> None:
    """Reduce neural base model epochs for fast smoke tests."""
    import backend.ml.training.neural.train_tabnet as _tn
    import backend.ml.training.neural.train_mlp as _mlp

    monkeypatch.setattr(_tn, "_TABNET_MAX_EPOCHS", 2)
    monkeypatch.setattr(_tn, "_TABNET_PATIENCE", 2)
    monkeypatch.setattr(_tn, "_TABNET_BATCH_SIZE", 256)
    monkeypatch.setattr(_tn, "_TABNET_VIRTUAL_BATCH_SIZE", 64)
    monkeypatch.setattr(_mlp, "_MLP_MAX_EPOCHS", 2)
    monkeypatch.setattr(_mlp, "_MLP_PATIENCE", 2)
    monkeypatch.setattr(_mlp, "_MLP_BATCH_SIZE", 256)


# ---------------------------------------------------------------------------
# 1. Full pipeline smoke roundtrip (using pre-computed StackingInputs)
# ---------------------------------------------------------------------------


def test_train_stacking_smoke_roundtrip(tmp_path) -> None:
    """Stacking trains, saves .pkl, loads, and round-trips identical probs."""
    artifact_path = tmp_path / "calibrated_stacking.pkl"
    inputs = _make_fake_stacking_inputs()

    art = train_stacking(
        stacking_inputs=inputs,
        stacking_artifact_path=artifact_path,
        stacking_config_path=tmp_path / "calibrated_stacking_config.json",
        metrics_path=tmp_path / "metrics.json",
        population_percentiles_path=tmp_path / "population_percentiles.json",
        random_state=_SEED,
    )

    # Artifact exists and is a .pkl
    assert art.stacking_artifact_path is not None
    assert art.stacking_artifact_path.is_file()
    assert art.stacking_artifact_path.suffix == ".pkl"

    # Probability arrays are valid
    assert isinstance(art.validation_probabilities, np.ndarray)
    assert isinstance(art.test_probabilities, np.ndarray)
    assert np.all(art.validation_probabilities >= 0.0)
    assert np.all(art.validation_probabilities <= 1.0)
    assert not np.isnan(art.validation_probabilities).any()
    assert np.all(art.test_probabilities >= 0.0)
    assert np.all(art.test_probabilities <= 1.0)
    assert not np.isnan(art.test_probabilities).any()

    # Model stats — two rows (val + test)
    assert len(art.model_stats) == 2
    splits = {r["split"] for r in art.model_stats}
    assert "validation_months_9_10" in splits
    assert "test_months_11_12" in splits
    for row in art.model_stats:
        assert row["model_name"] == ENSEMBLE_MODEL_NAME
        assert np.isfinite(row["auc_roc"])

    # Base model order preserved
    assert art.base_model_order == BASE_MODEL_ORDER

    # metrics.json written
    assert art.metrics_path is not None and art.metrics_path.is_file()
    mp = json.loads(art.metrics_path.read_text(encoding="utf-8"))
    assert any(r["model_name"] == ENSEMBLE_MODEL_NAME for r in mp["model_stats"])

    # population_percentiles.json written
    assert art.population_percentiles_path is not None
    pp = json.loads(art.population_percentiles_path.read_text(encoding="utf-8"))
    assert ENSEMBLE_MODEL_NAME in pp.get("models", {})
    assert pp.get("default_model_name") == ENSEMBLE_MODEL_NAME  # best test AUC wins

    # Round-trip: load and predict
    loaded = load_stacking_model(artifact_path)
    rt_probs = predict_stacking_proba(loaded, inputs.test_probabilities)
    np.testing.assert_allclose(
        rt_probs,
        art.test_probabilities,
        rtol=1e-6,
        atol=1e-6,
        err_msg="Loaded stacking model must reproduce identical probabilities.",
    )

    # Config sidecar
    assert art.stacking_config_path is not None and art.stacking_config_path.is_file()
    cfg = json.loads(art.stacking_config_path.read_text(encoding="utf-8"))
    assert cfg["model_name"] == ENSEMBLE_MODEL_NAME
    assert cfg["base_model_order"] == list(BASE_MODEL_ORDER)
    assert cfg["calibration"]["method"] == "isotonic"


# ---------------------------------------------------------------------------
# 2. Metrics merge preserves existing entries
# ---------------------------------------------------------------------------


def test_train_stacking_merges_into_existing_metrics(tmp_path) -> None:
    """Stacking row is appended; existing model rows are not dropped."""
    from backend.ml.training.neural.train_tabnet import train_tabnet
    from backend.ml.training.neural.train_mlp import train_mlp
    from backend.ml.training.classical.baselines import train_baselines
    from backend.ml.training.classical.train_classical import train_classical_models
    import backend.ml.training.neural.train_tabnet as _tn
    import backend.ml.training.neural.train_mlp as _mlp

    # Patch epochs
    _tn._TABNET_MAX_EPOCHS = 2
    _tn._TABNET_PATIENCE = 2
    _tn._TABNET_BATCH_SIZE = 256
    _tn._TABNET_VIRTUAL_BATCH_SIZE = 64
    _mlp._MLP_MAX_EPOCHS = 2
    _mlp._MLP_PATIENCE = 2
    _mlp._MLP_BATCH_SIZE = 256

    dataset = generate_synthetic_dataset(row_count=_SMALL_ROW_COUNT, seed=_SEED)

    bl = train_baselines(
        dataset,
        expected_row_count=_SMALL_ROW_COUNT,
        minimum_test_rows=200,
        preprocessor_artifact_path=tmp_path / "preprocessor.pkl",
        text_pca_artifact_path=tmp_path / "text_pca.pkl",
        logistic_artifact_path=tmp_path / "logistic_best.pkl",
        baseline_metrics_path=tmp_path / "baseline_metrics.json",
        metrics_path=tmp_path / "metrics.json",
        population_percentiles_path=tmp_path / "population_percentiles.json",
        psi_report_path=None,
        fairness_report_path=None,
        global_importance_path=None,
        dice_explainer_path=None,
    )

    cl = train_classical_models(
        dataset,
        expected_row_count=_SMALL_ROW_COUNT,
        minimum_test_rows=200,
        preprocessor_artifact_path=tmp_path / "preprocessor.pkl",
        text_pca_artifact_path=tmp_path / "text_pca.pkl",
        random_forest_artifact_path=tmp_path / "rf_best.pkl",
        xgboost_artifact_path=tmp_path / "xgb_best.pkl",
        lightgbm_artifact_path=tmp_path / "lgbm_best.pkl",
        logistic_artifact_path=bl.logistic_model_path,
        baseline_metrics_path=bl.baseline_metrics_path,
        metrics_path=bl.metrics_path,
        population_percentiles_path=bl.population_percentiles_path,
        psi_report_path=None,
        fairness_report_path=None,
        global_importance_path=None,
        dice_explainer_path=None,
        random_state=_SEED,
    )

    tn = train_tabnet(
        dataset,
        expected_row_count=_SMALL_ROW_COUNT,
        minimum_test_rows=200,
        preprocessor_artifact_path=tmp_path / "preprocessor.pkl",
        text_pca_artifact_path=tmp_path / "text_pca.pkl",
        tabnet_artifact_path=None,
        metrics_path=cl.metrics_path,
        population_percentiles_path=cl.population_percentiles_path,
        random_state=_SEED,
    )

    mlp_art = train_mlp(
        dataset,
        expected_row_count=_SMALL_ROW_COUNT,
        minimum_test_rows=200,
        preprocessor_artifact_path=tmp_path / "preprocessor.pkl",
        text_pca_artifact_path=tmp_path / "text_pca.pkl",
        mlp_artifact_path=None,
        metrics_path=tn.metrics_path,
        population_percentiles_path=tn.population_percentiles_path,
        random_state=_SEED,
    )

    # Build StackingInputs from already-trained artifacts
    from backend.ml.preprocessing.pipeline import (
        align_text_features_from_raw_text,
        prepare_temporal_data,
        transform_features,
    )
    import joblib

    aligned, raw_emb = align_text_features_from_raw_text(dataset.copy())
    prepared = prepare_temporal_data(
        aligned,
        raw_text_embeddings=raw_emb,
        text_pca_random_state=_SEED,
        text_pca_artifact_path=None,
    )
    y_val = prepared.validation.y.to_numpy(dtype=int)
    y_test_arr = prepared.test.y.to_numpy(dtype=int)

    # Load saved preprocessor and logistic model to derive logistic probs
    pre = joblib.load(str(tmp_path / "preprocessor.pkl"))
    log_model = joblib.load(str(tmp_path / "logistic_best.pkl"))
    Xv = transform_features(pre, prepared.validation.X)
    Xt = transform_features(pre, prepared.test.X)
    logistic_val = log_model.predict_proba(Xv)[:, 1].astype(float)
    logistic_test = log_model.predict_proba(Xt)[:, 1].astype(float)

    inputs = StackingInputs(
        validation_probabilities={
            "logistic_regression": logistic_val,
            "random_forest": cl.validation_probabilities["random_forest"],
            "xgboost": cl.validation_probabilities["xgboost"],
            "lightgbm": cl.validation_probabilities["lightgbm"],
            "tabnet": tn.validation_probabilities,
            "residual_mlp": mlp_art.validation_probabilities,
        },
        test_probabilities={
            "logistic_regression": logistic_test,
            "random_forest": cl.test_probabilities["random_forest"],
            "xgboost": cl.test_probabilities["xgboost"],
            "lightgbm": cl.test_probabilities["lightgbm"],
            "tabnet": tn.test_probabilities,
            "residual_mlp": mlp_art.test_probabilities,
        },
        y_validation=y_val,
        y_test=y_test_arr,
    )

    stk = train_stacking(
        stacking_inputs=inputs,
        stacking_artifact_path=tmp_path / "calibrated_stacking.pkl",
        stacking_config_path=None,
        metrics_path=mlp_art.metrics_path,
        population_percentiles_path=mlp_art.population_percentiles_path,
        random_state=_SEED,
    )

    mp = json.loads(stk.metrics_path.read_text(encoding="utf-8"))
    model_names = {r["model_name"] for r in mp["model_stats"]}
    for expected in ("random_forest", "xgboost", "lightgbm", "tabnet", "residual_mlp"):
        assert expected in model_names, f"'{expected}' dropped after stacking."
    assert ENSEMBLE_MODEL_NAME in model_names

    pp = json.loads(stk.population_percentiles_path.read_text(encoding="utf-8"))
    assert ENSEMBLE_MODEL_NAME in pp.get("models", {})


# ---------------------------------------------------------------------------
# 3. .pkl artifact saved and loadable
# ---------------------------------------------------------------------------


def test_stacking_save_produces_pkl_artifact(tmp_path) -> None:
    inputs = _make_fake_stacking_inputs()
    art = train_stacking(
        stacking_inputs=inputs,
        stacking_artifact_path=tmp_path / "stacking.pkl",
        stacking_config_path=None,
        metrics_path=None,
        population_percentiles_path=None,
        random_state=_SEED,
    )
    assert art.stacking_artifact_path is not None
    assert art.stacking_artifact_path.suffix == ".pkl"
    assert art.stacking_artifact_path.is_file()
    loaded = load_stacking_model(art.stacking_artifact_path)
    assert loaded is not None


# ---------------------------------------------------------------------------
# 4. Temporal split integrity
# ---------------------------------------------------------------------------


def test_train_stacking_temporal_split_integrity() -> None:
    train_months = set(TEMPORAL_SPLIT_MONTHS["train"])
    val_months = set(TEMPORAL_SPLIT_MONTHS["validation"])
    test_months = set(TEMPORAL_SPLIT_MONTHS["test"])
    assert train_months.isdisjoint(val_months)
    assert train_months.isdisjoint(test_months)
    assert val_months.isdisjoint(test_months)

    inputs = _make_fake_stacking_inputs()
    art = train_stacking(
        stacking_inputs=inputs,
        stacking_artifact_path=None,
        stacking_config_path=None,
        metrics_path=None,
        population_percentiles_path=None,
        random_state=_SEED,
    )
    assert len(art.model_stats) == 2


# ---------------------------------------------------------------------------
# 5. Missing base model probability raises ValueError
# ---------------------------------------------------------------------------


def test_train_stacking_missing_base_model_raises() -> None:
    inputs = _make_fake_stacking_inputs()
    # Drop one required model
    del inputs.validation_probabilities["tabnet"]
    del inputs.test_probabilities["tabnet"]
    with pytest.raises(ValueError, match="Missing base model"):
        train_stacking(
            stacking_inputs=inputs,
            stacking_artifact_path=None,
            stacking_config_path=None,
            metrics_path=None,
            population_percentiles_path=None,
        )


# ---------------------------------------------------------------------------
# 6. Missing .pkl raises FileNotFoundError
# ---------------------------------------------------------------------------


def test_load_stacking_model_missing_file_raises() -> None:
    with pytest.raises(FileNotFoundError, match="Stacking artifact not found"):
        load_stacking_model("/nonexistent/path/calibrated_stacking.pkl")
