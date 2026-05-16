# Backend Runtime Architecture

This document explains the current backend architecture decisions that a frontend or deployment developer must understand before modifying any backend code.

## Why Logistic Regression Is The Active Runtime Model

The `production_manifest.json` currently points to `logistic_regression` (v0.1.0) as the active runtime model. This is intentional.

The calibrated stacking ensemble (v0.2.0) was fully trained, calibrated, and promoted offline. However, it was **reverted** from runtime serving because:

1. **Feature dimension mismatch.** The stacking ensemble's `CalibratedClassifierCV` wraps a `LogisticRegression` meta-learner that expects **6 input features** (one probability column from each base model: logistic, RF, XGBoost, LightGBM, TabNet, MLP). The scoring service at `backend/app/services/scoring.py` currently sends **35 raw features** directly to `model.predict_proba()`. This causes a `ValueError: X has 35 features, but LogisticRegression is expecting 6 features as input`.

2. **No serving adapter exists.** Serving the ensemble requires a multi-step inference path:
   - Load all 6 base models
   - Transform raw features → preprocessed features
   - Run each base model's `predict_proba()` on the preprocessed features
   - Stack the 6 probability columns into a (1, 6) meta-feature matrix
   - Pass the meta-feature matrix to the calibrated stacking model
   - Return the final calibrated probability

   This adapter does not exist in the scoring service yet.

3. **Logistic regression is fully functional.** The logistic model accepts the same 35-feature preprocessed input that the scoring service already constructs. All explainability artifacts (SHAP, DICE), governance reports (fairness, PSI, global importance), and smoke tests are validated against this model.

## How The Future Ensemble Serving Adapter Should Work

When a developer implements ensemble serving, the following changes are needed:

### 1. Create `backend/ml/inference/ensemble_adapter.py`

```python
def predict_ensemble_proba(
    raw_features: pd.DataFrame,
    preprocessor: ColumnTransformer,
    base_models: dict[str, Any],  # name → fitted model
    stacking_model: CalibratedClassifierCV,
    base_model_order: list[str],
) -> np.ndarray:
    """Transform raw features → base probabilities → stacking prediction."""
    processed = preprocessor.transform(raw_features)
    meta_features = np.column_stack([
        base_models[name].predict_proba(processed)[:, 1]
        for name in base_model_order
    ])
    return stacking_model.predict_proba(meta_features)
```

### 2. Update `artifact_loader.py`

- When manifest `runtime_model_type` is `"ensemble"`, load all 6 base models in addition to the stacking model
- Store them in the `RuntimeArtifactBundle`

### 3. Update `scoring.py`

- Detect model type from the loaded bundle
- Route to either direct `predict_proba()` (classical) or the ensemble adapter

### 4. Update manifest

- Switch `runtime_model_name` to `stacking_ensemble`
- Add base model paths to the manifest artifact list
- Regenerate checksums

### 5. Update smoke tests

- Update `test_checked_in_runtime_bundle_smoke.py` assertions for the new model name/version

## Systems That Are Stable And Should Not Be Casually Modified

| System | Path | Why It's Frozen |
|---|---|---|
| Manifest loader | `backend/app/core/artifact_loader.py` | Checksum verification, artifact validation, 6 integration tests |
| Scoring service | `backend/app/services/scoring.py` | Tested E2E with checked-in bundle |
| Feature assembly | `backend/ml/inference/feature_assembly.py` | Canonical 35-feature pipeline, 4 integration tests |
| Preprocessing pipeline | `backend/ml/preprocessing/pipeline.py` | Train-fitted preprocessor + text PCA, serialized artifacts depend on it |
| Feature registry | `backend/ml/features/feature_registry.py` | 35 features, 6 unit tests, every other system depends on this |
| Analytics service | `backend/app/services/analytics.py` | Report-backed, 12 analytics endpoint tests |
| Health route | `backend/app/api/v1/routes/health.py` | Manifest-backed health reporting |
| Production manifest | `models/registry/production_manifest.json` | SHA256-verified, 11 artifact checksums |

**Rule:** If you need to change any of these files, run the full test suite first (`pytest tests/ -v`) and verify all 93+ tests pass before AND after your change.

## Artifact / Manifest Relationships

```
production_manifest.json
 ├── runtime_model      → models/artifacts/logistic_best.pkl
 ├── preprocessor       → models/preprocessors/preprocessor.pkl
 ├── text_pca           → models/preprocessors/text_pca.pkl
 ├── shap_explainer     → models/explainers/shap_explainer.pkl
 ├── dice_explainer     → models/explainers/dice_explainer.pkl
 ├── metrics            → models/reports/metrics.json
 ├── baseline_metrics   → models/reports/baseline_metrics.json
 ├── fairness_report    → models/reports/fairness_report.json
 ├── psi_report         → models/reports/psi_report.json
 ├── global_importance  → models/reports/global_importance.json
 └── population_percentiles → models/reports/population_percentiles.json
```

Each artifact has a SHA256 checksum in the manifest. At startup, the backend:
1. Loads and parses the manifest
2. Verifies each artifact's checksum against the file on disk
3. Loads and validates each artifact (deserialize, type check, feature count)
4. Reports loaded/missing/invalid artifacts in `/api/health`

If any **scoring-critical** artifact (model, preprocessor) fails validation, the backend refuses to score and returns `503`.

## Explainability / Runtime Dependencies

| Artifact | Purpose | Runtime Dependency |
|---|---|---|
| `shap_explainer.pkl` | Per-user SHAP explanations in `/api/score` | Optional — score works without it, but `explanation` array is empty |
| `dice_explainer.pkl` | Counterfactual improvement actions in `/api/score` | Optional — score works without it, but `counterfactual_actions` is empty |
| `global_importance.json` | Dashboard feature importance | Read-only by `/api/global-importance` |
| `fairness_report.json` | Dashboard fairness audit | Read-only by `/api/fairness-report` |
| `psi_report.json` | Dashboard drift report | Read-only by `/api/drift-report` |

## Environment / Version Constraints

| Component | Version | Notes |
|---|---|---|
| Python | ≥3.10 | Tested on 3.14.3 |
| scikit-learn | ≥1.8.0 | Required — artifacts are serialized with this version |
| pytorch-tabnet | 4.1.0 | Offline training only, not needed for serving |
| PyTorch | ≥2.0 | Transitive dep of tabnet/MLP, not needed for logistic serving |
| Node.js | ≥18 | Frontend build |
| Vite | ≥5.0 | Frontend dev server |
| React | ≥18 | Frontend framework |

The backend `requirements.txt` pins all ML dependencies. The frontend `package.json` pins all JS dependencies. Do not upgrade either without running the full test suite.
