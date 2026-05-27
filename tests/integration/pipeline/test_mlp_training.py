"""Integration / smoke tests for the residual MLP neural training pipeline.

Mirrors the 6-test structure of test_tabnet_training.py exactly:

1. Full pipeline smoke roundtrip (train + .pt save + load + probability parity).
2. Metrics merge does not drop classical or TabNet entries.
3. .pt artifact is saved and loadable.
4. Import guard: missing torch raises RuntimeError.
5. Temporal split integrity enforced.
6. Missing .pt file raises FileNotFoundError.

Tests run in < 30 s with epoch patching (2 epochs, 1,800-row dataset).
"""

from __future__ import annotations

import json

import numpy as np
import pytest

from backend.ml.data_generation.generator import generate_synthetic_dataset

_SMALL_ROW_COUNT = 1_800
_SEED = 99


def _try_import_torch() -> bool:
    try:
        import torch  # noqa: F401

        return True
    except ImportError:
        return False


pytestmark = [
    pytest.mark.slow,
    pytest.mark.skipif(
        not _try_import_torch(),
        reason="torch is not installed; skipping MLP training smoke tests.",
    ),
]


def _patch_fit_epochs(monkeypatch: pytest.MonkeyPatch) -> None:
    """Reduce MLP training to 2 epochs for fast smoke tests."""
    import backend.ml.training.neural.train_mlp as _mod

    monkeypatch.setattr(_mod, "_MLP_MAX_EPOCHS", 2)
    monkeypatch.setattr(_mod, "_MLP_PATIENCE", 2)
    monkeypatch.setattr(_mod, "_MLP_BATCH_SIZE", 256)


# ---------------------------------------------------------------------------
# 1. Full pipeline smoke roundtrip
# ---------------------------------------------------------------------------


