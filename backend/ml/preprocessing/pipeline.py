"""Preprocessing pipeline helpers for AlterScore offline training."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Final

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.decomposition import PCA
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OrdinalEncoder, StandardScaler

from backend.app.core.paths import MODEL_PREPROCESSORS_DIR
from backend.ml.data_generation.generator import TEMPORAL_SPLIT_MONTHS
from backend.ml.features.derived_features import DERIVED_FEATURES, add_derived_features
from backend.ml.nlp.extractor import RAW_EMBEDDING_DIM
from backend.ml.preprocessing.feature_registry import (
    ALL_MODEL_FEATURES,
    CATEGORICAL_FEATURES,
    NUMERIC_FEATURES,
    PROTECTED_FEATURES,
    TARGET,
    TEMPORAL_METADATA,
)

TEXT_PCA_FEATURES: Final[tuple[str, str]] = ("text_semantic_dim1", "text_semantic_dim2")
TEXT_PCA_COMPONENTS: Final[int] = 2
TEXT_PCA_RANDOM_STATE: Final[int] = 42
DEFAULT_PREPROCESSOR_ARTIFACT_PATH: Final[Path] = MODEL_PREPROCESSORS_DIR / "preprocessor.pkl"
DEFAULT_TEXT_PCA_ARTIFACT_PATH: Final[Path] = MODEL_PREPROCESSORS_DIR / "text_pca.pkl"
NON_DERIVED_MODEL_FEATURES: Final[list[str]] = [
    feature_name for feature_name in ALL_MODEL_FEATURES if feature_name not in DERIVED_FEATURES
]


@dataclass(frozen=True)
class TemporalDataSplit:
    X: pd.DataFrame
    y: pd.Series
    protected: pd.DataFrame
    indices: pd.Index
    cohort_months: pd.Series


@dataclass(frozen=True)
class PreparedTemporalData:
    train: TemporalDataSplit
    validation: TemporalDataSplit
    test: TemporalDataSplit
    text_pca: PCA | None


def build_preprocessor() -> ColumnTransformer:
    """Build the canonical sklearn preprocessing pipeline."""

    return ColumnTransformer(
        transformers=[
            (
                "num",
                Pipeline(
                    steps=[
                        ("imputer", SimpleImputer(strategy="median")),
                        ("scaler", StandardScaler()),
                    ]
                ),
                NUMERIC_FEATURES,
            ),
            (
                "cat",
                Pipeline(
                    steps=[
                        ("imputer", SimpleImputer(strategy="most_frequent")),
                        (
                            "encoder",
                            OrdinalEncoder(
                                handle_unknown="use_encoded_value",
                                unknown_value=-1,
                            ),
                        ),
                    ]
                ),
                CATEGORICAL_FEATURES,
            ),
        ],
        remainder="drop",
    )


def prepare_temporal_data(
    dataset: pd.DataFrame,
    raw_text_embeddings: np.ndarray | None = None,
    *,
    text_pca_components: int = TEXT_PCA_COMPONENTS,
    text_pca_random_state: int = TEXT_PCA_RANDOM_STATE,
    text_pca_artifact_path: str | Path | None = None,
) -> PreparedTemporalData:
    """Split a dataset by cohort month and inject train-fitted text PCA features."""

    _assert_required_dataset_columns(dataset)
    feature_source_columns = [column_name for column_name in dataset.columns if column_name in ALL_MODEL_FEATURES]
    feature_frame = prepare_model_feature_frame(dataset.loc[:, feature_source_columns].copy())
    _assert_feature_exclusions(feature_frame.columns)

    train_mask = dataset["cohort_month"].isin(TEMPORAL_SPLIT_MONTHS["train"])
    validation_mask = dataset["cohort_month"].isin(TEMPORAL_SPLIT_MONTHS["validation"])
    test_mask = dataset["cohort_month"].isin(TEMPORAL_SPLIT_MONTHS["test"])
    _assert_temporal_masks(dataset, train_mask, validation_mask, test_mask)

    text_pca: PCA | None = None
    if raw_text_embeddings is not None:
        _assert_embedding_shape(raw_text_embeddings=raw_text_embeddings, expected_rows=len(dataset))
        text_pca = fit_text_pca(
            raw_text_embeddings[train_mask.to_numpy()],
            n_components=text_pca_components,
            random_state=text_pca_random_state,
            artifact_path=text_pca_artifact_path,
        )
        feature_frame = apply_text_pca(feature_frame, raw_text_embeddings, text_pca)

    return PreparedTemporalData(
        train=_build_split(dataset, feature_frame, train_mask),
        validation=_build_split(dataset, feature_frame, validation_mask),
        test=_build_split(dataset, feature_frame, test_mask),
        text_pca=text_pca,
    )


def fit_text_pca(
    train_embeddings: np.ndarray,
    *,
    n_components: int = TEXT_PCA_COMPONENTS,
    random_state: int = TEXT_PCA_RANDOM_STATE,
    artifact_path: str | Path | None = None,
) -> PCA:
    """Fit text PCA on train-split embeddings only."""

    embeddings = np.asarray(train_embeddings, dtype=float)
    if embeddings.ndim != 2:
        raise ValueError("train_embeddings must be a 2D array.")
    if embeddings.shape[0] == 0:
        raise ValueError("train_embeddings must contain at least one row.")
    if embeddings.shape[1] < n_components:
        raise ValueError(
            f"train_embeddings must have at least {n_components} columns; found {embeddings.shape[1]}."
        )

    text_pca = PCA(n_components=n_components, random_state=random_state)
    text_pca.fit(embeddings)

    if artifact_path is not None:
        _save_artifact(text_pca, artifact_path)

    return text_pca


def apply_text_pca(
    feature_frame: pd.DataFrame,
    raw_text_embeddings: np.ndarray,
    text_pca: PCA,
) -> pd.DataFrame:
    """Project raw embeddings into the two canonical text semantic features."""

    embeddings = np.asarray(raw_text_embeddings, dtype=float)
    if embeddings.ndim != 2:
        raise ValueError("raw_text_embeddings must be a 2D array.")
    if len(feature_frame) != embeddings.shape[0]:
        raise ValueError(
            "raw_text_embeddings row count must match the feature frame row count."
        )

    projected_embeddings = text_pca.transform(embeddings)
    updated_feature_frame = feature_frame.copy()
    updated_feature_frame.loc[:, TEXT_PCA_FEATURES[0]] = projected_embeddings[:, 0]
    updated_feature_frame.loc[:, TEXT_PCA_FEATURES[1]] = projected_embeddings[:, 1]
    return updated_feature_frame


def fit_preprocessor(
    X_train: pd.DataFrame,
    *,
    artifact_path: str | Path | None = None,
) -> ColumnTransformer:
    """Fit the sklearn preprocessor on the train split."""

    preprocessor = build_preprocessor()
    preprocessor.fit(X_train)

    if artifact_path is not None:
        _save_artifact(preprocessor, artifact_path)

    return preprocessor


def prepare_model_feature_frame(feature_frame: pd.DataFrame) -> pd.DataFrame:
    """Ensure a feature frame contains all canonical model inputs in canonical order."""

    updated_feature_frame = feature_frame.copy()
    missing_derived_features = [
        feature_name for feature_name in DERIVED_FEATURES if feature_name not in updated_feature_frame.columns
    ]
    if missing_derived_features:
        updated_feature_frame = add_derived_features(updated_feature_frame)

    missing_columns = [
        feature_name for feature_name in ALL_MODEL_FEATURES if feature_name not in updated_feature_frame.columns
    ]
    if missing_columns:
        raise ValueError(f"Feature frame is missing required model features: {missing_columns}")

    return updated_feature_frame.loc[:, ALL_MODEL_FEATURES].copy()


def transform_features(
    preprocessor: ColumnTransformer,
    feature_frame: pd.DataFrame,
) -> np.ndarray:
    """Transform feature data with the fitted preprocessor."""

    transformed = preprocessor.transform(feature_frame)
    return np.asarray(transformed, dtype=float)


def _build_split(
    dataset: pd.DataFrame,
    feature_frame: pd.DataFrame,
    mask: pd.Series,
) -> TemporalDataSplit:
    split_dataset = dataset.loc[mask]
    split_features = feature_frame.loc[mask, ALL_MODEL_FEATURES].copy()

    return TemporalDataSplit(
        X=split_features,
        y=split_dataset[TARGET].copy(),
        protected=split_dataset.loc[:, PROTECTED_FEATURES].copy(),
        indices=split_dataset.index.copy(),
        cohort_months=split_dataset["cohort_month"].copy(),
    )


def _assert_required_dataset_columns(dataset: pd.DataFrame) -> None:
    required_columns = [*NON_DERIVED_MODEL_FEATURES, *PROTECTED_FEATURES, *TEMPORAL_METADATA, TARGET]
    missing_columns = [column for column in required_columns if column not in dataset.columns]
    if missing_columns:
        raise ValueError(f"Dataset is missing required columns: {missing_columns}")


def _assert_feature_exclusions(feature_columns: pd.Index) -> None:
    excluded_columns = set(PROTECTED_FEATURES) | set(TEMPORAL_METADATA) | {TARGET}
    overlap = sorted(set(feature_columns) & excluded_columns)
    if overlap:
        raise ValueError(f"Model feature frame contains excluded columns: {overlap}")


def _assert_temporal_masks(
    dataset: pd.DataFrame,
    train_mask: pd.Series,
    validation_mask: pd.Series,
    test_mask: pd.Series,
) -> None:
    if not train_mask.any() or not validation_mask.any() or not test_mask.any():
        raise ValueError("Temporal split must produce non-empty train, validation, and test splits.")

    month_series = dataset["cohort_month"]
    if month_series.loc[train_mask].max() > max(TEMPORAL_SPLIT_MONTHS["train"]):
        raise ValueError("Train split includes rows outside months 1-8.")
    if not month_series.loc[validation_mask].isin(TEMPORAL_SPLIT_MONTHS["validation"]).all():
        raise ValueError("Validation split includes rows outside months 9-10.")
    if month_series.loc[test_mask].min() < min(TEMPORAL_SPLIT_MONTHS["test"]):
        raise ValueError("Test split includes rows outside months 11-12.")

    combined_counts = (
        train_mask.astype(int) + validation_mask.astype(int) + test_mask.astype(int)
    )
    if not (combined_counts == 1).all():
        raise ValueError("Temporal split masks must be disjoint and cover the full dataset.")


def _assert_embedding_shape(
    raw_text_embeddings: np.ndarray,
    expected_rows: int,
) -> None:
    if raw_text_embeddings.ndim != 2:
        raise ValueError("raw_text_embeddings must be a 2D array.")
    if raw_text_embeddings.shape[0] != expected_rows:
        raise ValueError(
            "raw_text_embeddings row count must match the dataset row count."
        )
    if raw_text_embeddings.shape[1] != RAW_EMBEDDING_DIM:
        raise ValueError(
            f"raw_text_embeddings must have {RAW_EMBEDDING_DIM} columns; "
            f"found {raw_text_embeddings.shape[1]}."
        )


def _save_artifact(artifact: object, artifact_path: str | Path) -> None:
    path = Path(artifact_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(artifact, path)


__all__ = [
    "DEFAULT_PREPROCESSOR_ARTIFACT_PATH",
    "DEFAULT_TEXT_PCA_ARTIFACT_PATH",
    "PreparedTemporalData",
    "TEXT_PCA_COMPONENTS",
    "TEXT_PCA_FEATURES",
    "TEXT_PCA_RANDOM_STATE",
    "TemporalDataSplit",
    "apply_text_pca",
    "build_preprocessor",
    "fit_preprocessor",
    "fit_text_pca",
    "prepare_model_feature_frame",
    "prepare_temporal_data",
    "transform_features",
]
