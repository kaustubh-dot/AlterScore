"""Integration smoke tests for the ensemble promotion pipeline (Track D).

Test plan (5 tests):
  1. Full promotion smoke roundtrip — promotes ensemble, reads manifest, validates structure.
  2. SHAP explainer produced and validates against feature registry.
  3. DICE explainer produced with correct model_name.
  4. Global-importance report produced with ranked items.
  5. Manifest loads cleanly via ProductionManifest (checksum + schema validation).
"""

from __future__ import annotations

import json
import numpy as np
import pytest

from backend.ml.data_generation.generator import generate_synthetic_dataset
from backend.ml.explainability.shap_explainer import load_persisted_shap_explainer
from backend.ml.explainability.dice_explainer import load_persisted_dice_explainer
from backend.ml.preprocessing.feature_registry import ALL_MODEL_FEATURES
from backend.ml.registry.production_manifest import load_production_manifest
from backend.ml.training.ensemble.promote_ensemble import PromotionArtifacts, promote_ensemble
from backend.ml.training.ensemble.train_stacking import ENSEMBLE_MODEL_NAME


_SMALL_ROW_COUNT = 1_800
_SEED = 7


def _fast_promote(tmp_path, monkeypatch) -> PromotionArtifacts:
    """Run promote_ensemble with 2-epoch neural patches and small dataset."""
    import backend.ml.training.neural.train_tabnet as _tn
    import backend.ml.training.neural.train_mlp as _mlp
    monkeypatch.setattr(_tn, "_TABNET_MAX_EPOCHS", 2)
    monkeypatch.setattr(_tn, "_TABNET_PATIENCE", 2)
    monkeypatch.setattr(_tn, "_TABNET_BATCH_SIZE", 256)
    monkeypatch.setattr(_tn, "_TABNET_VIRTUAL_BATCH_SIZE", 64)
    monkeypatch.setattr(_mlp, "_MLP_MAX_EPOCHS", 2)
    monkeypatch.setattr(_mlp, "_MLP_PATIENCE", 2)
    monkeypatch.setattr(_mlp, "_MLP_BATCH_SIZE", 256)

    dataset = generate_synthetic_dataset(row_count=_SMALL_ROW_COUNT, seed=_SEED)
    return promote_ensemble(
        dataset=dataset,
        minimum_test_rows=200,
        random_state=_SEED,
        stacking_artifact_path=tmp_path / "calibrated_stacking.pkl",
        stacking_config_path=tmp_path / "calibrated_stacking_config.json",
        preprocessor_path=tmp_path / "preprocessor.pkl",
        text_pca_path=tmp_path / "text_pca.pkl",
        shap_explainer_path=tmp_path / "shap_explainer.pkl",
        dice_explainer_path=tmp_path / "dice_explainer.pkl",
        global_importance_path=tmp_path / "global_importance.json",
        fairness_report_path=tmp_path / "fairness_report.json",
        psi_report_path=tmp_path / "psi_report.json",
        metrics_path=tmp_path / "metrics.json",
        population_percentiles_path=tmp_path / "population_percentiles.json",
        manifest_path=tmp_path / "production_manifest.json",
        logistic_artifact_path=tmp_path / "logistic_best.pkl",
        random_forest_artifact_path=tmp_path / "rf_best.pkl",
        xgboost_artifact_path=tmp_path / "xgb_best.pkl",
        lightgbm_artifact_path=tmp_path / "lgbm_best.pkl",
        tabnet_artifact_path=tmp_path / "tabnet_epoch_best.zip",
        mlp_artifact_path=tmp_path / "mlp_best.pt",
    )


# ---------------------------------------------------------------------------
# 1. Full promotion smoke roundtrip
# ---------------------------------------------------------------------------


