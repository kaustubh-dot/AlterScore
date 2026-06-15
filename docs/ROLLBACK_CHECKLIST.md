# AlterScore — Production Rollback Checklist

> Tied to manifest versions. Use this checklist when reverting from a failing or problematic production model back to a known-good state.

## Prerequisites

- Access to the git history containing the target rollback manifest
- Ability to restart the backend process (uvicorn)
- The target manifest's artifacts must exist at the paths declared in its `artifacts` block

---

## Currently Active Manifest

| Field | Value |
|-------|-------|
| manifest_version | `xgboost_monotonic_calibrated_v4` |
| model_version | `0.7.0` |
| runtime_model_name | `xgboost_monotonic` |
| runtime_model_type | `classical_monotonic` |
| promotion_status | `promoted` |
| gate_status | `passed` (under `promotion_gate_policy_v2`) |

## Known Rollback Targets

| Manifest Version | Model | Type | Commit / Notes |
|-------------------|-------|------|----------------|
| `xgboost_monotonic_calibrated_v4` | xgboost_monotonic v0.7.0 | classical_monotonic | Current active (cognition-driven, gaming-stack governance) |
| (stacking ensemble, if retained) | stacking_ensemble | ensemble | Pre-monotonic era; ensemble adapter still in codebase |

> [!WARNING]
> Rolling back to the stacking ensemble requires that the ensemble manifest and all its referenced artifacts (6 base models + meta-learner + preprocessors) are present at their declared paths. The `ensemble_adapter.py` runtime path is still functional for manifests declaring `runtime_model_type: "ensemble"`.

---

## Rollback Procedure

### Step 1: Identify the Rollback Target

```powershell
# View manifest history
git log --oneline --follow -- models/registry/production_manifest.json
```

Identify the commit hash of the last known-good manifest version.

### Step 2: Restore the Manifest and Artifacts

**Option A — Git revert (preferred if the rollback commit is recent):**
```powershell
git revert <bad-commit-hash>
```

**Option B — Checkout specific manifest version:**
```powershell
git checkout <good-commit-hash> -- models/registry/production_manifest.json models/artifacts/ models/preprocessors/ models/explainers/ models/reports/
```

> [!CAUTION]
> When restoring artifacts, you must restore **all** files referenced in the target manifest's `artifacts` block. Partial restores will cause SHA-256 checksum validation failures at startup.

### Step 3: Verify Artifact Integrity

```powershell
.\.venv312\Scripts\python.exe -m backend.ml.registry.promotion_gates --manifest models/registry/production_manifest.json
```

All artifact checksums must validate. If any fail, the restore is incomplete.

### Step 4: Restart the Backend

```powershell
# Kill existing uvicorn process, then:
.\.venv312\Scripts\python.exe -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

### Step 5: Verify Health

```powershell
curl http://127.0.0.1:8000/api/health
```

**Expected response must include:**
- `"manifest_backed": true`
- `"model_loaded": true`
- `"model_version"` matching the rollback target
- No missing or invalid artifacts

### Step 6: Smoke Test

Submit a test scoring request to verify end-to-end functionality:
```powershell
# Use the prime borrower fixture from tests/fixtures/ or the REST smoke test from docs/RELEASE_SMOKE_TESTS_AND_DEMO.md
```

### Step 7: Record the Rollback

- Update `docs/CURRENT_STATE.md` with the new active manifest version
- Note the rollback reason in a commit message
- If the rollback is permanent, update `docs/MODEL_REGISTRY.md` to mark the reverted version as "reverted" and the restored version as "active"

---

## Post-Rollback Decision Tree

```
Rollback successful?
├── YES → Monitor for 24h, then decide:
│   ├── Root-cause the original failure → fix → retrain → re-promote
│   └── Accept rollback as new baseline → update docs
└── NO (artifacts missing / checksum fail) →
    ├── Check if artifacts exist in git history
    ├── If not → must retrain from the target version's training script
    └── Retrain: .\.venv312\Scripts\python.exe scripts\training\train_calibrated_monotonic_xgboost.py --device cuda
```

---

## Environment Notes

- Python: 3.12.x (use `.venv312`)
- scikit-learn: >=1.5,<1.6 (pinned for artifact compatibility)
- XGBoost: >=2.1.3,<2.2
- Do NOT change sklearn version without retraining — deserialization will fail