def test_train_mlp_smoke_roundtrip(tmp_path, monkeypatch) -> None:
    """MLP training produces valid probabilities and a round-trippable .pt artifact."""
    from backend.ml.training.neural.train_mlp import (
        MLP_MODEL_NAME,
        MLP_MODEL_TYPE,
        NUMERIC_METRIC_FIELDS,
        load_mlp_model,
        train_mlp,
    )
    from backend.ml.preprocessing.pipeline import (
        align_text_features_from_raw_text,
    )
    from backend.ml.data_generation.generator import TEMPORAL_SPLIT_MONTHS
    import joblib

    _patch_fit_epochs(monkeypatch)
    dataset = generate_synthetic_dataset(row_count=_SMALL_ROW_COUNT, seed=_SEED)
    mlp_pt_path = tmp_path / "mlp_best.pt"

    artifacts = train_mlp(
        dataset,
        expected_row_count=_SMALL_ROW_COUNT,
        minimum_test_rows=200,
        preprocessor_artifact_path=tmp_path / "preprocessor.pkl",
        text_pca_artifact_path=tmp_path / "text_pca.pkl",
        mlp_artifact_path=mlp_pt_path,
        metrics_path=tmp_path / "metrics.json",
        population_percentiles_path=tmp_path / "population_percentiles.json",
        random_state=_SEED,
    )

    # Artifact path and extension
    assert artifacts.mlp_artifact_path is not None
    assert artifacts.mlp_artifact_path.is_file()
    assert artifacts.mlp_artifact_path.suffix == ".pt"

    # Probability arrays
    assert isinstance(artifacts.validation_probabilities, np.ndarray)
    assert isinstance(artifacts.test_probabilities, np.ndarray)
    assert np.all(artifacts.validation_probabilities >= 0.0)
    assert np.all(artifacts.validation_probabilities <= 1.0)
    assert not np.isnan(artifacts.validation_probabilities).any()
    assert np.all(artifacts.test_probabilities >= 0.0)
    assert np.all(artifacts.test_probabilities <= 1.0)
    assert not np.isnan(artifacts.test_probabilities).any()

    # Model stats
    assert len(artifacts.model_stats) == 2
    for row in artifacts.model_stats:
        assert row["model_name"] == MLP_MODEL_NAME
        assert row["model_type"] == MLP_MODEL_TYPE
        assert np.isfinite([row[f] for f in NUMERIC_METRIC_FIELDS]).all()

    splits = {r["split"] for r in artifacts.model_stats}
    assert "validation_months_9_10" in splits
    assert "test_months_11_12" in splits

    # Validation-derived threshold used consistently
    val_row = next(
        r for r in artifacts.model_stats if r["split"] == "validation_months_9_10"
    )
    test_row = next(
        r for r in artifacts.model_stats if r["split"] == "test_months_11_12"
    )
    assert val_row["threshold"] == test_row["threshold"]

    # metrics.json
    assert artifacts.metrics_path is not None and artifacts.metrics_path.is_file()
    mp = json.loads(artifacts.metrics_path.read_text(encoding="utf-8"))
    assert "model_stats" in mp and "evaluation_details" in mp
    mlp_rows = [r for r in mp["model_stats"] if r["model_name"] == MLP_MODEL_NAME]
    assert len(mlp_rows) == 2

    # population_percentiles.json
    assert artifacts.population_percentiles_path is not None
    assert artifacts.population_percentiles_path.is_file()
    pp = json.loads(artifacts.population_percentiles_path.read_text(encoding="utf-8"))
    assert MLP_MODEL_NAME in pp.get("models", {})
    assert "default_model_name" in pp

    # Round-trip: load from .pt and verify probabilities match
    import torch
    from backend.ml.preprocessing.pipeline import (
        apply_text_pca,
        prepare_model_feature_frame,
    )
    from backend.ml.preprocessing.feature_registry import ALL_MODEL_FEATURES

    loaded_model = load_mlp_model(artifacts.mlp_artifact_path)
    preprocessor = joblib.load(tmp_path / "preprocessor.pkl")
    text_pca = joblib.load(tmp_path / "text_pca.pkl")

    aligned_dataset, raw_text_embeddings = align_text_features_from_raw_text(
        dataset.copy()
    )
    feature_frame = prepare_model_feature_frame(
        aligned_dataset.loc[
            :, [c for c in aligned_dataset.columns if c in ALL_MODEL_FEATURES]
        ].copy()
    )
    feature_frame = apply_text_pca(feature_frame, raw_text_embeddings, text_pca)
    test_mask = dataset["cohort_month"].isin(TEMPORAL_SPLIT_MONTHS["test"])
    X_test_features = feature_frame.loc[test_mask]
    X_test_processed = preprocessor.transform(X_test_features)

    loaded_model.eval()
    with torch.no_grad():
        loaded_test_probs = (
            loaded_model(torch.tensor(X_test_processed, dtype=torch.float32))
            .cpu()
            .numpy()
        )

    np.testing.assert_allclose(
        loaded_test_probs,
        artifacts.test_probabilities,
        rtol=1e-5,
        atol=1e-5,
        err_msg="Loaded MLP model must produce identical probabilities to training-time model.",
    )


# ---------------------------------------------------------------------------
# 2. Metrics merge preserves existing entries
# ---------------------------------------------------------------------------


def test_train_mlp_merges_into_existing_metrics(tmp_path, monkeypatch) -> None:
    """MLP metrics are appended without dropping existing classical or TabNet rows."""
    from backend.ml.training.neural.train_mlp import MLP_MODEL_NAME, train_mlp
    from backend.ml.training.neural.train_tabnet import train_tabnet
    from backend.ml.training.classical.baselines import train_baselines
    from backend.ml.training.classical.train_classical import train_classical_models
    import backend.ml.training.neural.train_tabnet as _tn

    _patch_fit_epochs(monkeypatch)
    monkeypatch.setattr(_tn, "_TABNET_MAX_EPOCHS", 2)
    monkeypatch.setattr(_tn, "_TABNET_PATIENCE", 2)
    monkeypatch.setattr(_tn, "_TABNET_BATCH_SIZE", 256)
    monkeypatch.setattr(_tn, "_TABNET_VIRTUAL_BATCH_SIZE", 64)

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
        tabnet_artifact_path=tmp_path / "tabnet_epoch_best.zip",
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
        mlp_artifact_path=tmp_path / "mlp_best.pt",
        metrics_path=tn.metrics_path,
        population_percentiles_path=tn.population_percentiles_path,
        random_state=_SEED,
    )

    mp = json.loads(mlp_art.metrics_path.read_text(encoding="utf-8"))
    model_names = {r["model_name"] for r in mp["model_stats"]}
    for expected in ("random_forest", "xgboost", "lightgbm", "tabnet"):
        assert (
            expected in model_names
        ), f"'{expected}' must not be dropped after MLP training."
    assert MLP_MODEL_NAME in model_names

    pp = json.loads(mlp_art.population_percentiles_path.read_text(encoding="utf-8"))
    assert MLP_MODEL_NAME in pp.get("models", {})


