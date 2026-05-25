# Backend Dependency Audit

## Scope Reviewed

This audit covered the backend dependency surface in the repository root and backend code:

- `backend/requirements.txt`
- `README.md`
- `docs/DEPLOYMENT.md`
- backend/runtime/training imports under `backend/`
- tests under `tests/`
- Python entrypoints under `scripts/`

Files that were explicitly requested but are **not present** in this repository:

- `pyproject.toml`
- `poetry.lock`
- `Pipfile`
- `setup.py`
- CI/CD workflow files such as `.github/workflows/*.yml`
- shell startup scripts such as `.sh` or `.ps1`

## Executive Summary

The original backend manifest was not portable as-is.

The most important issues were:

1. `dice-ml==0.11` conflicts with `pandas==2.2.3`, so a fresh `pip install -r backend/requirements.txt` fails on Python 3.12 before the app can start.
2. The machine default Python in this workspace is `3.14.3`, and the original exact pins forced `numpy`, `pandas`, and `scipy` into source-build paths there. `scipy==1.14.1` then failed on Windows because no Fortran compiler was installed.
3. The checked-in runtime bundle loads PyTorch, TabNet, XGBoost, and LightGBM artifacts at startup, but `torch` was not declared directly even though the runtime genuinely imports and uses it.
4. Test-only packages (`pytest`, `httpx`) were mixed into the main runtime requirements.
5. Unused packages (`optuna`, `imbalanced-learn`, `dice-ml`) increased resolver pressure and installation risk without helping backend startup or the checked-in tests.

## Concrete Failures Reproduced

### Fresh install on Python 3.14.3

Observed behavior:

- `numpy==2.2.1`, `pandas==2.2.3`, and `scipy==1.14.1` did not resolve to wheels in the fresh audit venv.
- `pip` attempted source builds.
- `scipy==1.14.1` failed during metadata generation because no Fortran compiler was installed on Windows.

Observed error pattern:

- native build via Meson
- missing `gfortran` / `ifort` / `ifx`

Portability impact:

- new developer setup fails on a modern Python install even before application imports
- Windows is hit first, but Linux/macOS would also require native toolchains if wheels are unavailable

### Fresh install on Python 3.12.7

Observed behavior:

- wheel resolution succeeded for the scientific stack
- installation still failed because of an explicit dependency conflict

Observed resolver conflict:

- `pandas==2.2.3`
- `dice-ml==0.11` requires `pandas<2.0.0`

Portability impact:

- even on the better interpreter family, the original manifest could not be installed cleanly

## Current Dependency Risk Review

### Exact pins (`==`)

The original manifest hard-pinned nearly every dependency:

- `fastapi==0.115.6`
- `uvicorn[standard]==0.34.0`
- `pydantic==2.10.4`
- `numpy==2.2.1`
- `pandas==2.2.3`
- `scipy==1.14.1`
- `joblib==1.4.2`
- `vaderSentiment==3.3.2`
- `spacy==3.8.3`
- `sentence-transformers==3.3.1`
- `xgboost==2.1.3`
- `lightgbm==4.6.0`
- `optuna==4.1.0`
- `imbalanced-learn==0.13.0`
- `shap==0.46.0`
- `dice-ml==0.11`
- `pytorch-tabnet==4.1.0`
- `pytest==8.3.4`
- `httpx==0.28.1`

Why this was risky:

- exact pins increase breakage when a different Python version needs newer wheels
- exact pins make dependency resolution more fragile around transitive constraints
- exact pins in a plain requirements file do not provide true lockfile reproducibility anyway

### Unused or unnecessary packages

The following packages were in the original requirements file but are not imported by backend code, tests, or Python entrypoints:

- `optuna`
- `imbalanced-learn`
- `dice-ml`

Risk:

- larger download and install surface
- more transitive conflicts
- harder cross-platform setup

Recommendation:

- remove them from the default backend environment

### Missing direct dependency

`torch` was not declared directly, but the runtime and tests import it:

- `backend/ml/inference/ensemble_adapter.py`
- `backend/ml/training/neural/train_mlp.py`
- `tests/unit/ml/test_ensemble_adapter.py`

