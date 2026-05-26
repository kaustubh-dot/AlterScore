"""Lightweight validity probe for AlterScore score-inflation audit.

Checks synthetic data distribution, answer parsing for random users,
and score mapping behavior. Does NOT require model artifacts or GPU.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

# Ensure project root is on sys.path
project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


def probe_synthetic_data_distribution() -> None:
    """Check the synthetic data label and feature distributions."""
    print("=" * 60)
    print("PROBE 1: Synthetic Data Distribution")
    print("=" * 60)

    from backend.ml.data_generation.generator import generate_synthetic_dataset

    df = generate_synthetic_dataset(10_000, seed=42)
    default_rate = float((df["repayment_label"] == 0).mean())
    repay_rate = 1.0 - default_rate

    print(f"  Repayment rate: {repay_rate:.1%}")
    print(f"  Default rate:   {default_rate:.1%}")
    print()

    if default_rate < 0.30:
        print("  [FAIL] Default rate too low (< 30%). Model will be too optimistic.")
    elif default_rate > 0.45:
        print("  [FAIL] Default rate too high (> 45%). Model may be too pessimistic.")
    else:
        print(f"  [PASS] Default rate {default_rate:.1%} is in the target range [30%, 45%].")

    print()
    print("  Feature statistics:")
    key_features = [
        "numeracy_score", "CRT_score", "honesty_score", "resilience_score",
        "conscientiousness_score", "future_orientation", "psychological_credit_index",
        "engagement_score", "impulsivity_index", "behavioral_trust_score",
    ]
    for col in key_features:
        mean = df[col].mean()
        std = df[col].std()
        median = df[col].median()
        print(f"    {col:35s}: mean={mean:.3f}  std={std:.3f}  median={median:.3f}")
    print()


def probe_random_answer_profile() -> None:
    """Simulate a random user's psychometric profile."""
    print("=" * 60)
    print("PROBE 2: Random-Answer Psychometric Profile")
    print("=" * 60)

    from backend.ml.features.answer_parser import parse_answers

    rng = np.random.default_rng(42)
    n_simulations = 1000
    all_features: dict[str, list[float]] = {}

    for _ in range(n_simulations):
        answers = {
            "numeracy_q1": rng.integers(1000, 10000),
            "numeracy_q2": rng.integers(500, 2000),
            "numeracy_q3": rng.integers(5000, 20000),
            "financial_literacy_q1": int(rng.integers(0, 4)),
            "financial_literacy_q2": int(rng.integers(0, 3)),
            "conscientiousness_q1": int(rng.integers(1, 6)),
            "CRT_q1": rng.integers(1, 20),
            "CRT_q2": rng.integers(1, 200),
            "CRT_q3": rng.integers(1, 100),
            "future_orient_q1": int(rng.integers(0, 2)),
            "future_orient_q2": int(rng.integers(0, 2)),
            "future_orient_q3": int(rng.integers(1, 6)),
            "risk_q1": int(rng.integers(0, 2)),
            "risk_q2": int(rng.integers(0, 2)),
            "loss_aversion_q1": int(rng.integers(0, 3)),
            "locus_q1": int(rng.integers(0, 3)),
            "locus_q2": int(rng.integers(0, 3)),
            "locus_q3": int(rng.integers(1, 6)),
            "social_capital_q1": int(rng.integers(0, 4)),
            "social_capital_q2": int(rng.integers(0, 3)),
            "social_capital_q3": int(rng.integers(0, 3)),
            "resilience_q1": int(rng.integers(1, 6)),
            "resilience_q2": int(rng.integers(1, 6)),
            "resilience_q3": int(rng.integers(0, 4)),
            "reciprocity_q1": int(rng.integers(1, 6)),
            "reciprocity_q2": int(rng.integers(0, 3)),
            "future_orient_repeat": int(rng.integers(0, 2)),
            "locus_repeat": int(rng.integers(0, 3)),
            "honesty_trap_q1": int(rng.integers(1, 6)),
            "honesty_trap_q2": int(rng.integers(1, 6)),
        }
        features = parse_answers(answers)
        for key, value in features.items():
            all_features.setdefault(key, []).append(value)

    print("  Expected psychometric profile from 1000 random simulations:")
    print()
    for feature_name, values in all_features.items():
        arr = np.array(values)
        status = "[PASS]" if arr.mean() < 0.40 else ("[WARN]" if arr.mean() < 0.55 else "[FAIL]")
        print(f"    {status:8s} {feature_name:35s}: mean={arr.mean():.3f}  std={arr.std():.3f}")
    print()


