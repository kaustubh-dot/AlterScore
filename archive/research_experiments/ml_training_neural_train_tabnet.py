"""TabNet neural training loop for AlterScore temporal splits.

TabNet artifacts are saved/loaded as .zip archives by pytorch-tabnet.
The save/load contract mirrors the classical joblib pattern but uses
TabNetClassifier's native ``save_model`` / ``load_model`` interface:

  - ``save_model(str_path_without_extension)``   → writes ``<path>.zip``
  - ``load_model(str_path_with_extension)``       → loads from ``<path>.zip``

Both halves of the contract are exercised in the integration smoke test.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Final

import numpy as np
import pandas as pd

from backend.app.core.paths import MODEL_ARTIFACTS_DIR, RAW_DATA_DIR
from backend.ml.data_generation.validators import (
    MINIMUM_TEST_ROWS,
    validate_synthetic_dataset,
)
from backend.ml.evaluation.metrics import (
    build_population_percentiles_payload,
    build_split_evaluation_details,
    compute_binary_classification_metrics,
    merge_evaluation_details,
    merge_population_percentiles_reports,
    optimal_threshold,
    select_best_test_auc_model,
)
from backend.ml.preprocessing.pipeline import (
    DEFAULT_PREPROCESSOR_ARTIFACT_PATH,
    DEFAULT_TEXT_PCA_ARTIFACT_PATH,
    align_text_features_from_raw_text,
    fit_preprocessor,
    prepare_temporal_data,
    transform_features,
)
from backend.ml.training.classical.baselines import (
    DEFAULT_METRICS_PATH,
    DEFAULT_POPULATION_PERCENTILES_PATH,
    DEFAULT_RANDOM_STATE,
)

# ---------------------------------------------------------------------------
# Module-level constants
# ---------------------------------------------------------------------------

DEFAULT_DATASET_PATH: Final[Path] = RAW_DATA_DIR / "synthetic_dataset.csv"
DEFAULT_TABNET_ARTIFACT_PATH: Final[Path] = (
    MODEL_ARTIFACTS_DIR / "tabnet_epoch_best.zip"
)
TABNET_MODEL_TYPE: Final[str] = "neural"
TABNET_MODEL_NAME: Final[str] = "tabnet"

# TabNet hyper-parameters tuned for the 35-feature AlterScore dataset.
# These are intentionally conservative to keep smoke-test runtime manageable
# while still producing meaningful probability estimates.
_TABNET_N_D: Final[int] = 16
_TABNET_N_A: Final[int] = 16
_TABNET_N_STEPS: Final[int] = 3
_TABNET_GAMMA: Final[float] = 1.3
_TABNET_N_INDEPENDENT: Final[int] = 2
_TABNET_N_SHARED: Final[int] = 2
_TABNET_MOMENTUM: Final[float] = 0.02
_TABNET_EPSILON: Final[float] = 1e-15
_TABNET_MAX_EPOCHS: Final[int] = 50
_TABNET_PATIENCE: Final[int] = 10
_TABNET_BATCH_SIZE: Final[int] = 1024
_TABNET_VIRTUAL_BATCH_SIZE: Final[int] = 256
_TABNET_MASK_TYPE: Final[str] = "sparsemax"

NUMERIC_METRIC_FIELDS: Final[tuple[str, ...]] = (
    "auc_roc",
    "auc_pr",
    "ks_statistic",
    "brier_score",
    "expected_calibration_error",
    "accuracy",
    "precision",
    "recall",
    "f1",
    "threshold",
)


# ---------------------------------------------------------------------------
# Public result container
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class TabNetTrainingArtifacts:
    run_id: str
    dataset_path: Path | None
    preprocessor_path: Path | None
    text_pca_path: Path | None
    tabnet_artifact_path: Path | None
    metrics_path: Path | None
    population_percentiles_path: Path | None
    model_stats: list[dict[str, Any]]
    validation_probabilities: np.ndarray
    test_probabilities: np.ndarray


# ---------------------------------------------------------------------------
# Primary entry point
# ---------------------------------------------------------------------------


def train_tabnet(
    dataset: pd.DataFrame | None = None,
    *,
    dataset_path: str | Path | None = None,
    expected_row_count: int | None = None,
    minimum_test_rows: int = MINIMUM_TEST_ROWS,
    preprocessor_artifact_path: str | Path | None = DEFAULT_PREPROCESSOR_ARTIFACT_PATH,
    text_pca_artifact_path: str | Path | None = DEFAULT_TEXT_PCA_ARTIFACT_PATH,
    tabnet_artifact_path: str | Path | None = DEFAULT_TABNET_ARTIFACT_PATH,
    metrics_path: str | Path | None = DEFAULT_METRICS_PATH,
    population_percentiles_path: (
        str | Path | None
    ) = DEFAULT_POPULATION_PERCENTILES_PATH,
    random_state: int = DEFAULT_RANDOM_STATE,
    max_epochs: int = _TABNET_MAX_EPOCHS,
    patience: int = _TABNET_PATIENCE,
) -> TabNetTrainingArtifacts:
    """Train a TabNet classifier on the documented temporal split.

    Reuses the existing preprocessing, text-PCA, temporal-split, evaluation,
    and metrics infrastructure without modification. The TabNet artifact is
    persisted as a ``.zip`` file using the library's native save/load
    interface to preserve all internal architecture metadata required for
    inference-time reconstruction.

    Args:
        dataset: An already-loaded DataFrame. When provided, ``dataset_path``
            is ignored and no file is written for the dataset.
        dataset_path: Path to the synthetic dataset CSV. Falls back to the
            repository default when ``None``.
        expected_row_count: Optional exact row-count guard passed to the
            dataset validator.
        minimum_test_rows: Minimum acceptable test-split row count.
        preprocessor_artifact_path: Where to save/reuse the sklearn preprocessor.
        text_pca_artifact_path: Where to save/reuse the text PCA artifact.
        tabnet_artifact_path: Destination ``.zip`` path for the trained model.
            Pass ``None`` to skip artifact persistence (useful for smoke tests).
        metrics_path: Destination for the merged ``metrics.json`` payload.
        population_percentiles_path: Destination for the merged
            ``population_percentiles.json`` payload.
        random_state: Master seed for numpy and TabNet internal PRNG.

    Returns:
        A :class:`TabNetTrainingArtifacts` dataclass with paths and in-memory
        probability arrays for downstream stacking use.

    Raises:
        RuntimeError: If ``pytorch-tabnet`` is not installed.
        FileNotFoundError: If the dataset is not found on disk.
        ValueError: If probability arrays contain NaN or out-of-range values.
    """
    _assert_tabnet_available()

    # ------------------------------------------------------------------
    # Determinism
    # ------------------------------------------------------------------
    np.random.seed(random_state)
    _set_pytorch_seed(random_state)

    # ------------------------------------------------------------------
    # Data loading and preprocessing (fully reused infrastructure)
    # ------------------------------------------------------------------
    resolved_dataset, resolved_dataset_path = _load_dataset(dataset, dataset_path)
    aligned_dataset, raw_text_embeddings = align_text_features_from_raw_text(
        resolved_dataset
    )
    validate_synthetic_dataset(
        aligned_dataset,
        expected_row_count=(
            len(aligned_dataset) if expected_row_count is None else expected_row_count
        ),
        minimum_test_rows=minimum_test_rows,
    )

    prepared = prepare_temporal_data(
        aligned_dataset,
        raw_text_embeddings=raw_text_embeddings,
        text_pca_random_state=random_state,
        text_pca_artifact_path=text_pca_artifact_path,
    )
    preprocessor = fit_preprocessor(
        prepared.train.X,
        artifact_path=preprocessor_artifact_path,
    )
    X_full_processed = transform_features(preprocessor, prepared.feature_frame)
    X_train_processed = transform_features(preprocessor, prepared.train.X)
    X_validation_processed = transform_features(preprocessor, prepared.validation.X)
    X_test_processed = transform_features(preprocessor, prepared.test.X)
    y_train = prepared.train.y.to_numpy(dtype=int)
    y_validation = prepared.validation.y.to_numpy(dtype=int)
    y_test = prepared.test.y.to_numpy(dtype=int)

    # ------------------------------------------------------------------
    # TabNet training
    # ------------------------------------------------------------------
    model = _build_tabnet_model(random_state=random_state)
    model.fit(
        X_train=X_train_processed,
        y_train=y_train,
        eval_set=[(X_validation_processed, y_validation)],
        eval_name=["validation"],
        eval_metric=["auc"],
        max_epochs=max_epochs,
        patience=patience,
        batch_size=_TABNET_BATCH_SIZE,
        virtual_batch_size=_TABNET_VIRTUAL_BATCH_SIZE,
        num_workers=0,
        drop_last=False,
    )

    # ------------------------------------------------------------------
    # Artifact persistence (zip format required by pytorch-tabnet)
    # ------------------------------------------------------------------
    resolved_tabnet_path = _optional_path(tabnet_artifact_path)
    if resolved_tabnet_path is not None:
        _save_tabnet_model(model, resolved_tabnet_path)

    # ------------------------------------------------------------------
    # Probability inference
    # ------------------------------------------------------------------
    validation_probs = _predict_positive_class_probabilities(
        TABNET_MODEL_NAME,
        model.predict_proba(X_validation_processed)[:, 1],
    )
    test_probs = _predict_positive_class_probabilities(
        TABNET_MODEL_NAME,
        model.predict_proba(X_test_processed)[:, 1],
    )
    validation_threshold = optimal_threshold(y_validation, validation_probs)

    # ------------------------------------------------------------------
    # Metrics and evaluation details
    # ------------------------------------------------------------------
    model_stats = [
        compute_binary_classification_metrics(
            y_validation,
            validation_probs,
            model_name=TABNET_MODEL_NAME,
            model_type=TABNET_MODEL_TYPE,
            split="validation_months_9_10",
            threshold=validation_threshold,
        ),
        compute_binary_classification_metrics(
            y_test,
            test_probs,
            model_name=TABNET_MODEL_NAME,
            model_type=TABNET_MODEL_TYPE,
            split="test_months_11_12",
            threshold=validation_threshold,
        ),
    ]
    evaluation_details: dict[str, dict[str, Any]] = {
        "validation_months_9_10": {
            TABNET_MODEL_NAME: build_split_evaluation_details(
                y_validation,
                validation_probs,
                model_name=TABNET_MODEL_NAME,
                model_type=TABNET_MODEL_TYPE,
                split="validation_months_9_10",
                threshold=validation_threshold,
            )
        },
        "test_months_11_12": {
            TABNET_MODEL_NAME: build_split_evaluation_details(
                y_test,
                test_probs,
                model_name=TABNET_MODEL_NAME,
                model_type=TABNET_MODEL_TYPE,
                split="test_months_11_12",
                threshold=validation_threshold,
            )
        },
    }
    population_payload = build_population_percentiles_payload(
        _predict_positive_class_probabilities(
            TABNET_MODEL_NAME,
            model.predict_proba(X_full_processed)[:, 1],
        ),
        model_name=TABNET_MODEL_NAME,
    )

    run_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_tabnet")
    split_row_counts = {
        "train": int(len(y_train)),
        "validation": int(len(y_validation)),
        "test": int(len(y_test)),
    }

    # ------------------------------------------------------------------
    # Merge and persist metrics.json
    # ------------------------------------------------------------------
    if metrics_path is not None:
        existing_payload = _load_existing_metrics_payload(metrics_path)
        existing_model_stats: list[dict[str, Any]] = existing_payload.get(
            "model_stats", []
        )
        merged_model_stats = _merge_model_stats(
            existing_model_stats=existing_model_stats,
            updated_model_stats=model_stats,
        )
        baselines = existing_payload.get("baselines", [])
        metrics_payload: dict[str, Any] = {
            **{
                key: value
                for key, value in existing_payload.items()
                if key
                not in {
                    "run_id",
                    "split_row_counts",
                    "model_stats",
                    "evaluation_details",
                }
            },
            "run_id": run_id,
            "split_row_counts": split_row_counts,
            "model_stats": merged_model_stats,
            "baselines": baselines,
            "evaluation_details": merge_evaluation_details(
                existing_payload.get("evaluation_details"),
                evaluation_details,
            ),
        }
        _save_json(metrics_payload, metrics_path)

    # ------------------------------------------------------------------
    # Merge and persist population_percentiles.json
    # ------------------------------------------------------------------
    if population_percentiles_path is not None:
        existing_population_payload = _load_existing_population_payload(
            population_percentiles_path
        )
        existing_merged_model_stats_for_percentile = (
            merged_model_stats
            if metrics_path is not None
            else _merge_model_stats(
                existing_model_stats=_load_existing_metrics_payload(metrics_path).get(
                    "model_stats", []
                ),
                updated_model_stats=model_stats,
            )
        )
        default_model_name = _resolve_population_default_model_name(
            model_stats=existing_merged_model_stats_for_percentile,
            existing_payload=existing_population_payload,
            updated_model_payloads={TABNET_MODEL_NAME: population_payload},
        )
        merged_population_payload = merge_population_percentiles_reports(
            existing_population_payload,
            {TABNET_MODEL_NAME: population_payload},
            default_model_name=default_model_name,
        )
        _save_json(merged_population_payload, population_percentiles_path)

    return TabNetTrainingArtifacts(
        run_id=run_id,
        dataset_path=resolved_dataset_path,
        preprocessor_path=_optional_path(preprocessor_artifact_path),
        text_pca_path=_optional_path(text_pca_artifact_path),
        tabnet_artifact_path=resolved_tabnet_path,
        metrics_path=_optional_path(metrics_path),
        population_percentiles_path=_optional_path(population_percentiles_path),
        model_stats=model_stats,
        validation_probabilities=validation_probs,
        test_probabilities=test_probs,
    )


# ---------------------------------------------------------------------------
# TabNet model construction and save/load helpers
# ---------------------------------------------------------------------------


def _build_tabnet_model(*, random_state: int) -> Any:
    """Construct a TabNetClassifier with deterministic AlterScore defaults."""
    from pytorch_tabnet.tab_model import TabNetClassifier  # type: ignore[import]

    return TabNetClassifier(
        n_d=_TABNET_N_D,
        n_a=_TABNET_N_A,
        n_steps=_TABNET_N_STEPS,
        gamma=_TABNET_GAMMA,
        n_independent=_TABNET_N_INDEPENDENT,
        n_shared=_TABNET_N_SHARED,
        momentum=_TABNET_MOMENTUM,
        epsilon=_TABNET_EPSILON,
        mask_type=_TABNET_MASK_TYPE,
        seed=random_state,
        verbose=0,
    )


def _save_tabnet_model(model: Any, artifact_path: Path) -> None:
    """Persist a trained TabNetClassifier as a ``.zip`` archive.

    ``pytorch-tabnet``'s ``save_model`` accepts a path *without* the
    ``.zip`` extension and appends it automatically. We strip any trailing
    ``.zip`` from the caller's path to avoid double-extension artifacts.
    """
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    # Strip .zip if already present to avoid double-extension from the library
    stem_path = str(artifact_path)
    if stem_path.endswith(".zip"):
        stem_path = stem_path[:-4]
    model.save_model(stem_path)


def load_tabnet_model(artifact_path: str | Path) -> Any:
    """Load a saved TabNetClassifier from a ``.zip`` archive.

    This function is the inference-time counterpart of ``_save_tabnet_model``.
    It preserves train/inference parity by using the same ``load_model``
    interface used by the library for round-trip compatibility.

    Args:
        artifact_path: Path to the ``.zip`` archive produced by a previous
            ``train_tabnet`` call.

    Returns:
        A ``TabNetClassifier`` instance ready for ``predict_proba``.

    Raises:
        RuntimeError: If ``pytorch-tabnet`` is not installed.
        FileNotFoundError: If the artifact does not exist on disk.
    """
    _assert_tabnet_available()
    from pytorch_tabnet.tab_model import TabNetClassifier  # type: ignore[import]

    resolved_path = Path(artifact_path)
    if not resolved_path.is_file():
        raise FileNotFoundError(
            f"TabNet artifact not found at {resolved_path}. "
            "Run the TabNet training job first."
        )
    model = TabNetClassifier()
    # load_model requires the path *with* the .zip extension
    model.load_model(str(resolved_path))
    return model


# ---------------------------------------------------------------------------
# Private helpers — all mirrored from train_classical.py for consistency
# ---------------------------------------------------------------------------


def _assert_tabnet_available() -> None:
    """Raise a clear RuntimeError if pytorch-tabnet is not installed."""
    try:
        import pytorch_tabnet  # noqa: F401  # type: ignore[import]
    except ImportError as exc:  # pragma: no cover - dependency guard
        raise RuntimeError(
            "pytorch-tabnet is required to train the AlterScore TabNet model. "
            "Install it with: pip install pytorch-tabnet"
        ) from exc


def _set_pytorch_seed(seed: int) -> None:
    """Set PyTorch and CUDA seeds for reproducibility when torch is available."""
    try:
        import torch  # type: ignore[import]

        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
    except ImportError:  # pragma: no cover - torch may not be installed in test env
        pass


def _predict_positive_class_probabilities(
    model_name: str,
    probabilities: np.ndarray | list[float],
) -> np.ndarray:
    probability_array = np.asarray(probabilities, dtype=float)
    if np.isnan(probability_array).any():
        raise ValueError(f"{model_name} produced NaN predicted probabilities.")
    if ((probability_array < 0.0) | (probability_array > 1.0)).any():
        raise ValueError(
            f"{model_name} produced probabilities outside the documented [0, 1] range."
        )
    return probability_array


def _load_dataset(
    dataset: pd.DataFrame | None,
    dataset_path: str | Path | None,
) -> tuple[pd.DataFrame, Path | None]:
    if dataset is not None:
        return dataset.copy(), None

    resolved_dataset_path = Path(dataset_path or DEFAULT_DATASET_PATH)
    if not resolved_dataset_path.is_file():
        raise FileNotFoundError(
            f"Dataset not found at {resolved_dataset_path}. "
            "Run the synthetic dataset materialization command first."
        )
    return pd.read_csv(resolved_dataset_path), resolved_dataset_path


def _optional_path(path: str | Path | None) -> Path | None:
    return None if path is None else Path(path)


def _load_existing_metrics_payload(
    metrics_path: str | Path | None,
) -> dict[str, Any]:
    if metrics_path is None:
        return {}

    resolved_metrics_path = Path(metrics_path)
    if not resolved_metrics_path.is_file():
        return {}

    payload = json.loads(resolved_metrics_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("metrics.json payload must be a JSON object.")
    return payload


def _load_existing_population_payload(
    population_percentiles_path: str | Path | None,
) -> dict[str, Any] | None:
    if population_percentiles_path is None:
        return None

    resolved_path = Path(population_percentiles_path)
    if not resolved_path.is_file():
        return None

    payload = json.loads(resolved_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("population_percentiles.json payload must be a JSON object.")
    return payload


def _merge_model_stats(
    *,
    existing_model_stats: list[dict[str, Any]],
    updated_model_stats: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    updated_lookup = {
        (item["model_name"], item["split"]): item for item in updated_model_stats
    }
    merged_model_stats: list[dict[str, Any]] = []
    seen_keys: set[tuple[str, str]] = set()

    for item in existing_model_stats:
        key = (str(item.get("model_name")), str(item.get("split")))
        replacement = updated_lookup.get(key)
        if replacement is not None:
            merged_model_stats.append(replacement)
            seen_keys.add(key)
            continue
        merged_model_stats.append(item)

    for item in updated_model_stats:
        key = (item["model_name"], item["split"])
        if key in seen_keys:
            continue
        merged_model_stats.append(item)
        seen_keys.add(key)

    return merged_model_stats


def _resolve_population_default_model_name(
    *,
    model_stats: list[dict[str, Any]],
    existing_payload: dict[str, Any] | None,
    updated_model_payloads: dict[str, dict[str, Any]],
) -> str:
    available_model_names = set(updated_model_payloads)
    if isinstance(existing_payload, dict):
        existing_models = existing_payload.get("models")
        if isinstance(existing_models, dict):
            available_model_names.update(
                model_name
                for model_name, payload in existing_models.items()
                if isinstance(model_name, str) and isinstance(payload, dict)
            )

    selected_model_name = select_best_test_auc_model(
        model_stats,
        candidate_model_names=available_model_names,
    )
    if selected_model_name is not None:
        return selected_model_name

    existing_default = (
        None if existing_payload is None else existing_payload.get("default_model_name")
    )
    if isinstance(existing_default, str) and existing_default in available_model_names:
        return existing_default

    if available_model_names:
        return sorted(available_model_names)[0]

    raise ValueError("At least one population percentile model payload is required.")


def _save_json(payload: Any, path: str | Path) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


__all__ = [
    "DEFAULT_DATASET_PATH",
    "DEFAULT_TABNET_ARTIFACT_PATH",
    "NUMERIC_METRIC_FIELDS",
    "TABNET_MODEL_NAME",
    "TABNET_MODEL_TYPE",
    "TabNetTrainingArtifacts",
    "load_tabnet_model",
    "train_tabnet",
]
