# Release and Runtime Governance

This document outlines the strict procedures for verifying, releasing, and promoting backend artifacts for the AlterScore application. As a financial application, all changes to the model and runtime must be explicitly tracked, verified, and audited.

## 1. Release Checklist

Before marking the backend as ready for a new release or promoting to production:
- [ ] **Tests Pass:** `python -m pytest tests/` passes with 100% success on the relevant backend, ML, and API suite.
- [ ] **Data Drift Acceptable:** `/api/drift-report` shows no core feature with PSI > 0.30 (Alert) without documented explanation.
- [ ] **Fairness Maintained:** `/api/fairness-report` shows acceptable AUC deviation (< 0.07 gap) across demographic groups.
- [ ] **Calibration Intact:** `/api/calibration-curve` shows the predicted probability reliably matches the fraction of positive outcomes.
- [ ] **Promotion Gates Clean:** `python -m backend.ml.registry.promotion_gates --manifest models/registry/production_manifest.json --require-clean-pass` passes against `models/registry/promotion_gate_policy.json`.
- [ ] **API Contracts Unchanged:** No breaking changes introduced to the request/response payloads defined in `API_CONTRACTS.md`.

## 2. Manifest Promotion Checklist

Models are not promoted manually by copying files. We use `production_manifest.json` with strict SHA256 checksums to enforce integrity.

1. **Verify candidate training completed:** `models/registry/candidate_manifest.json` exists.
2. **Review Governance Reports:** Compare `metrics.json`, `fairness_report.json`, and `psi_report.json` against the active model.
3. **Run Promotion Gates:** Run `python -m backend.ml.registry.promotion_gates --manifest models/registry/candidate_manifest.json --require-clean-pass`.
4. **Execute Promotion:** Run `python -m backend.ml.training.ensemble.promote_ensemble`.
5. **Audit Checksums:** Verify that `production_manifest.json` has updated SHA256 hashes for all 18+ ensemble and base model artifacts.
6. **Commit Manifest:** The `production_manifest.json`, `promotion_gate_policy.json`, and all `models/` artifacts must be committed to source control (tracked by LFS if applicable).

## 3. Runtime Validation Workflow

When the backend starts up, the `artifact_loader.py` enforces runtime validation:

- **Checksum Verification:** Every artifact path defined in `production_manifest.json` is hashed and checked against the expected checksum. If any hash mismatches, startup is aborted.
- **Dependency Flow:** Base models are loaded first, followed by the stacking meta-learner, and finally the explainers (SHAP, DICE).
- **Health Check Status:** Ensure the `/api/health` endpoint returns `"status": "ok"` and `"model_loaded": true`.

## 4. Rollback Procedure

If a deployed model exhibits degraded performance or unexpected bias in production:

1. Identify the previous stable commit containing the known-good `production_manifest.json`.
2. Revert the commit that updated the manifest and artifacts: `git revert <commit-hash>`.
3. Restart the backend service. The application will strictly enforce loading the artifacts defined in the restored manifest.
4. Verify rollback success by checking `/api/health` to confirm the `model_version` matches the restored manifest.

## 5. Artifact Integrity Verification

To manually verify artifact integrity without starting the server, run the smoke tests:
`python -m pytest tests/integration/api/test_checked_in_runtime_bundle_smoke.py`
This test suite initializes the artifact loader, validates all checksums, tests the ensemble inference bundle, and performs an end-to-end score calculation.