Why this matters:

- relying on `pytorch-tabnet` to pull PyTorch transitively is brittle
- CPU/GPU wheel selection is often the hardest part of PyTorch installation
- explicit declaration makes the install contract honest

## Package-Specific Findings

### `numpy`

Current risk:

- `numpy==2.2.1` is wheel-friendly on Python 3.12, but not on the local Python 3.14 install used for this audit
- when wheel resolution fails, native compilation becomes likely

Potential errors:

- source build attempts
- compiler/toolchain failures
- binary ABI mismatch with compiled scientific packages

Recommendation:

- keep within the tested `2.2.x` family using `numpy>=2.2,<2.3`

### `pandas`

Current risk:

- exact pin plus `dice-ml==0.11` caused a hard resolver failure
- major pandas changes can affect ML preprocessing code and downstream dependencies

Potential errors:

- `ResolutionImpossible`
- API changes if jumped too far forward

Recommendation:

- keep within the tested `2.2.x` family using `pandas>=2.2,<2.3`

### `scipy`

Current risk:

- exact `scipy==1.14.1` failed to install from source on Windows/Python 3.14 because Fortran was missing
- SciPy is one of the highest-risk packages for source builds

Potential errors:

- Meson/native build failures
- missing Fortran compiler
- long compile times even when the toolchain exists

Recommendation:

- keep `scipy>=1.14.1,<1.15`
- recommend Python 3.12 so wheels are used

### `scikit-learn`

Current risk:

- the code imports `sklearn.frozen.FrozenEstimator` in `backend/ml/training/ensemble/train_stacking.py`
- persisted sklearn artifacts are usually safest when loaded with the same major/minor family used during training

Potential errors:

- import errors on older sklearn
- pickle/joblib artifact incompatibilities across distant sklearn versions

Recommendation:

- keep a strict minor-family range: `scikit-learn>=1.8,<1.9`

### `torch`

Current risk:

- required for the checked-in runtime ensemble because the MLP artifact is a PyTorch checkpoint
- large wheel downloads
- optional CUDA variants can confuse setup if chosen accidentally

Potential errors:

- `ImportError: torch is required...`
- wrong CUDA/CPU wheel selection
- long install times

Recommendation:

- declare it directly as `torch>=2.12,<2.13`
- document that CPU wheels are the default and recommended path for local setup

### `pytorch-tabnet`

Current risk:

- upstream release is old relative to the rest of the stack
- PyPI metadata advertises older Python classifiers even though it may still work on newer versions

Potential errors:

- future compatibility drift with new PyTorch or Python releases
- runtime artifact load failures if the package API changes unexpectedly

Recommendation:

- keep `pytorch-tabnet>=4.1,<4.2`
- prefer Python 3.12 rather than 3.13/3.14 for local development

### `xgboost`

Current risk:

- binary-heavy dependency
- platform wheel availability matters

Potential errors:

- import failures if wheel/platform support is missing
- longer install times on slower networks

Recommendation:

- keep `xgboost>=2.1.3,<2.2`

### `lightgbm`

Current risk:

- binary dependency with OpenMP/runtime caveats
- Linux imports can fail if `libgomp` is missing

Potential errors:

- `OSError` on Linux when OpenMP runtime is missing
- wheel/platform-specific issues

Recommendation:

- keep `lightgbm>=4.6,<4.7`
- document Linux OpenMP troubleshooting

### `fastapi` / `uvicorn` / `pydantic`

Current risk:

- not individually problematic today, but exact pins were unnecessarily strict for a plain requirements file
- FastAPI and Pydantic must remain in the same compatibility generation

Recommendation:

- `fastapi>=0.115.6,<0.116`
- `uvicorn[standard]>=0.34,<0.35`
- `pydantic>=2.10.4,<2.11`

### `shap`

Current risk:

- compiled extension dependency
- can be sensitive to NumPy/scikit-learn changes

Recommendation:

- keep within the current minor family: `shap>=0.46,<0.47`