def test_promote_ensemble_smoke_roundtrip(tmp_path, monkeypatch) -> None:
    """promote_ensemble runs end-to-end and produces a valid manifest."""
    art = _fast_promote(tmp_path, monkeypatch)

    assert art.manifest_path.is_file()
    assert art.stacking_artifact_path.is_file()
    assert art.shap_explainer_path.is_file()
    assert art.dice_explainer_path.is_file()
    assert art.metrics_path.is_file()
    assert art.fairness_report_path.is_file()
    assert art.global_importance_path.is_file()
    assert np.isfinite(art.test_auc_roc)
    assert 0.0 <= art.test_auc_roc <= 1.0
    assert art.run_id.endswith("_ensemble_promotion")

    manifest_raw = json.loads(art.manifest_path.read_text(encoding="utf-8"))
    assert manifest_raw["runtime_model_name"] == "stacking_ensemble"
    assert manifest_raw["runtime_model_type"] == "ensemble"
    assert manifest_raw["promotion_status"] == "promoted"
    assert "artifacts" in manifest_raw
    assert "runtime_model" in manifest_raw["artifacts"]
    assert manifest_raw["metrics_summary"]["calibration"] == "isotonic"


# ---------------------------------------------------------------------------
# 2. SHAP explainer validates against feature registry
# ---------------------------------------------------------------------------


def test_shap_explainer_validates_against_feature_registry(tmp_path, monkeypatch) -> None:
    """SHAP explainer loads and passes validate() with canonical feature names."""
    art = _fast_promote(tmp_path, monkeypatch)
    explainer = load_persisted_shap_explainer(
        art.shap_explainer_path,
        expected_feature_names=ALL_MODEL_FEATURES,
    )
    assert explainer.model_name == ENSEMBLE_MODEL_NAME
    assert explainer.algorithm == "exact_linear_shap"
    assert len(explainer.feature_names) == len(ALL_MODEL_FEATURES)
    assert explainer.background_size > 0
    assert np.isfinite(explainer.coefficients).all()
    assert np.isfinite(explainer.background_mean).all()


# ---------------------------------------------------------------------------
# 3. DICE explainer has correct model_name
# ---------------------------------------------------------------------------


def test_dice_explainer_has_correct_model_name(tmp_path, monkeypatch) -> None:
    """DICE explainer loads cleanly and is labelled as calibrated_stacking."""
    art = _fast_promote(tmp_path, monkeypatch)
    explainer = load_persisted_dice_explainer(
        art.dice_explainer_path,
        expected_feature_names=ALL_MODEL_FEATURES,
    )
    assert explainer.model_name == ENSEMBLE_MODEL_NAME
    assert len(explainer.feature_policies) > 0


# ---------------------------------------------------------------------------
# 4. Global-importance report has ranked items
# ---------------------------------------------------------------------------


def test_global_importance_has_ranked_items(tmp_path, monkeypatch) -> None:
    """global_importance.json is produced with non-empty ranked items."""
    art = _fast_promote(tmp_path, monkeypatch)
    gi = json.loads(art.global_importance_path.read_text(encoding="utf-8"))
    assert isinstance(gi.get("items"), list)
    assert len(gi["items"]) > 0
    ranks = [item["rank"] for item in gi["items"]]
    assert ranks == sorted(ranks)
    for item in gi["items"]:
        assert item["mean_abs_shap"] >= 0.0


# ---------------------------------------------------------------------------
# 5. Manifest loads via ProductionManifest schema validator
# ---------------------------------------------------------------------------


def test_manifest_loads_via_production_manifest(tmp_path, monkeypatch) -> None:
    """production_manifest.json passes the full ProductionManifest schema validator."""
    art = _fast_promote(tmp_path, monkeypatch)
    m = load_production_manifest(art.manifest_path)
    assert m.runtime_model_name == "stacking_ensemble"
    assert m.runtime_model_type == "ensemble"
    assert m.promotion_status == "promoted"
    assert "runtime_model" in m.artifacts
    sha256 = m.artifact_checksum("runtime_model")
    assert len(sha256) == 64 and sha256.islower()
    from backend.ml.registry.production_manifest import compute_file_sha256
    actual = compute_file_sha256(art.stacking_artifact_path)
    assert sha256 == actual