def probe_score_mapping() -> None:
    """Show the score mapping table for key probabilities."""
    print("=" * 60)
    print("PROBE 3: Score Mapping Table")
    print("=" * 60)

    from backend.ml.inference.score_mapper import probability_to_score, get_risk_band

    probabilities = [0.10, 0.20, 0.30, 0.40, 0.50, 0.60, 0.65, 0.70, 0.75,
                     0.80, 0.85, 0.90, 0.95, 0.97, 0.98, 0.99]
    print(f"  {'Probability':>12s}  {'Score':>6s}  {'Band':>10s}")
    print(f"  {'-'*12}  {'-'*6}  {'-'*10}")
    for prob in probabilities:
        score = probability_to_score(prob)
        band = get_risk_band(score)
        print(f"  {prob:>12.3f}  {score:>6d}  {band:>10s}")
    print()

    # Verify the 838 case
    for prob in [0.95, 0.96, 0.97, 0.98, 0.985, 0.988, 0.99]:
        score = probability_to_score(prob)
        if score >= 838:
            print(f"  [WARN] 838 score now requires P(repay) >= {prob:.3f}")
            break
    print()


def probe_governance_multiplier() -> None:
    """Test the governance multiplier for different user profiles."""
    print("=" * 60)
    print("PROBE 4: Governance Multiplier Behavior")
    print("=" * 60)

    # We import and call the private function directly
    from backend.app.services.scoring import _calculate_governance_multiplier

    profiles = {
        "Random user (low cognitive, moderate behavior)": {
            "impulsivity_index": 0.8,
            "honesty_score": 0.45,
            "dropout_count": 0,
            "answer_change_rate": 0.05,
            "numeracy_score": 0.0,
            "CRT_score": 0.0,
            "engagement_score": 0.5,
            "avg_response_time_ms": 3000,
        },
        "Fast random spammer": {
            "impulsivity_index": 2.0,
            "honesty_score": 0.30,
            "dropout_count": 1,
            "answer_change_rate": 0.10,
            "numeracy_score": 0.0,
            "CRT_score": 0.0,
            "engagement_score": 0.15,
            "avg_response_time_ms": 1200,
        },
        "Thoughtful responsible user": {
            "impulsivity_index": 0.3,
            "honesty_score": 0.85,
            "dropout_count": 0,
            "answer_change_rate": 0.02,
            "numeracy_score": 0.8,
            "CRT_score": 0.7,
            "engagement_score": 0.75,
            "avg_response_time_ms": 7000,
        },
        "Gaming user (all perfect + traps)": {
            "impulsivity_index": 0.2,
            "honesty_score": 0.25,
            "dropout_count": 0,
            "answer_change_rate": 0.0,
            "numeracy_score": 1.0,
            "CRT_score": 1.0,
            "engagement_score": 0.80,
            "avg_response_time_ms": 5000,
        },
    }

    from backend.ml.inference.score_mapper import probability_to_score, get_risk_band

    for profile_name, feature_row in profiles.items():
        multiplier, reasons = _calculate_governance_multiplier(feature_row)
        # Show what score a P=0.95 base probability would produce
        adjusted = max(0.01, min(0.99, 0.95 * multiplier))
        score = probability_to_score(adjusted)
        band = get_risk_band(score)
        print(f"\n  {profile_name}:")
        print(f"    Multiplier: {multiplier:.3f}")
        print(f"    If base P=0.95 -> adjusted P={adjusted:.3f} -> score={score} ({band})")
        if reasons:
            for reason in reasons:
                print(f"    [WARN] {reason}")
        else:
            print(f"    [PASS] No governance penalties triggered")
    print()


if __name__ == "__main__":
    probe_synthetic_data_distribution()
    probe_random_answer_profile()
    probe_score_mapping()
    probe_governance_multiplier()
    print("=" * 60)
    print("All probes complete.")
    print("=" * 60)
