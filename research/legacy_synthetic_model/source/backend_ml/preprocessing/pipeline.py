"""Preprocessing pipeline helpers for AlterScore offline training."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final

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
from backend.ml.nlp.extractor import (
    RAW_EMBEDDING_DIM,
    RAW_TEXT_RESPONSE_COLUMN,
    extract_raw_text_embedding,
    extract_nlp_feature_batch,
)
from backend.ml.preprocessing.feature_registry import (
    ALL_MODEL_FEATURES,
    CATEGORICAL_FEATURES,
    NUMERIC_FEATURES,
    PROTECTED_FEATURES,
    TARGET,
    TEMPORAL_METADATA,
)

TEXT_PCA_FEATURES: Final[tuple[str, str]] = ("text_semantic_dim1", "text_semantic_dim2")
TEXT_INTERPRETABLE_FEATURES: Final[tuple[str, ...]] = (
    "text_sentiment_compound",
    "text_agency_score",
    "text_problem_solving_flag",
)
TEXT_PCA_COMPONENTS: Final[int] = 2
TEXT_PCA_RANDOM_STATE: Final[int] = 42
DEFAULT_PREPROCESSOR_ARTIFACT_PATH: Final[Path] = (
    MODEL_PREPROCESSORS_DIR / "preprocessor.pkl"
)
DEFAULT_TEXT_PCA_ARTIFACT_PATH: Final[Path] = MODEL_PREPROCESSORS_DIR / "text_pca.pkl"
TEXT_SOURCE_COLUMN: Final[str] = RAW_TEXT_RESPONSE_COLUMN
SYNTHETIC_TEXT_SOURCE_COLUMNS: Final[tuple[str, ...]] = (
    "text_sentiment_compound",
    "text_agency_score",
    "text_problem_solving_flag",
    "future_orientation",
    "resilience_score",
    "social_capital_score",
    "conscientiousness_score",
    "honesty_score",
)
NON_DERIVED_MODEL_FEATURES: Final[list[str]] = [
    feature_name
    for feature_name in ALL_MODEL_FEATURES
    if feature_name not in DERIVED_FEATURES
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
    feature_frame: pd.DataFrame
    text_pca: PCA | None


def build_preprocessor() -> ColumnTransformer:
    """Build the canonical sklearn preprocessing pipeline."""

    transformers: list[tuple[str, Pipeline, list[str]]] = [
        (
            "num",
            Pipeline(
                steps=[
                    ("imputer", SimpleImputer(strategy="median")),
                    ("scaler", StandardScaler()),
                ]
            ),
            NUMERIC_FEATURES,
        )
    ]
    if CATEGORICAL_FEATURES:
        transformers.append(
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
            )
        )
    return ColumnTransformer(
        transformers=transformers,
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
    feature_source_columns = [
        column_name
        for column_name in dataset.columns
        if column_name in ALL_MODEL_FEATURES
    ]
    feature_frame = prepare_model_feature_frame(
        dataset.loc[:, feature_source_columns].copy()
    )
    _assert_feature_exclusions(feature_frame.columns)

    train_mask = dataset["cohort_month"].isin(TEMPORAL_SPLIT_MONTHS["train"])
    validation_mask = dataset["cohort_month"].isin(TEMPORAL_SPLIT_MONTHS["validation"])
    test_mask = dataset["cohort_month"].isin(TEMPORAL_SPLIT_MONTHS["test"])
    _assert_temporal_masks(dataset, train_mask, validation_mask, test_mask)

    text_pca: PCA | None = None
    if raw_text_embeddings is not None:
        _assert_embedding_shape(
            raw_text_embeddings=raw_text_embeddings, expected_rows=len(dataset)
        )
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
        feature_frame=feature_frame.copy(),
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


def build_text_embedding_matrix(
    dataset: pd.DataFrame,
    *,
    text_column: str = TEXT_SOURCE_COLUMN,
) -> np.ndarray:
    """Build runtime-compatible raw text embeddings from dataset text or deterministic surrogates."""

    if dataset.empty:
        return np.zeros((0, RAW_EMBEDDING_DIM), dtype=float)

    texts = _resolve_text_corpus(dataset, text_column=text_column)
    embeddings = [extract_raw_text_embedding(text) for text in texts]
    return np.vstack(embeddings).astype(float, copy=False)


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


def align_text_features_from_raw_text(
    dataset: pd.DataFrame,
    *,
    text_column: str = TEXT_SOURCE_COLUMN,
) -> tuple[pd.DataFrame, np.ndarray]:
    """Overwrite text-derived model features from the raw resilience response text."""

    text_values = _resolve_text_corpus(dataset, text_column=text_column)
    nlp_feature_rows, raw_embeddings = extract_nlp_feature_batch(text_values)
    updated_dataset = dataset.copy()
    for feature_name in TEXT_INTERPRETABLE_FEATURES:
        if feature_name not in updated_dataset.columns:
            updated_dataset.loc[:, feature_name] = 0.0
    updated_dataset = updated_dataset.astype(
        {feature_name: float for feature_name in TEXT_INTERPRETABLE_FEATURES},
        copy=False,
    )

    for feature_name in TEXT_INTERPRETABLE_FEATURES:
        updated_dataset.loc[:, feature_name] = np.asarray(
            [feature_row[feature_name] for feature_row in nlp_feature_rows],
            dtype=float,
        )

    return updated_dataset, raw_embeddings


def prepare_model_feature_frame(feature_frame: pd.DataFrame) -> pd.DataFrame:
    """Ensure a feature frame contains all canonical model inputs in canonical order."""

    updated_feature_frame = feature_frame.copy()
    missing_derived_features = [
        feature_name
        for feature_name in DERIVED_FEATURES
        if feature_name not in updated_feature_frame.columns
    ]
    if missing_derived_features:
        updated_feature_frame = add_derived_features(updated_feature_frame)

    missing_columns = [
        feature_name
        for feature_name in ALL_MODEL_FEATURES
        if feature_name not in updated_feature_frame.columns
    ]
    if missing_columns:
        raise ValueError(
            f"Feature frame is missing required model features: {missing_columns}"
        )

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
    required_columns = [
        *NON_DERIVED_MODEL_FEATURES,
        *PROTECTED_FEATURES,
        *TEMPORAL_METADATA,
        TARGET,
    ]
    missing_columns = [
        column for column in required_columns if column not in dataset.columns
    ]
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
        raise ValueError(
            "Temporal split must produce non-empty train, validation, and test splits."
        )

    month_series = dataset["cohort_month"]
    if month_series.loc[train_mask].max() > max(TEMPORAL_SPLIT_MONTHS["train"]):
        raise ValueError("Train split includes rows outside months 1-8.")
    if (
        not month_series.loc[validation_mask]
        .isin(TEMPORAL_SPLIT_MONTHS["validation"])
        .all()
    ):
        raise ValueError("Validation split includes rows outside months 9-10.")
    if month_series.loc[test_mask].min() < min(TEMPORAL_SPLIT_MONTHS["test"]):
        raise ValueError("Test split includes rows outside months 11-12.")

    combined_counts = (
        train_mask.astype(int) + validation_mask.astype(int) + test_mask.astype(int)
    )
    if not (combined_counts == 1).all():
        raise ValueError(
            "Temporal split masks must be disjoint and cover the full dataset."
        )


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


def _resolve_text_corpus(
    dataset: pd.DataFrame,
    *,
    text_column: str,
) -> list[str]:
    if text_column in dataset.columns:
        return dataset[text_column].fillna("").astype(str).tolist()

    missing_columns = [
        column_name
        for column_name in SYNTHETIC_TEXT_SOURCE_COLUMNS
        if column_name not in dataset.columns
    ]
    if missing_columns:
        raise ValueError(
            "Dataset is missing the text source needed to build raw embeddings: "
            f"{missing_columns}"
        )

    surrogate_rows = dataset.loc[:, list(SYNTHETIC_TEXT_SOURCE_COLUMNS)]
    return [
        _build_synthetic_resilience_text(row)
        for row in surrogate_rows.itertuples(index=False, name="SyntheticTextRow")
    ]


def _build_synthetic_resilience_text(row: Any) -> str:
    sentiment_clause = (
        "I stayed optimistic and calm while dealing with the setback."
        if float(row.text_sentiment_compound) >= 0.25
        else (
            "I stayed cautious but steady while dealing with the setback."
            if float(row.text_sentiment_compound) >= -0.15
            else "I felt stressed and uncertain while dealing with the setback."
        )
    )
    agency_clause = (
        "I took action early and handled the problem myself."
        if float(row.text_agency_score) >= 0.65
        else (
            "I tried to respond and make decisions as the situation changed."
            if float(row.text_agency_score) >= 0.40
            else "I felt stuck for a while before reacting."
        )
    )
    problem_solving_clause = (
        "I reduced expenses, adjusted my budget, and looked for extra work."
        if float(row.text_problem_solving_flag) >= 0.5
        else "I struggled to find a clear solution at first."
    )
    planning_clause = (
        "I kept a long-term repayment plan in mind."
        if float(row.future_orientation) >= 0.60
        else "I focused more on immediate needs than a long-term plan."
    )
    resilience_clause = (
        "I kept going after setbacks and recovered step by step."
        if float(row.resilience_score) >= 0.60
        else "It took time for me to recover after setbacks."
    )
    support_clause = (
        "I leaned on community support when needed."
        if float(row.social_capital_score) >= 0.55
        else "I handled most of the pressure on my own."
    )
    discipline_clause = (
        "I followed a careful budget and tried to stay organized."
        if float(row.conscientiousness_score) >= 0.60
        else "I tried to stay organized even when the plan was hard to follow."
    )
    honesty_clause = (
        "I wanted to repay what I owed and be transparent about the situation."
        if float(row.honesty_score) >= 0.60
        else "I knew repayment would be difficult and I was not fully confident."
    )

    return " ".join(
        [
            agency_clause,
            sentiment_clause,
            problem_solving_clause,
            planning_clause,
            resilience_clause,
            support_clause,
            discipline_clause,
            honesty_clause,
        ]
    )


def _save_artifact(artifact: object, artifact_path: str | Path) -> None:
    path = Path(artifact_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(artifact, path)


__all__ = [
    "DEFAULT_PREPROCESSOR_ARTIFACT_PATH",
    "DEFAULT_TEXT_PCA_ARTIFACT_PATH",
    "PreparedTemporalData",
    "RAW_TEXT_RESPONSE_COLUMN",
    "TEXT_PCA_COMPONENTS",
    "TEXT_PCA_FEATURES",
    "TEXT_INTERPRETABLE_FEATURES",
    "TEXT_PCA_RANDOM_STATE",
    "TEXT_SOURCE_COLUMN",
    "TemporalDataSplit",
    "align_text_features_from_raw_text",
    "apply_text_pca",
    "build_preprocessor",
    "build_text_embedding_matrix",
    "fit_preprocessor",
    "fit_text_pca",
    "prepare_model_feature_frame",
    "prepare_temporal_data",
    "transform_features",
]
