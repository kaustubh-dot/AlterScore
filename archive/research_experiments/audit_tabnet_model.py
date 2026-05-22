"""Targeted TabNet audit for distribution, sensitivity, and calibration behavior."""

from __future__ import annotations

import copy
import json
import os
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, roc_auc_score

ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PATH = ROOT / "tests" / "fixtures" / "score_request_valid.json"
DATASET_PATH = ROOT / "data" / "raw" / "synthetic_dataset.csv"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.core.artifact_loader import load_runtime_artifact_bundle
from backend.ml.inference.feature_assembly import assemble_request_features
from backend.ml.preprocessing.pipeline import (
    align_text_features_from_raw_text,
    prepare_temporal_data,
    transform_features,
)


def main() -> None:
    os.environ.setdefault("HF_HUB_OFFLINE", "1")
    os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

    artifacts = load_runtime_artifact_bundle(strict=True)
    tabnet_model = artifacts.base_models["tabnet"]

    dataset = pd.read_csv(DATASET_PATH)
    subgroup_analysis = build_subgroup_analysis(dataset)

    aligned_dataset, raw_embeddings = align_text_features_from_raw_text(dataset)
    prepared = prepare_temporal_data(
        aligned_dataset,
        raw_text_embeddings=raw_embeddings,
        text_pca_artifact_path=None,
    )
    X_validation = transform_features(artifacts.preprocessor, prepared.validation.X)
    X_test = transform_features(artifacts.preprocessor, prepared.test.X)
    y_validation = prepared.validation.y.to_numpy(dtype=int)
    y_test = prepared.test.y.to_numpy(dtype=int)

    validation_raw_probabilities = tabnet_model.predict_proba(X_validation)[:, 1]
    test_raw_probabilities = tabnet_model.predict_proba(X_test)[:, 1]

    isotonic_calibrator = IsotonicRegression(out_of_bounds="clip")
    isotonic_calibrator.fit(validation_raw_probabilities, y_validation)
    validation_isotonic_probabilities = isotonic_calibrator.predict(validation_raw_probabilities)
    test_isotonic_probabilities = isotonic_calibrator.predict(test_raw_probabilities)

    platt_calibrator = LogisticRegression(max_iter=1000, solver="lbfgs")
    platt_calibrator.fit(validation_raw_probabilities.reshape(-1, 1), y_validation)
    validation_platt_probabilities = platt_calibrator.predict_proba(
        validation_raw_probabilities.reshape(-1, 1)
    )[:, 1]
    test_platt_probabilities = platt_calibrator.predict_proba(
        test_raw_probabilities.reshape(-1, 1)
    )[:, 1]

    monotonic_sensitivity = build_monotonic_sensitivity_analysis(
        artifacts=artifacts,
        tabnet_model=tabnet_model,
        isotonic_calibrator=isotonic_calibrator,
        platt_calibrator=platt_calibrator,
    )

    report = {
        "runtime_model_name": artifacts.report.runtime_model_name,
        "tabnet_distribution_audit": subgroup_analysis,
        "tabnet_calibration_audit": {
            "validation": {
                "raw_auc": float(roc_auc_score(y_validation, validation_raw_probabilities)),
                "raw_brier": float(brier_score_loss(y_validation, validation_raw_probabilities)),
                "isotonic_auc": float(roc_auc_score(y_validation, validation_isotonic_probabilities)),
                "isotonic_brier": float(
                    brier_score_loss(y_validation, validation_isotonic_probabilities)
                ),
                "platt_auc": float(roc_auc_score(y_validation, validation_platt_probabilities)),
                "platt_brier": float(brier_score_loss(y_validation, validation_platt_probabilities)),
            },
            "test": {
                "raw_auc": float(roc_auc_score(y_test, test_raw_probabilities)),
                "raw_brier": float(brier_score_loss(y_test, test_raw_probabilities)),
                "isotonic_auc": float(roc_auc_score(y_test, test_isotonic_probabilities)),
                "isotonic_brier": float(brier_score_loss(y_test, test_isotonic_probabilities)),
                "platt_auc": float(roc_auc_score(y_test, test_platt_probabilities)),
                "platt_brier": float(brier_score_loss(y_test, test_platt_probabilities)),
            },
        },
        "tabnet_monotonic_sensitivity": monotonic_sensitivity,
        "generator_risk_notes": [
            "Synthetic label generation still uses the historical engagement_score formula where scroll_hesitation_score increases engagement.",
            "Synthetic labels also include a direct positive repayment bonus for device_type == desktop.",
            "These correlations can be learned by TabNet even after inference-time fixes remove or neutralize them.",
        ],
    }
    print(json.dumps(report, indent=2))


