"""Residual MLP neural training loop for AlterScore temporal splits.

Artifact format: ``.pt`` checkpoint via ``torch.save`` containing:
  - ``model_name``: string identifier
  - ``config``: architecture dict (n_features, hidden_dim, n_hidden_layers, dropout)
  - ``state_dict``: CPU-mapped model weights

Save/load contract::

  _save_mlp_checkpoint(model, config, path)   -> writes <path>.pt
  load_mlp_model(path)                        -> ResidualMLP in eval() on CPU

Architecture — ResidualMLP:
  Input -> Linear -> BatchNorm -> ReLU -> Dropout  (+skip projection)
  Hidden blocks (residual)
  Output -> Sigmoid
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
from backend.ml.data_generation.validators import MINIMUM_TEST_ROWS, validate_synthetic_dataset
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
# Constants
# ---------------------------------------------------------------------------

DEFAULT_DATASET_PATH: Final[Path] = RAW_DATA_DIR / "synthetic_dataset.csv"
DEFAULT_MLP_ARTIFACT_PATH: Final[Path] = MODEL_ARTIFACTS_DIR / "mlp_best.pt"
MLP_MODEL_TYPE: Final[str] = "neural"
MLP_MODEL_NAME: Final[str] = "residual_mlp"

_MLP_HIDDEN_DIM: Final[int] = 128
_MLP_N_HIDDEN_LAYERS: Final[int] = 2
_MLP_DROPOUT: Final[float] = 0.3
_MLP_LEARNING_RATE: Final[float] = 1e-3
_MLP_WEIGHT_DECAY: Final[float] = 1e-4
_MLP_MAX_EPOCHS: Final[int] = 50
_MLP_PATIENCE: Final[int] = 10
_MLP_BATCH_SIZE: Final[int] = 512

NUMERIC_METRIC_FIELDS: Final[tuple[str, ...]] = (
    "auc_roc", "auc_pr", "ks_statistic", "brier_score",
    "expected_calibration_error", "accuracy", "precision", "recall", "f1", "threshold",
)


# ---------------------------------------------------------------------------
# Public result container
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class MLPTrainingArtifacts:
    run_id: str
    dataset_path: Path | None
    preprocessor_path: Path | None
    text_pca_path: Path | None
    mlp_artifact_path: Path | None
    metrics_path: Path | None
    population_percentiles_path: Path | None
    model_stats: list[dict[str, Any]]
    validation_probabilities: np.ndarray
    test_probabilities: np.ndarray


# ---------------------------------------------------------------------------
# Primary entry point
# ---------------------------------------------------------------------------


def train_mlp(
    dataset: pd.DataFrame | None = None,
    *,
    dataset_path: str | Path | None = None,
    expected_row_count: int | None = None,
    minimum_test_rows: int = MINIMUM_TEST_ROWS,
    preprocessor_artifact_path: str | Path | None = DEFAULT_PREPROCESSOR_ARTIFACT_PATH,
    text_pca_artifact_path: str | Path | None = DEFAULT_TEXT_PCA_ARTIFACT_PATH,
    mlp_artifact_path: str | Path | None = DEFAULT_MLP_ARTIFACT_PATH,
    metrics_path: str | Path | None = DEFAULT_METRICS_PATH,
    population_percentiles_path: str | Path | None = DEFAULT_POPULATION_PERCENTILES_PATH,
    random_state: int = DEFAULT_RANDOM_STATE,
) -> MLPTrainingArtifacts:
    """Train a residual MLP on the documented temporal split.

    Strictly reuses existing preprocessing, temporal-split, evaluation, and
    metrics infrastructure. Artifact is a ``.pt`` checkpoint loadable via
    ``load_mlp_model``.

    Raises:
        RuntimeError: If torch is not installed.
        FileNotFoundError: If the dataset CSV is absent.
        ValueError: If probability arrays contain NaN or out-of-range values.
    """
    _assert_torch_available()
    import torch

    # Determinism
    np.random.seed(random_state)
    _set_torch_seed(random_state)

    # Data loading and preprocessing
    resolved_dataset, resolved_dataset_path = _load_dataset(dataset, dataset_path)
    aligned_dataset, raw_text_embeddings = align_text_features_from_raw_text(resolved_dataset)
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
    preprocessor = fit_preprocessor(prepared.train.X, artifact_path=preprocessor_artifact_path)
    X_full_processed = transform_features(preprocessor, prepared.feature_frame)
    X_train_processed = transform_features(preprocessor, prepared.train.X)
    X_val_processed = transform_features(preprocessor, prepared.validation.X)
    X_test_processed = transform_features(preprocessor, prepared.test.X)
    y_train = prepared.train.y.to_numpy(dtype=int)
    y_val = prepared.validation.y.to_numpy(dtype=int)
    y_test = prepared.test.y.to_numpy(dtype=int)

    # Build and train
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    n_features = X_train_processed.shape[1]
    mlp_config = {
        "n_features": n_features,
        "hidden_dim": _MLP_HIDDEN_DIM,
        "n_hidden_layers": _MLP_N_HIDDEN_LAYERS,
        "dropout": _MLP_DROPOUT,
    }
    model = _build_mlp_model(mlp_config, device=device)
    model = _fit_mlp(
        model,
        X_train=X_train_processed,
        y_train=y_train,
        X_val=X_val_processed,
        y_val=y_val,
        device=device,
        random_state=random_state,
    )
    model.eval()

    # Persist artifact
    resolved_mlp_path = _optional_path(mlp_artifact_path)
    if resolved_mlp_path is not None:
        _save_mlp_checkpoint(model, mlp_config, resolved_mlp_path)

    # Inference
    val_probs = _predict_positive_class_probabilities(
        MLP_MODEL_NAME, _infer_proba(model, X_val_processed, device)
    )
    test_probs = _predict_positive_class_probabilities(
        MLP_MODEL_NAME, _infer_proba(model, X_test_processed, device)
    )
    full_probs = _predict_positive_class_probabilities(
        MLP_MODEL_NAME, _infer_proba(model, X_full_processed, device)
    )
    val_threshold = optimal_threshold(y_val, val_probs)

    # Metrics
    model_stats = [
        compute_binary_classification_metrics(
            y_val, val_probs,
            model_name=MLP_MODEL_NAME, model_type=MLP_MODEL_TYPE,
            split="validation_months_9_10", threshold=val_threshold,
        ),
        compute_binary_classification_metrics(
            y_test, test_probs,
            model_name=MLP_MODEL_NAME, model_type=MLP_MODEL_TYPE,
            split="test_months_11_12", threshold=val_threshold,
        ),
    ]
    evaluation_details: dict[str, dict[str, Any]] = {
        "validation_months_9_10": {
            MLP_MODEL_NAME: build_split_evaluation_details(
                y_val, val_probs,
                model_name=MLP_MODEL_NAME, model_type=MLP_MODEL_TYPE,
                split="validation_months_9_10", threshold=val_threshold,
            )
        },
        "test_months_11_12": {
            MLP_MODEL_NAME: build_split_evaluation_details(
                y_test, test_probs,
                model_name=MLP_MODEL_NAME, model_type=MLP_MODEL_TYPE,
                split="test_months_11_12", threshold=val_threshold,
            )
        },
    }
    population_payload = build_population_percentiles_payload(full_probs, model_name=MLP_MODEL_NAME)
    run_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_mlp")
    split_row_counts = {"train": int(len(y_train)), "validation": int(len(y_val)), "test": int(len(y_test))}

    # Merge metrics.json
    merged_model_stats: list[dict[str, Any]] = model_stats
    if metrics_path is not None:
        existing_payload = _load_existing_metrics_payload(metrics_path)
        merged_model_stats = _merge_model_stats(
            existing_model_stats=existing_payload.get("model_stats", []),
            updated_model_stats=model_stats,
        )
        metrics_out: dict[str, Any] = {
            **{k: v for k, v in existing_payload.items()
               if k not in {"run_id", "split_row_counts", "model_stats", "evaluation_details"}},
            "run_id": run_id,
            "split_row_counts": split_row_counts,
            "model_stats": merged_model_stats,
            "baselines": existing_payload.get("baselines", []),
            "evaluation_details": merge_evaluation_details(
                existing_payload.get("evaluation_details"), evaluation_details
            ),
        }
        _save_json(metrics_out, metrics_path)

    # Merge population_percentiles.json
    if population_percentiles_path is not None:
        existing_pop = _load_existing_population_payload(population_percentiles_path)
        default_name = _resolve_population_default_model_name(
            model_stats=merged_model_stats,
            existing_payload=existing_pop,
            updated_model_payloads={MLP_MODEL_NAME: population_payload},
        )
        _save_json(
            merge_population_percentiles_reports(
                existing_pop, {MLP_MODEL_NAME: population_payload}, default_model_name=default_name
            ),
            population_percentiles_path,
        )

    return MLPTrainingArtifacts(
        run_id=run_id,
        dataset_path=resolved_dataset_path,
        preprocessor_path=_optional_path(preprocessor_artifact_path),
        text_pca_path=_optional_path(text_pca_artifact_path),
        mlp_artifact_path=resolved_mlp_path,
        metrics_path=_optional_path(metrics_path),
        population_percentiles_path=_optional_path(population_percentiles_path),
        model_stats=model_stats,
        validation_probabilities=val_probs,
        test_probabilities=test_probs,
    )


# ---------------------------------------------------------------------------
# ResidualMLP definition
# ---------------------------------------------------------------------------


def _build_mlp_model(config: dict[str, Any], *, device: Any) -> Any:
    import torch.nn as nn

    class ResidualMLP(nn.Module):
        def __init__(self, n_features: int, hidden_dim: int, n_hidden_layers: int, dropout: float) -> None:
            super().__init__()
            self.input_proj = nn.Sequential(
                nn.Linear(n_features, hidden_dim), nn.BatchNorm1d(hidden_dim), nn.ReLU(), nn.Dropout(dropout),
            )
            self.skip = nn.Linear(n_features, hidden_dim) if n_features != hidden_dim else nn.Identity()
            self.hidden_blocks = nn.ModuleList([
                nn.Sequential(
                    nn.Linear(hidden_dim, hidden_dim), nn.BatchNorm1d(hidden_dim), nn.ReLU(), nn.Dropout(dropout),
                )
                for _ in range(max(0, n_hidden_layers - 1))
            ])
            self.output = nn.Linear(hidden_dim, 1)

        def forward(self, x: Any) -> Any:
            import torch
            h = self.input_proj(x) + self.skip(x)
            for block in self.hidden_blocks:
                h = block(h) + h
            return torch.sigmoid(self.output(h)).squeeze(1)

    return ResidualMLP(
        n_features=config["n_features"],
        hidden_dim=config["hidden_dim"],
        n_hidden_layers=config["n_hidden_layers"],
        dropout=config["dropout"],
    ).to(device)


def _fit_mlp(
    model: Any,
    *,
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_val: np.ndarray,
    y_val: np.ndarray,
    device: Any,
    random_state: int,
) -> Any:
    import torch
    import torch.nn.functional as F
    from sklearn.metrics import roc_auc_score

    _set_torch_seed(random_state)
    X_tr = torch.tensor(X_train, dtype=torch.float32).to(device)
    y_tr = torch.tensor(y_train, dtype=torch.float32).to(device)
    X_v = torch.tensor(X_val, dtype=torch.float32).to(device)

    n_pos = float(y_train.sum())
    n_neg = float(len(y_train) - n_pos)
    pos_weight_val = (n_neg / n_pos) if n_pos > 0 else 1.0
    pos_w = torch.tensor([pos_weight_val], dtype=torch.float32).to(device)

    optimizer = torch.optim.Adam(model.parameters(), lr=_MLP_LEARNING_RATE, weight_decay=_MLP_WEIGHT_DECAY)

    best_auc = -1.0
    best_state: dict[str, Any] = {}
    patience_ctr = 0
    n = len(X_tr)

    for _ in range(_MLP_MAX_EPOCHS):
        model.train()
        perm = torch.randperm(n)
        for start in range(0, n, _MLP_BATCH_SIZE):
            idx = perm[start: start + _MLP_BATCH_SIZE]
            xb, yb = X_tr[idx], y_tr[idx]
            optimizer.zero_grad()
            preds = model(xb)
            w = torch.where(yb == 1, pos_w.expand_as(yb), torch.ones_like(yb))
            loss = (w * F.binary_cross_entropy(preds, yb, reduction="none")).mean()
            loss.backward()
            optimizer.step()

        model.eval()
        with torch.no_grad():
            vp = model(X_v).cpu().numpy()
        try:
            val_auc = float(roc_auc_score(y_val, vp))
        except ValueError:
            val_auc = 0.5

        if val_auc > best_auc:
            best_auc = val_auc
            best_state = {k: v.cpu().clone() for k, v in model.state_dict().items()}
            patience_ctr = 0
        else:
            patience_ctr += 1
            if patience_ctr >= _MLP_PATIENCE:
                break

    if best_state:
        model.load_state_dict({k: v.to(device) for k, v in best_state.items()})
    return model


# ---------------------------------------------------------------------------
# Artifact I/O
# ---------------------------------------------------------------------------


def _save_mlp_checkpoint(model: Any, config: dict[str, Any], artifact_path: Path) -> None:
    import torch
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(
        {"model_name": MLP_MODEL_NAME, "config": config,
         "state_dict": {k: v.cpu() for k, v in model.state_dict().items()}},
        str(artifact_path),
    )


def load_mlp_model(artifact_path: str | Path) -> Any:
    """Load a ResidualMLP from a ``.pt`` checkpoint in eval mode on CPU.

    Raises:
        RuntimeError: If torch is not installed.
        FileNotFoundError: If the artifact is absent.
    """
    _assert_torch_available()
    import torch

    resolved = Path(artifact_path)
    if not resolved.is_file():
        raise FileNotFoundError(
            f"MLP artifact not found at {resolved}. Run the MLP training job first."
        )
    ckpt = torch.load(str(resolved), map_location="cpu", weights_only=False)
    model = _build_mlp_model(ckpt["config"], device=torch.device("cpu"))
    model.load_state_dict(ckpt["state_dict"])
    model.eval()
    return model


def _infer_proba(model: Any, X: np.ndarray, device: Any) -> np.ndarray:
    import torch
    model.eval()
    with torch.no_grad():
        return model(torch.tensor(X, dtype=torch.float32).to(device)).cpu().numpy().astype(float)


# ---------------------------------------------------------------------------
# Shared private helpers
# ---------------------------------------------------------------------------


def _assert_torch_available() -> None:
    try:
        import torch  # noqa: F401
    except ImportError as exc:
        raise RuntimeError(
            "torch is required for the AlterScore residual MLP model. "
            "Install it with: pip install torch"
        ) from exc


def _set_torch_seed(seed: int) -> None:
    try:
        import torch
        torch.manual_seed(seed)
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
    except ImportError:
        pass


def _predict_positive_class_probabilities(model_name: str, probabilities: np.ndarray | list[float]) -> np.ndarray:
    arr = np.asarray(probabilities, dtype=float)
    if np.isnan(arr).any():
        raise ValueError(f"{model_name} produced NaN predicted probabilities.")
    if ((arr < 0.0) | (arr > 1.0)).any():
        raise ValueError(f"{model_name} produced probabilities outside [0, 1].")
    return arr


def _load_dataset(dataset: pd.DataFrame | None, dataset_path: str | Path | None) -> tuple[pd.DataFrame, Path | None]:
    if dataset is not None:
        return dataset.copy(), None
    resolved = Path(dataset_path or DEFAULT_DATASET_PATH)
    if not resolved.is_file():
        raise FileNotFoundError(
            f"Dataset not found at {resolved}. Run the synthetic dataset materialization command first."
        )
    return pd.read_csv(resolved), resolved


def _optional_path(path: str | Path | None) -> Path | None:
    return None if path is None else Path(path)


def _load_existing_metrics_payload(metrics_path: str | Path | None) -> dict[str, Any]:
    if metrics_path is None:
        return {}
    p = Path(metrics_path)
    if not p.is_file():
        return {}
    payload = json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("metrics.json payload must be a JSON object.")
    return payload


def _load_existing_population_payload(path: str | Path | None) -> dict[str, Any] | None:
    if path is None:
        return None
    p = Path(path)
    if not p.is_file():
        return None
    payload = json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("population_percentiles.json payload must be a JSON object.")
    return payload


def _merge_model_stats(
    *, existing_model_stats: list[dict[str, Any]], updated_model_stats: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    lookup = {(item["model_name"], item["split"]): item for item in updated_model_stats}
    merged: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for item in existing_model_stats:
        key = (str(item.get("model_name")), str(item.get("split")))
        rep = lookup.get(key)
        if rep is not None:
            merged.append(rep)
            seen.add(key)
        else:
            merged.append(item)
    for item in updated_model_stats:
        key = (item["model_name"], item["split"])
        if key not in seen:
            merged.append(item)
            seen.add(key)
    return merged


def _resolve_population_default_model_name(
    *, model_stats: list[dict[str, Any]], existing_payload: dict[str, Any] | None,
    updated_model_payloads: dict[str, dict[str, Any]],
) -> str:
    available = set(updated_model_payloads)
    if isinstance(existing_payload, dict):
        existing_models = existing_payload.get("models")
        if isinstance(existing_models, dict):
            available.update(n for n, p in existing_models.items() if isinstance(n, str) and isinstance(p, dict))
    selected = select_best_test_auc_model(model_stats, candidate_model_names=available)
    if selected is not None:
        return selected
    existing_default = None if existing_payload is None else existing_payload.get("default_model_name")
    if isinstance(existing_default, str) and existing_default in available:
        return existing_default
    if available:
        return sorted(available)[0]
    raise ValueError("At least one population percentile model payload is required.")


def _save_json(payload: Any, path: str | Path) -> None:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")


__all__ = [
    "DEFAULT_DATASET_PATH", "DEFAULT_MLP_ARTIFACT_PATH",
    "MLP_MODEL_NAME", "MLP_MODEL_TYPE", "NUMERIC_METRIC_FIELDS",
    "MLPTrainingArtifacts", "load_mlp_model", "train_mlp",
]
