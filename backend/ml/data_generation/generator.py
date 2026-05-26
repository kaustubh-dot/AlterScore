"""Deterministic synthetic data generation for the AlterScore pipeline."""

from __future__ import annotations

from typing import Final

import numpy as np
import pandas as pd

from backend.ml.nlp.extractor import RAW_TEXT_RESPONSE_COLUMN
from backend.ml.preprocessing.feature_registry import (
    ALL_MODEL_FEATURES,
    PROTECTED_FEATURES,
    TARGET,
    TEMPORAL_METADATA,
)

DEFAULT_ROW_COUNT: Final[int] = 10_000
DEFAULT_SEED: Final[int] = 42
DEFAULT_COHORT_YEAR: Final[int] = 2025

TEMPORAL_SPLIT_MONTHS: Final[dict[str, tuple[int, ...]]] = {
    "train": tuple(range(1, 9)),
    "validation": (9, 10),
    "test": (11, 12),
}

_MONTH_DISTRIBUTION_WEIGHTS: Final[np.ndarray] = np.array(
    [0.085, 0.085, 0.085, 0.085, 0.085, 0.085, 0.085, 0.085, 0.07, 0.07, 0.09, 0.09],
    dtype=float,
)
_MONTH_LENGTHS: Final[np.ndarray] = np.array(
    [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31],
    dtype=int,
)
_POSITIVE_RESILIENCE_OPENERS: Final[tuple[str, ...]] = (
    "When income fell, I stayed calm and made a plan.",
    "I felt pressure, but I decided to act early and stay in control.",
    "I was confident I could recover, so I started working on a better plan.",
)
_NEGATIVE_RESILIENCE_OPENERS: Final[tuple[str, ...]] = (
    "Things fell apart and bad things kept happening.",
    "I felt stuck and worse after the loss.",
    "The crisis felt overwhelming and I was unable to think clearly at first.",
)
_HIGH_AGENCY_ACTIONS: Final[tuple[str, ...]] = (
    "I budgeted strictly, found extra work, and saved what I could.",
    "I managed my expenses, negotiated payments, and worked to rebuild income.",
    "I reduced spending, planned repayments, and handled the problem directly.",
)
_MODERATE_AGENCY_ACTIONS: Final[tuple[str, ...]] = (
    "I asked for help, learned what to change, and started improving the situation.",
    "I made some changes, found support, and tried to recover step by step.",
    "I chose a smaller plan, worked steadily, and looked for better options.",
)
_LOW_AGENCY_ACTIONS: Final[tuple[str, ...]] = (
    "I had no choice and felt nothing I did would help.",
    "I gave up for a while because I felt unable to do anything.",
    "I felt forced to wait and stayed stuck instead of acting.",
)
_PROBLEM_SOLVING_CLOSERS: Final[tuple[str, ...]] = (
    "That plan helped me improve and feel more stable.",
    "The steps gave me relief and a better path forward.",
    "Working through it helped me recover and build confidence.",
)
_NEUTRAL_CLOSERS: Final[tuple[str, ...]] = (
    "I kept going and looked for a practical next step.",
    "I tried to stay steady while the situation changed.",
    "I focused on the next thing I could do.",
)
_NEGATIVE_CLOSERS: Final[tuple[str, ...]] = (
    "I still felt stuck and afraid things would get worse.",
    "The problem felt unresolved and I lost confidence.",
    "It was hard to recover and I felt unable to improve much.",
)


