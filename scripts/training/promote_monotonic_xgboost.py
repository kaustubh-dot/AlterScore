"""Backward-compatible entrypoint for monotonic XGBoost promotion.

The old implementation copied a prebuilt candidate from runtime/. Promotion is
now reproducible: this wrapper delegates to the calibrated monotonic trainer,
which rebuilds the model, reports, explainers, and manifest from source.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.training.train_calibrated_monotonic_xgboost import main

if __name__ == "__main__":
    raise SystemExit(main())