### `spacy` / `sentence-transformers` / `vaderSentiment`

Current risk:

- `spacy` and `sentence-transformers` are comparatively heavy
- `sentence-transformers` may trigger model downloads
- `spacy` features are best when the `en_core_web_sm` model is installed

Important code behavior:

- the backend gracefully falls back when these extras are unavailable:
  - hashed embeddings when sentence-transformers/model download is unavailable
  - rule-based agency extraction when spaCy or the English model is unavailable
  - rule-based sentiment when VADER is unavailable

Recommendation:

- keep them in the default environment for behavior parity with the intended scoring path
- document that missing model downloads degrade behavior but do not block startup

### `psycopg2`, `cryptography`, `tensorflow`, `opencv`

Result:

- not present in the backend dependency graph for this repository

## Python Version Compatibility

### Code syntax floor

The codebase uses Python 3.10+ syntax extensively:

- `X | Y` union syntax
- `list[str]`, `dict[str, Any]`
- `from __future__ import annotations`

Minimum code-level Python:

- Python `3.10`

### Practical project version

The practical project target is narrower than the syntax floor:

- Python `3.14.3` failed during fresh installation because the pinned scientific stack dropped to source builds
- Python `3.12.7` resolved wheels cleanly, aside from the `dice-ml` conflict
- the training/runtime stack depends on older-but-still-common ML packages, especially `pytorch-tabnet`

Recommended project Python:

- **Python 3.12**

Why 3.12:

- strong wheel availability for the current scientific/ML stack
- newer than the language floor, but not so new that binary-package support becomes patchy
- better fit for PyTorch, SciPy, XGBoost, LightGBM, SHAP, and scikit-learn together

## Refactor Applied

### `backend/requirements.txt`

Changes made:

- replaced exact pins with conservative compatible ranges
- removed unused and conflicting packages:
  - `optuna`
  - `imbalanced-learn`
  - `dice-ml`
- added explicit direct `torch` dependency
- removed test-only dependencies from the runtime manifest

### `backend/requirements-dev.txt`

Added:

- runtime requirements via `-r requirements.txt`
- `pytest`
- `httpx`

### `.python-version`

Added:

- `3.12.7`

## Risk Notes For Range Changes

The new ranges are intentionally conservative.

Remaining risk:

- allowing a newer patch or nearby minor inside each family can still surface behavior differences compared with the exact versions originally used
- the biggest compatibility-sensitive package remains `scikit-learn`, which is why its range stays narrow at `>=1.8,<1.9`
- `torch` and `pytorch-tabnet` remain a long-term maintenance risk if the project later moves to Python 3.13/3.14

Why the changes are still justified:

- the original manifest already failed to install cleanly
- the new ranges preserve the same library families while restoring installability and separating runtime from test tooling

## Verification Status

### Verified directly in this audit

- fresh install with original requirements failed on Python `3.14.3`
- fresh install with original requirements failed on Python `3.12.7`
- root causes were reproduced and captured

### Verified after manifest refactor

Verified in a fresh Python `3.12.7` virtual environment:

- `pip install -r backend/requirements.txt` completed successfully after the manifest refactor
- `pip install -r backend/requirements-dev.txt` completed successfully
- import smoke test succeeded for:
  - FastAPI / Uvicorn / Pydantic
  - NumPy / pandas / SciPy / scikit-learn / joblib
  - VADER / spaCy / sentence-transformers
  - XGBoost / LightGBM / SHAP / PyTorch / pytorch-tabnet
- `from backend.app.main import create_app` succeeded
- `tests/integration/api/test_checked_in_runtime_bundle_smoke.py` passed: `6/6`
- full repository test run passed `140/150`

The remaining `10` failures were **not** dependency-resolution failures. They were local filesystem write-permission errors while training-path tests attempted to overwrite checked-in files under `models/reports/`:

- `models/reports/baseline_metrics.json`
- `models/reports/fairness_report.json`
- `models/reports/psi_report.json`

Interpretation:

- the dependency refactor restored environment installability and backend startup/test viability
- there is still a separate repository-local writeability issue affecting some training tests on this machine