def build_subgroup_analysis(dataset: pd.DataFrame) -> dict[str, Any]:
    subgroup_masks = {
        "strong_profiles": (
            (dataset["numeracy_score"] >= 0.8)
            & (dataset["future_orientation"] >= 0.8)
            & (dataset["resilience_score"] >= 0.8)
        ),
        "resilience_heavy": dataset["resilience_score"] >= 0.8,
        "numeracy_heavy": dataset["numeracy_score"] >= 0.8,
        "future_heavy": dataset["future_orientation"] >= 0.8,
    }

    subgroup_summaries = {}
    for subgroup_name, mask in subgroup_masks.items():
        subset = dataset.loc[mask]
        subgroup_summaries[subgroup_name] = {
            "count": int(mask.sum()),
            "repayment_rate": float(subset["repayment_label"].mean()) if len(subset) else None,
            "avg_scroll_hesitation_score": (
                float(subset["scroll_hesitation_score"].mean()) if len(subset) else None
            ),
            "avg_engagement_score": float(subset["engagement_score"].mean()) if len(subset) else None,
            "device_mix": {
                key: float(value)
                for key, value in subset["device_type"].value_counts(normalize=True).to_dict().items()
            }
            if len(subset)
            else {},
            "time_mix": {
                key: float(value)
                for key, value in subset["time_of_day"].value_counts(normalize=True).to_dict().items()
            }
            if len(subset)
            else {},
        }

    label_correlations = {
        "scroll_hesitation_score": float(dataset["scroll_hesitation_score"].corr(dataset["repayment_label"])),
        "engagement_score": float(dataset["engagement_score"].corr(dataset["repayment_label"])),
        "numeracy_score": float(dataset["numeracy_score"].corr(dataset["repayment_label"])),
        "future_orientation": float(dataset["future_orientation"].corr(dataset["repayment_label"])),
        "resilience_score": float(dataset["resilience_score"].corr(dataset["repayment_label"])),
        "device_type": {
            column_name: float(dummy_frame[column_name].corr(dataset["repayment_label"]))
            for dummy_frame in [pd.get_dummies(dataset["device_type"], prefix="device_type")]
            for column_name in dummy_frame.columns
        },
        "time_of_day": {
            column_name: float(dummy_frame[column_name].corr(dataset["repayment_label"]))
            for dummy_frame in [pd.get_dummies(dataset["time_of_day"], prefix="time_of_day")]
            for column_name in dummy_frame.columns
        },
    }

    return {
        "subgroups": subgroup_summaries,
        "label_correlations": label_correlations,
    }


def build_monotonic_sensitivity_analysis(
    *,
    artifacts: Any,
    tabnet_model: Any,
    isotonic_calibrator: IsotonicRegression,
    platt_calibrator: LogisticRegression,
) -> dict[str, Any]:
    anchor_payload = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    anchor_payload["answers"].update(
        {
            "numeracy_q1": 6600,
            "numeracy_q2": 1120,
            "numeracy_q3": 14400,
            "future_orient_q1": 1,
            "future_orient_q2": 1,
            "future_orient_q3": 5,
            "resilience_q1": 5,
            "resilience_q2": 5,
            "resilience_q3": 0,
            "q27_resilience_text": (
                "When sales fell, I reviewed every expense, negotiated supplier terms, "
                "found extra freelance work, and protected my repayment plan. "
                "I learned to act early, stay transparent, and keep a cash buffer "
                "for future shocks."
            ),
        }
    )
    assembled = assemble_request_features(
        anchor_payload,
        text_pca=artifacts.text_pca,
        require_text_pca=True,
    )
    anchor_feature_frame = assembled.feature_frame.copy()

    def sweep_feature(feature_name: str, values: np.ndarray) -> list[dict[str, float]]:
        sweep_rows: list[dict[str, float]] = []
        for value in values:
            feature_frame = anchor_feature_frame.copy()
            feature_frame.loc[:, feature_name] = float(value)
            processed_features = transform_features(artifacts.preprocessor, feature_frame)
            raw_probability = float(tabnet_model.predict_proba(processed_features)[:, 1][0])
            sweep_rows.append(
                {
                    "value": float(value),
                    "raw_tabnet_probability": raw_probability,
                    "isotonic_probability": float(isotonic_calibrator.predict([raw_probability])[0]),
                    "platt_probability": float(
                        platt_calibrator.predict_proba([[raw_probability]])[:, 1][0]
                    ),
                }
            )
        return sweep_rows

    feature_grid = np.linspace(0.0, 1.0, 11)
    return {
        "anchor_profile_summary": {
            "numeracy_score": float(anchor_feature_frame.iloc[0]["numeracy_score"]),
            "future_orientation": float(anchor_feature_frame.iloc[0]["future_orientation"]),
            "resilience_score": float(anchor_feature_frame.iloc[0]["resilience_score"]),
            "text_agency_score": float(anchor_feature_frame.iloc[0]["text_agency_score"]),
            "scroll_hesitation_score": float(anchor_feature_frame.iloc[0]["scroll_hesitation_score"]),
        },
        "feature_sweeps": {
            "numeracy_score": sweep_feature("numeracy_score", feature_grid),
            "future_orientation": sweep_feature("future_orientation", feature_grid),
            "resilience_score": sweep_feature("resilience_score", feature_grid),
            "text_agency_score": sweep_feature("text_agency_score", feature_grid),
            "scroll_hesitation_score": sweep_feature("scroll_hesitation_score", feature_grid),
        },
    }


if __name__ == "__main__":
    main()