def generate_synthetic_dataset(
    row_count: int = DEFAULT_ROW_COUNT,
    seed: int = DEFAULT_SEED,
) -> pd.DataFrame:
    """Generate a deterministic in-memory synthetic dataset."""

    if row_count <= 0:
        raise ValueError("row_count must be a positive integer.")

    rng = np.random.default_rng(seed)
    cohort_month = _build_cohort_months(row_count)
    month_offset = cohort_month.astype(float) - 1.0

    capacity = rng.normal(0.0, 1.0, row_count)
    discipline = 0.38 * capacity + rng.normal(0.0, 0.92, row_count)
    stability = 0.24 * discipline + rng.normal(0.0, 0.97, row_count)
    integrity = 0.20 * discipline + 0.18 * stability + rng.normal(0.0, 0.94, row_count)
    social = 0.18 * discipline + 0.28 * stability + rng.normal(0.0, 0.93, row_count)

    numeracy_score = _clip01(_sigmoid(0.95 * capacity + 0.18 * discipline + rng.normal(0.0, 0.55, row_count)))
    crt_score = _clip01(_sigmoid(0.82 * capacity + 0.12 * discipline + rng.normal(0.0, 0.58, row_count)))
    financial_literacy_score = _clip01(
        _sigmoid(0.58 * capacity + 0.30 * discipline + rng.normal(0.0, 0.56, row_count))
    )
    future_orientation = _clip01(_sigmoid(0.62 * discipline + 0.24 * stability + rng.normal(0.0, 0.60, row_count)))
    delay_discounting_rate = _clip01(
        0.68 * future_orientation + 0.12 * _sigmoid(0.35 * discipline) + rng.normal(0.0, 0.08, row_count)
    )
    risk_attitude = np.clip(
        0.52 + 0.10 * capacity - 0.06 * discipline + rng.normal(0.0, 0.16, row_count),
        0.02,
        0.98,
    )
    risk_consistency_probability = np.clip(
        0.32 - 0.09 * discipline - 0.07 * capacity + rng.normal(0.0, 0.05, row_count),
        0.04,
        0.55,
    )
    risk_consistency_flag = (rng.random(row_count) < risk_consistency_probability).astype(int)
    loss_aversion_score = _clip01(_sigmoid(0.22 * stability - 0.12 * capacity + rng.normal(0.0, 0.66, row_count)))
    locus_of_control = _clip01(_sigmoid(0.56 * stability + 0.18 * discipline + rng.normal(0.0, 0.58, row_count)))
    conscientiousness_score = _clip01(
        _sigmoid(0.58 * discipline + 0.16 * stability + rng.normal(0.0, 0.56, row_count))
    )
    social_capital_score = _clip01(_sigmoid(0.64 * social + 0.18 * integrity + rng.normal(0.0, 0.60, row_count)))
    honesty_score = _clip01(_sigmoid(0.72 * integrity + 0.18 * discipline + rng.normal(0.0, 0.58, row_count)))
    resilience_score = _clip01(_sigmoid(0.54 * stability + 0.22 * social + rng.normal(0.0, 0.60, row_count)))
    reciprocity_norm = _clip01(_sigmoid(0.56 * social + 0.20 * integrity + rng.normal(0.0, 0.62, row_count)))

    device_type = rng.choice(
        np.array(["mobile", "desktop", "tablet"], dtype=object),
        size=row_count,
        p=[0.72, 0.20, 0.08],
    )
    time_of_day = rng.choice(
        np.array(["morning", "afternoon", "evening", "night"], dtype=object),
        size=row_count,
        p=[0.22, 0.34, 0.29, 0.15],
    )

    avg_response_time_ms = np.clip(
        5_900
        - 1_050 * capacity
        - 380 * discipline
        - 90 * month_offset
        + 250 * (device_type == "mobile")
        + 120 * (time_of_day == "night")
        + rng.normal(0.0, 620.0, row_count),
        900.0,
        12_000.0,
    )
    answer_change_rate = np.clip(
        0.18
        - 0.06 * discipline
        - 0.04 * integrity
        + 0.03 * risk_consistency_flag
        + rng.normal(0.0, 0.04, row_count),
        0.0,
        0.45,
    )
    dropout_lambda = np.clip(
        0.32
        + 0.12 * (risk_attitude > 0.72)
        + 0.08 * (answer_change_rate > 0.18)
        - 0.08 * discipline
        + 0.05 * (device_type == "mobile"),
        0.05,
        1.20,
    )
    dropout_count = np.clip(rng.poisson(dropout_lambda), 0, 6).astype(int)
    scroll_hesitation_score = np.clip(
        0.48
        - 0.10 * discipline
        - 0.08 * stability
        + 0.12 * answer_change_rate
        + rng.normal(0.0, 0.08, row_count),
        0.02,
        0.98,
    )
    risk_response_speed_ratio = np.clip(
        0.90
        + 0.24 * (risk_attitude - 0.5)
        - 0.28 * (crt_score - 0.5)
        - 0.05 * month_offset / 11.0
        + rng.normal(0.0, 0.14, row_count),
        0.30,
        2.50,
    )
    typing_speed_wpm = np.clip(
        28.0
        + 7.5 * capacity
        + 4.0 * conscientiousness_score
        + 0.40 * month_offset
        + 1.5 * (device_type == "desktop")
        + rng.normal(0.0, 4.4, row_count),
        10.0,
        85.0,
    )
    session_duration_sec = np.clip(
        (avg_response_time_ms * 27.0 / 1_000.0) * (1.08 + 0.55 * scroll_hesitation_score + 0.20 * answer_change_rate)
        + dropout_count * 24.0
        + rng.normal(0.0, 22.0, row_count),
        120.0,
        1_400.0,
    )

    text_agency_score = np.clip(
        0.20
        + 0.34 * locus_of_control
        + 0.18 * resilience_score
        + 0.14 * conscientiousness_score
        + rng.normal(0.0, 0.08, row_count),
        0.0,
        1.0,
    )
    text_sentiment_compound = np.clip(
        -0.12
        + 0.92 * (resilience_score - 0.5)
        + 0.38 * (future_orientation - 0.5)
        + 0.18 * (social_capital_score - 0.5)
        + rng.normal(0.0, 0.18, row_count),
        -1.0,
        1.0,
    )
    problem_solving_probability = np.clip(
        0.18
        + 0.34 * resilience_score
        + 0.20 * conscientiousness_score
        + 0.12 * text_agency_score
        + rng.normal(0.0, 0.05, row_count),
        0.05,
        0.95,
    )
    text_problem_solving_flag = (rng.random(row_count) < problem_solving_probability).astype(int)
    text_semantic_dim1 = (
        1.35 * (text_agency_score - 0.5)
        + 0.95 * (resilience_score - 0.5)
        + rng.normal(0.0, 0.65, row_count)
    )
    text_semantic_dim2 = (
        1.10 * text_sentiment_compound
        - 0.60 * (risk_attitude - 0.5)
        + rng.normal(0.0, 0.70, row_count)
    )

    psychological_credit_index = (
        0.22 * numeracy_score
        + 0.18 * honesty_score
        + 0.16 * future_orientation
        + 0.12 * locus_of_control
        + 0.10 * social_capital_score
        + 0.08 * conscientiousness_score
        + 0.06 * crt_score
        + 0.05 * financial_literacy_score
        + 0.03 * (1.0 - loss_aversion_score)
    )
    cognitive_consistency_index = np.clip(
        crt_score * (1.0 - risk_consistency_flag) * (1.0 - answer_change_rate),
        0.0,
        1.0,
    )
    repayment_intention_score = np.clip(
        locus_of_control * social_capital_score * honesty_score,
        0.0,
        1.0,
    )
    impulsivity_index = np.clip(
        (risk_attitude * risk_response_speed_ratio) / (crt_score + 0.1),
        0.0,
        5.0,
    )
    cognitive_load_index = np.clip(
        (avg_response_time_ms / 4_500.0) * (1.0 + answer_change_rate) * (1.0 + dropout_count * 0.2),
        0.0,
        None,
    )
    engagement_score = np.clip(
        (1.0 - scroll_hesitation_score)
        * (1.0 - answer_change_rate)
        * np.clip(1.0 - dropout_count / 4.0, 0.0, 1.0)
        * np.clip(1.0 - risk_response_speed_ratio * 0.3, 0.0, 1.0),
        0.0,
        1.0,
    )
    behavioral_trust_score = np.clip(
        engagement_score * honesty_score * (1.0 - impulsivity_index),
        -1.0,
        1.0,
    )

    gender = rng.choice(
        np.array(["male", "female", "non_binary"], dtype=object),
        size=row_count,
        p=[0.50, 0.47, 0.03],
    )
    age_group = rng.choice(
        np.array(["18-25", "26-35", "36-50", "50+"], dtype=object),
        size=row_count,
        p=[0.25, 0.38, 0.27, 0.10],
    )
    region = rng.choice(
        np.array(["urban", "semi-urban", "rural"], dtype=object),
        size=row_count,
        p=[0.30, 0.35, 0.35],
    )
    education_level = rng.choice(
        np.array(["none", "primary", "secondary", "graduate"], dtype=object),
        size=row_count,
        p=[0.10, 0.24, 0.46, 0.20],
    )
    application_date = _build_application_dates(cohort_month, rng)

    risk_balance = 1.0 - np.clip(np.abs(risk_attitude - 0.55) / 0.55, 0.0, 1.0)
    typing_signal = np.clip((typing_speed_wpm - 18.0) / 40.0, 0.0, 1.0)
    response_burden = np.clip((avg_response_time_ms - 2_000.0) / 6_000.0, 0.0, 1.0)
    load_signal = np.clip((cognitive_load_index - 0.8) / 1.6, 0.0, 2.0)
    impulsivity_signal = np.clip((impulsivity_index - 0.8) / 1.6, 0.0, 2.5)

    repayment_logit = (
        2.8 * (psychological_credit_index - 0.52)
        + 2.3 * (repayment_intention_score - 0.20)
        + 1.4 * (engagement_score - 0.16)
        + 0.9 * (text_agency_score - 0.55)
        + 0.6 * text_problem_solving_flag
        + 0.5 * (typing_signal - 0.35)
        + 0.4 * (risk_balance - 0.5)
        - 1.5 * impulsivity_signal
        - 1.1 * load_signal
        - 0.5 * response_burden
        - 0.7 * answer_change_rate
        - 0.12 * dropout_count
        + rng.normal(0.0, 0.42, row_count)
        + 1.35
    )
    repayment_probability = _sigmoid(repayment_logit)
    repayment_label = (rng.random(row_count) < repayment_probability).astype(int)
    resilience_text = _build_resilience_texts(
        rng,
        text_agency_score=text_agency_score,
        text_sentiment_compound=text_sentiment_compound,
        text_problem_solving_flag=text_problem_solving_flag,
    )

    dataset = pd.DataFrame(
        {
            "numeracy_score": numeracy_score,
            "CRT_score": crt_score,
            "financial_literacy_score": financial_literacy_score,
            "future_orientation": future_orientation,
            "delay_discounting_rate": delay_discounting_rate,
            "risk_attitude": risk_attitude,
            "risk_consistency_flag": risk_consistency_flag,
            "loss_aversion_score": loss_aversion_score,
            "locus_of_control": locus_of_control,
            "conscientiousness_score": conscientiousness_score,
            "social_capital_score": social_capital_score,
            "honesty_score": honesty_score,
            "resilience_score": resilience_score,
            "reciprocity_norm": reciprocity_norm,
            "avg_response_time_ms": avg_response_time_ms,
            "answer_change_rate": answer_change_rate,
            "session_duration_sec": session_duration_sec,
            "dropout_count": dropout_count,
            "scroll_hesitation_score": scroll_hesitation_score,
            "risk_response_speed_ratio": risk_response_speed_ratio,
            "typing_speed_wpm": typing_speed_wpm,
            "text_sentiment_compound": text_sentiment_compound,
            "text_agency_score": text_agency_score,
            "text_problem_solving_flag": text_problem_solving_flag,
            "text_semantic_dim1": text_semantic_dim1,
            "text_semantic_dim2": text_semantic_dim2,
            "psychological_credit_index": psychological_credit_index,
            "cognitive_consistency_index": cognitive_consistency_index,
            "repayment_intention_score": repayment_intention_score,
            "impulsivity_index": impulsivity_index,
            "cognitive_load_index": cognitive_load_index,
            "engagement_score": engagement_score,
            "behavioral_trust_score": behavioral_trust_score,
            "device_type": device_type,
            "time_of_day": time_of_day,
            "gender": gender,
            "age_group": age_group,
            "region": region,
            "education_level": education_level,
            "cohort_month": cohort_month,
            "application_date": application_date,
            TARGET: repayment_label,
            RAW_TEXT_RESPONSE_COLUMN: resilience_text,
        },
        columns=[
            *ALL_MODEL_FEATURES,
            *PROTECTED_FEATURES,
            *TEMPORAL_METADATA,
            TARGET,
            RAW_TEXT_RESPONSE_COLUMN,
        ],
    )

    return dataset


