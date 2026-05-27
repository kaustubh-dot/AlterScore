from __future__ import annotations

import shutil
import sys
import tempfile
from pathlib import Path
from typing import Iterator

from filelock import FileLock
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
TEST_TMP_ROOT = REPO_ROOT / "runtime" / "pytest-workspace"

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


@pytest.fixture(scope="session")
def session_trained_model_dir(tmp_path_factory, worker_id) -> Path:
    """Train the baseline model once per test session, shared across all xdist workers using a file lock."""
    # Find a shared base directory for all workers
    base_temp_dir = tmp_path_factory.getbasetemp().parent
    shared_dir = base_temp_dir / "shared_session_trained_model"
    lock_file = base_temp_dir / "session_trained_model.lock"

    with FileLock(str(lock_file)):
        model_root = shared_dir / "models"
        if not model_root.exists():
            model_root.mkdir(parents=True, exist_ok=True)
            from backend.ml.data_generation.generator import generate_synthetic_dataset
            from backend.ml.training.classical.baselines import train_baselines

            train_baselines(
                generate_synthetic_dataset(row_count=2_400, seed=37),
                expected_row_count=2_400,
                minimum_test_rows=300,
                preprocessor_artifact_path=model_root
                / "preprocessors"
                / "preprocessor.pkl",
                text_pca_artifact_path=model_root / "preprocessors" / "text_pca.pkl",
                logistic_artifact_path=model_root / "artifacts" / "logistic_best.pkl",
                baseline_metrics_path=model_root / "reports" / "baseline_metrics.json",
                metrics_path=model_root / "reports" / "metrics.json",
                population_percentiles_path=model_root
                / "reports"
                / "population_percentiles.json",
                fairness_report_path=model_root / "reports" / "fairness_report.json",
                psi_report_path=model_root / "reports" / "psi_report.json",
                global_importance_path=model_root
                / "reports"
                / "global_importance.json",
                dice_explainer_path=model_root / "explainers" / "dice_explainer.pkl",
            )

    return shared_dir


@pytest.fixture
def trained_model_dir(tmp_path, session_trained_model_dir) -> Path:
    """Provide a fresh function-scoped copy of the pre-trained model directory."""
    shutil.copytree(
        session_trained_model_dir / "models", tmp_path / "models", dirs_exist_ok=True
    )
    return tmp_path


@pytest.fixture
def tmp_path() -> Iterator[Path]:
    """Provide a workspace-local temp directory without relying on global temp paths."""

    TEST_TMP_ROOT.mkdir(parents=True, exist_ok=True)
    path = Path(tempfile.mkdtemp(prefix="pytest-", dir=TEST_TMP_ROOT))
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)