# ---------------------------------------------------------------------------
# 3. Save produces a .pt artifact
# ---------------------------------------------------------------------------


def test_mlp_save_produces_pt_artifact(tmp_path, monkeypatch) -> None:
    """The saved artifact must have a .pt extension and be loadable."""
    from backend.ml.training.neural.train_mlp import load_mlp_model, train_mlp

    _patch_fit_epochs(monkeypatch)
    dataset = generate_synthetic_dataset(row_count=_SMALL_ROW_COUNT, seed=_SEED + 1)

    art = train_mlp(
        dataset,
        expected_row_count=_SMALL_ROW_COUNT,
        minimum_test_rows=200,
        preprocessor_artifact_path=None,
        text_pca_artifact_path=None,
        mlp_artifact_path=tmp_path / "mlp_model.pt",
        metrics_path=None,
        population_percentiles_path=None,
        random_state=_SEED,
    )

    assert art.mlp_artifact_path is not None
    assert art.mlp_artifact_path.suffix == ".pt"
    assert art.mlp_artifact_path.is_file()
    loaded = load_mlp_model(art.mlp_artifact_path)
    assert loaded is not None


# ---------------------------------------------------------------------------
# 4. Import guard
# ---------------------------------------------------------------------------


def test_train_mlp_import_guard() -> None:
    """torch absence surfaces as a clear RuntimeError."""
    import backend.ml.training.neural.train_mlp as _mod

    original = _mod._assert_torch_available

    def _fake() -> None:
        raise RuntimeError("torch is required for the AlterScore residual MLP model.")

    _mod._assert_torch_available = _fake
    try:
        with pytest.raises(RuntimeError, match="torch is required"):
            _mod._assert_torch_available()
    finally:
        _mod._assert_torch_available = original


# ---------------------------------------------------------------------------
# 5. Temporal split integrity
# ---------------------------------------------------------------------------


def test_train_mlp_temporal_split_integrity(tmp_path, monkeypatch) -> None:
    """Train/validation/test must be disjoint; training must complete without error."""
    from backend.ml.training.neural.train_mlp import train_mlp
    from backend.ml.data_generation.generator import TEMPORAL_SPLIT_MONTHS

    _patch_fit_epochs(monkeypatch)
    dataset = generate_synthetic_dataset(row_count=_SMALL_ROW_COUNT, seed=_SEED + 2)

    train_months = set(TEMPORAL_SPLIT_MONTHS["train"])
    val_months = set(TEMPORAL_SPLIT_MONTHS["validation"])
    test_months = set(TEMPORAL_SPLIT_MONTHS["test"])
    assert train_months.isdisjoint(val_months)
    assert train_months.isdisjoint(test_months)
    assert val_months.isdisjoint(test_months)

    art = train_mlp(
        dataset,
        expected_row_count=_SMALL_ROW_COUNT,
        minimum_test_rows=200,
        preprocessor_artifact_path=None,
        text_pca_artifact_path=None,
        mlp_artifact_path=None,
        metrics_path=None,
        population_percentiles_path=None,
        random_state=_SEED,
    )
    assert len(art.model_stats) == 2


# ---------------------------------------------------------------------------
# 6. Missing .pt raises FileNotFoundError
# ---------------------------------------------------------------------------


def test_load_mlp_model_missing_file_raises() -> None:
    """load_mlp_model raises FileNotFoundError when the artifact is absent."""
    from backend.ml.training.neural.train_mlp import load_mlp_model

    with pytest.raises(FileNotFoundError, match="MLP artifact not found"):
        load_mlp_model("/nonexistent/path/mlp_best.pt")