def _build_cohort_months(row_count: int) -> np.ndarray:
    raw_counts = _MONTH_DISTRIBUTION_WEIGHTS * row_count
    month_counts = np.floor(raw_counts).astype(int)
    remainder = row_count - int(month_counts.sum())

    if remainder:
        order = np.argsort(-(raw_counts - month_counts))
        month_counts[order[:remainder]] += 1

    return np.concatenate(
        [
            np.full(month_count, month_index + 1, dtype=int)
            for month_index, month_count in enumerate(month_counts)
        ]
    )


def _build_application_dates(cohort_month: np.ndarray, rng: np.random.Generator) -> list[str]:
    days = [
        int(rng.integers(1, _MONTH_LENGTHS[int(month) - 1] + 1))
        for month in cohort_month
    ]
    return [
        f"{DEFAULT_COHORT_YEAR}-{int(month):02d}-{day:02d}"
        for month, day in zip(cohort_month, days, strict=True)
    ]


def _build_resilience_texts(
    rng: np.random.Generator,
    *,
    text_agency_score: np.ndarray,
    text_sentiment_compound: np.ndarray,
    text_problem_solving_flag: np.ndarray,
) -> list[str]:
    texts: list[str] = []

    for agency, sentiment, problem_solving in zip(
        text_agency_score,
        text_sentiment_compound,
        text_problem_solving_flag,
        strict=True,
    ):
        if sentiment >= 0.2:
            opener_pool = _POSITIVE_RESILIENCE_OPENERS
        elif sentiment <= -0.2:
            opener_pool = _NEGATIVE_RESILIENCE_OPENERS
        else:
            opener_pool = _POSITIVE_RESILIENCE_OPENERS + _NEGATIVE_RESILIENCE_OPENERS

        if agency >= 0.65:
            action_pool = _HIGH_AGENCY_ACTIONS
        elif agency >= 0.4:
            action_pool = _MODERATE_AGENCY_ACTIONS
        else:
            action_pool = _LOW_AGENCY_ACTIONS

        if int(problem_solving) == 1:
            closer_pool = _PROBLEM_SOLVING_CLOSERS
        elif sentiment <= -0.2:
            closer_pool = _NEGATIVE_CLOSERS
        else:
            closer_pool = _NEUTRAL_CLOSERS

        texts.append(
            " ".join(
                [
                    str(rng.choice(opener_pool)),
                    str(rng.choice(action_pool)),
                    str(rng.choice(closer_pool)),
                ]
            )
        )

    return texts


def _clip01(values: np.ndarray) -> np.ndarray:
    return np.clip(values, 0.0, 1.0)


def _sigmoid(values: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-values))


__all__ = [
    "DEFAULT_ROW_COUNT",
    "DEFAULT_SEED",
    "TEMPORAL_SPLIT_MONTHS",
    "generate_synthetic_dataset",
]
