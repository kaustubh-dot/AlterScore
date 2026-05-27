"""Fast behavioral sanity-check system for AlterScore backend scoring.

Validates:
- governance manifest and runtime loading
- protected feature exclusion
- score semantics and risk bands
- positive & negative monotonicity
- explanation consistency
- counterfactual realism
- psychological response consistency (extreme profiles)
- 8 golden regression reference profiles (regression assertions)
- malformed/boundary input resilience (Pydantic validations)

Target runtime: < 15 seconds.
"""

import sys
import json
import traceback
from pathlib import Path
from pydantic import ValidationError

# Setup paths relative to script
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from backend.app.core.artifact_loader import load_runtime_artifact_bundle
from backend.app.services.scoring import ScoringService
from backend.ml.preprocessing.feature_registry import (
    ALL_MODEL_FEATURES,
    PROTECTED_FEATURES,
    ACTIONABLE_FEATURES,
)
from backend.ml.explainability.global_importance import FEATURE_DISPLAY_NAMES
from backend.ml.explainability.dice_explainer import DEFAULT_COUNTERFACTUAL_POLICIES


def load_base_request() -> dict:
    """Load standard valid score request fixture as a base case."""
    fixture_path = REPO_ROOT / "tests" / "fixtures" / "score_request_valid.json"
    if not fixture_path.exists():
        raise FileNotFoundError(
            f"Base score request fixture not found at {fixture_path}"
        )
    with open(fixture_path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_golden_profiles() -> list[dict]:
    """Load 8 golden reference profiles and their assertions."""
    profiles_path = REPO_ROOT / "tests" / "fixtures" / "golden_profiles.json"
    if not profiles_path.exists():
        raise FileNotFoundError(f"Golden profiles fixture not found at {profiles_path}")
    with open(profiles_path, "r", encoding="utf-8") as f:
        return json.load(f)


def perturb_request(
    base: dict, answers_updates: dict = None, behavioral_updates: dict = None
) -> dict:
    """Create a deep copy of base request and update answers/behavioral fields."""
    perturbed = json.loads(json.dumps(base))
    if answers_updates:
        perturbed["answers"].update(answers_updates)
    if behavioral_updates:
        perturbed["behavioral"].update(behavioral_updates)
    return perturbed


def check_governance_and_loading(bundle) -> None:
    """Verify production manifest exists, is valid, and matches loaded model."""
    print("Check 1: Governance & Loading Sanity...")
    report = bundle.report
    if not report.scoring_ready:
        raise ValueError("Artifact bundle reports scoring is NOT ready.")

    manifest_path = REPO_ROOT / "models" / "registry" / "production_manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"Production manifest missing at {manifest_path}")

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    required_keys = [
        "manifest_version",
        "model_version",
        "runtime_model_name",
        "runtime_model_type",
    ]
    for key in required_keys:
        if key not in manifest:
            raise KeyError(f"Production manifest is missing key '{key}'")

    if manifest["runtime_model_name"] != report.runtime_model_name:
        raise ValueError(
            f"Manifest model name '{manifest['runtime_model_name']}' does not match "
            f"loaded bundle model name '{report.runtime_model_name}'"
        )
    print("  [+] OK: Artifact bundle loaded and verified cleanly.")
    print(
        f"  [+] OK: Model name: '{report.runtime_model_name}', type: '{report.runtime_model_type}'"
    )


def check_protected_features() -> None:
    """Ensure protected features are excluded from all active model features."""
    print("\nCheck 2: Protected Feature Exclusion...")
    for pf in PROTECTED_FEATURES:
        if pf in ALL_MODEL_FEATURES:
            raise ValueError(
                f"Protected feature '{pf}' was found in ALL_MODEL_FEATURES!"
            )
    print("  [+] OK: Protected features strictly excluded from model feature registry.")


def check_score_semantics_and_risk_bands(service, base_request) -> None:
    """Verify that credit scores fall within [300, 850] and map correctly to risk bands."""
    print("\nCheck 3: Score Semantics & Risk Bands...")
    response = service.score_request(base_request)

    score = response.credit_score
    if not (300 <= score <= 850):
        raise ValueError(f"Credit score {score} out of bounds [300, 850]")

    risk_band = response.risk_band
    # Thresholds: Excellent (>=750), Good (>=650), Fair (>=550), Poor (<550)
    expected_band = "poor"
    if score >= 750:
        expected_band = "excellent"
    elif score >= 650:
        expected_band = "good"
    elif score >= 550:
        expected_band = "fair"

    if risk_band != expected_band:
        raise ValueError(
            f"Risk band mismatch. Score: {score}, Got: {risk_band}, Expected: {expected_band}"
        )

    eligibility = response.loan_eligibility
    if eligibility.band != risk_band:
        raise ValueError(
            f"Loan eligibility band '{eligibility.band}' doesn't match risk band '{risk_band}'"
        )

    # Check amount bounds
    if risk_band == "excellent":
        expected_min, expected_max = 30000, 75000
    elif risk_band == "good":
        expected_min, expected_max = 10000, 30000
    elif risk_band == "fair":
        expected_min, expected_max = 5000, 12000
    else:
        expected_min, expected_max = 0, 5000

    if eligibility.amount_min != expected_min or eligibility.amount_max != expected_max:
        raise ValueError(
            f"Loan eligibility bounds mismatch for {risk_band}. "
            f"Got: {eligibility.amount_min}-{eligibility.amount_max}, "
            f"Expected: {expected_min}-{expected_max}"
        )

    print(f"  [+] OK: Base request score: {score}, risk band: {risk_band}")
    print(
        f"  [+] OK: Loan eligibility bounds correctly aligned: {eligibility.amount_min} - {eligibility.amount_max}"
    )


def check_monotonicity(service, base_request) -> None:
    """Validate monotonic trends for positive and negative constraints."""
    print("\nCheck 4: Monotonic Behavior...")

    # 1. Numeracy Score (positive constraint, correct answers: 6600, 1120, 14400)
    print("  - Testing Numeracy monotonicity...")
    num_vals = [
        {"numeracy_q1": 0, "numeracy_q2": 0, "numeracy_q3": 0},
        {"numeracy_q1": 6600, "numeracy_q2": 0, "numeracy_q3": 0},
        {"numeracy_q1": 6600, "numeracy_q2": 1120, "numeracy_q3": 0},
        {"numeracy_q1": 6600, "numeracy_q2": 1120, "numeracy_q3": 14400},
    ]
    scores = []
    probs = []
    for val in num_vals:
        req = perturb_request(base_request, answers_updates=val)
        res = service.score_request(req)
        scores.append(res.credit_score)
        probs.append(res.repayment_probability)

    for i in range(len(probs) - 1):
        if probs[i + 1] < probs[i]:
            raise ValueError(
                f"Numeracy monotonicity violation (positive)! "
                f"Step {i}: prob {probs[i]:.4f} (score {scores[i]}), "
                f"Step {i+1}: prob {probs[i+1]:.4f} (score {scores[i+1]})"
            )

    # 2. Avg Response Time MS (negative constraint)
    print("  - Testing Average Response Time monotonicity...")
    time_vals = [1000.0, 5000.0, 20000.0, 60000.0]
    scores = []
    probs = []
    for val in time_vals:
        req = perturb_request(
            base_request, behavioral_updates={"avg_response_time_ms": val}
        )
        res = service.score_request(req)
        scores.append(res.credit_score)
        probs.append(res.repayment_probability)

    for i in range(len(probs) - 1):
        if probs[i + 1] > probs[i]:
            raise ValueError(
                f"Avg response time monotonicity violation (negative)! "
                f"Step {i} ({time_vals[i]}ms): prob {probs[i]:.4f} (score {scores[i]}), "
                f"Step {i+1} ({time_vals[i+1]}ms): prob {probs[i+1]:.4f} (score {scores[i+1]})"
            )

    # 3. Scroll Hesitation Score (negative constraint)
    print("  - Testing Scroll Hesitation monotonicity...")
    scroll_vals = [0.05, 0.35, 0.70, 0.95]
    scores = []
    probs = []
    for val in scroll_vals:
        req = perturb_request(
            base_request, behavioral_updates={"scroll_hesitation_score": val}
        )
        res = service.score_request(req)
        scores.append(res.credit_score)
        probs.append(res.repayment_probability)

    for i in range(len(probs) - 1):
        if probs[i + 1] > probs[i]:
            raise ValueError(
                f"Scroll hesitation monotonicity violation (negative)! "
                f"Step {i} ({scroll_vals[i]}): prob {probs[i]:.4f} (score {scores[i]}), "
                f"Step {i+1} ({scroll_vals[i+1]}): prob {probs[i+1]:.4f} (score {scores[i+1]})"
            )

    # 4. Answer Change Rate (negative constraint)
    print("  - Testing Answer Change Rate monotonicity...")
    change_vals = [0.0, 0.1, 0.4, 0.8]
    scores = []
    probs = []
    for val in change_vals:
        req = perturb_request(
            base_request, behavioral_updates={"answer_change_rate": val}
        )
        res = service.score_request(req)
        scores.append(res.credit_score)
        probs.append(res.repayment_probability)

    for i in range(len(probs) - 1):
        if probs[i + 1] > probs[i]:
            raise ValueError(
                f"Answer change rate monotonicity violation (negative)! "
                f"Step {i} ({change_vals[i]}): prob {probs[i]:.4f} (score {scores[i]}), "
                f"Step {i+1} ({change_vals[i+1]}): prob {probs[i+1]:.4f} (score {scores[i+1]})"
            )

    # 5. Conscientiousness Score (positive constraint)
    print("  - Testing Conscientiousness monotonicity...")
    cons_vals = [1, 3, 5]
    scores = []
    probs = []
    for val in cons_vals:
        req = perturb_request(
            base_request, answers_updates={"conscientiousness_q1": val}
        )
        res = service.score_request(req)
        scores.append(res.credit_score)
        probs.append(res.repayment_probability)

    for i in range(len(probs) - 1):
        if probs[i + 1] < probs[i]:
            raise ValueError(
                f"Conscientiousness monotonicity violation (positive)! "
                f"Step {i} (q1={cons_vals[i]}): prob {probs[i]:.4f} (score {scores[i]}), "
                f"Step {i+1} (q1={cons_vals[i+1]}): prob {probs[i+1]:.4f} (score {scores[i+1]})"
            )

    print(
        "  [+] OK: Monotonicity verified successfully for numeric and psychometric features."
    )


def check_explanations(service, base_request) -> None:
    """Verify that shap contributions, directions, display names, and plain language are correct."""
    print("\nCheck 5: Explanation Consistency...")
    response = service.score_request(base_request)

    if not response.explanation:
        raise ValueError("Explanations list is empty.")

    for item in response.explanation:
        feature = item.feature
        display_name = item.display_name
        shap_value = item.shap_value
        direction = item.direction
        plain_language = item.plain_language

        # Verify display names mapping
        expected_display = FEATURE_DISPLAY_NAMES.get(
            feature, feature.replace("_", " ").title()
        )
        if display_name != expected_display:
            raise ValueError(
                f"Display name mismatch for '{feature}': Got '{display_name}', Expected '{expected_display}'"
            )

        # Verify direction matches SHAP sign
        if direction == "positive" and shap_value < 0.0:
            raise ValueError(
                f"Direction is 'positive' but SHAP value is negative ({shap_value}) for {feature}"
            )
        if direction == "negative" and shap_value >= 0.0:
            raise ValueError(
                f"Direction is 'negative' but SHAP value is positive/zero ({shap_value}) for {feature}"
            )

        # Verify plain language output
        if direction == "positive":
            expected_plain = f"{display_name} is supporting the current score."
        else:
            expected_plain = f"{display_name} is pulling the current score down."

        if plain_language != expected_plain:
            raise ValueError(
                f"Plain language mismatch for {feature}. Got: '{plain_language}', Expected: '{expected_plain}'"
            )

    print(
        "  [+] OK: Explanation directions, display names, and plain language verified."
    )


def check_counterfactual_realism(service, base_request) -> None:
    """Verify counterfactual properties, directions, gains, and boundary conditions."""
    print("\nCheck 6: Counterfactual Realism...")
    response = service.score_request(base_request)

    # 1. Standard Case (Score < 850)
    score = response.credit_score
    actions = response.counterfactual_actions

    if score < 850:
        if not actions:
            raise ValueError(
                f"No counterfactual actions generated for sub-maximal score {score}"
            )

        for action in actions:
            feature = action.feature
            current_value = action.current_value
            suggested_value = action.suggested_value
            gain = action.estimated_score_gain

            # Check actionability
            if feature not in ACTIONABLE_FEATURES:
                raise ValueError(
                    f"Counterfactual proposed on non-actionable feature: {feature}"
                )

            # Verify target directions
            policy = DEFAULT_COUNTERFACTUAL_POLICIES.get(feature)
            if policy:
                direction = policy["direction"]
                if direction == "increase" and suggested_value <= current_value:
                    raise ValueError(
                        f"CF suggests decreasing/equal value ({suggested_value} <= {current_value}) for positive feature {feature}"
                    )
                if direction == "decrease" and suggested_value >= current_value:
                    raise ValueError(
                        f"CF suggests increasing/equal value ({suggested_value} >= {current_value}) for negative feature {feature}"
                    )

            if gain < 0:
                raise ValueError(f"Negative score gain {gain} for feature {feature}")

        print(
            f"  [+] OK: Generated {len(actions)} realistic actions on actionable features."
        )

    # 2. Maximum Score Boundary Case (Score = 850)
    print("  - Testing Boundary Case (Maximum Score 850)...")
    perfect_req = perturb_request(
        base_request,
        answers_updates={
            "numeracy_q1": 6600,
            "numeracy_q2": 1120.0,
            "numeracy_q3": 14400.0,
            "financial_literacy_q1": 1,
            "financial_literacy_q2": 1,
            "conscientiousness_q1": 5,
            "CRT_q1": 5.0,
            "CRT_q2": 5.0,
            "CRT_q3": 47,
            "future_orient_q1": 1,
            "future_orient_q2": 1,
            "future_orient_q3": 5,
            "risk_q1": 0,
            "risk_q2": 0,
            "locus_q1": 0,
            "locus_q2": 0,
            "locus_q3": 5,
            "social_capital_q1": 3,
            "social_capital_q2": 0,
            "social_capital_q3": 0,
            "resilience_q1": 5,
            "resilience_q2": 5,
            "resilience_q3": 0,
            "loss_aversion_q1": 2,
            "honesty_trap_q1": 1,
            "honesty_trap_q2": 1,
            "future_orient_repeat": 1,
            "locus_repeat": 0,
            "reciprocity_q1": 5,
            "reciprocity_q2": 0,
            "q27_resilience_text": "I responded immediately to the setback, reduced my daily expenses, created a strict budget, and successfully paid off my obligations.",
        },
        behavioral_updates={
            "avg_response_time_ms": 1200.0,
            "answer_change_rate": 0.0,
            "session_duration_sec": 180.0,
            "dropout_count": 0,
            "scroll_hesitation_score": 0.01,
            "risk_response_speed_ratio": 1.0,
            "typing_speed_wpm": 75.0,
        },
    )
    perfect_res = service.score_request(perfect_req)
    if perfect_res.credit_score != 850:
        print(
            f"  [!] Warning: Perfect profile score is {perfect_res.credit_score}, not 850. Continuing boundary checks..."
        )

    # Verify maximum score boundary handling (should run without crash, actions list is valid type)
    if not isinstance(perfect_res.counterfactual_actions, list):
        raise TypeError("counterfactual_actions for max score is not a list.")

    print(
        f"  [+] OK: Boundary score: {perfect_res.credit_score}, counterfactuals: {len(perfect_res.counterfactual_actions)} items"
    )


def check_extreme_profiles(service, base_request) -> None:
    """Verify that perfect and poor profiles yield expected and highly distinct risk categorizations."""
    print("\nCheck 7: Extreme Profile Response...")

    # 1. Perfect Profile
    perfect_req = perturb_request(
        base_request,
        answers_updates={
            "numeracy_q1": 6600,
            "numeracy_q2": 1120.0,
            "numeracy_q3": 14400.0,
            "financial_literacy_q1": 1,
            "financial_literacy_q2": 1,
            "conscientiousness_q1": 5,
            "CRT_q1": 5.0,
            "CRT_q2": 5.0,
            "CRT_q3": 47,
            "future_orient_q1": 1,
            "future_orient_q2": 1,
            "future_orient_q3": 5,
            "risk_q1": 0,
            "risk_q2": 0,
            "locus_q1": 0,
            "locus_q2": 0,
            "locus_q3": 5,
            "social_capital_q1": 3,
            "social_capital_q2": 0,
            "social_capital_q3": 0,
            "resilience_q1": 5,
            "resilience_q2": 5,
            "resilience_q3": 0,
            "loss_aversion_q1": 2,
            "honesty_trap_q1": 1,
            "honesty_trap_q2": 1,
            "future_orient_repeat": 1,
            "locus_repeat": 0,
            "reciprocity_q1": 5,
            "reciprocity_q2": 0,
            "q27_resilience_text": "I responded immediately to the setback, reduced my daily expenses, created a strict budget, and successfully paid off my obligations.",
        },
        behavioral_updates={
            "avg_response_time_ms": 1200.0,
            "answer_change_rate": 0.0,
            "session_duration_sec": 180.0,
            "dropout_count": 0,
            "scroll_hesitation_score": 0.01,
            "risk_response_speed_ratio": 1.0,
            "typing_speed_wpm": 75.0,
        },
    )
    perfect_res = service.score_request(perfect_req)

    # 2. Poor Profile
    poor_req = perturb_request(
        base_request,
        answers_updates={
            "numeracy_q1": 0,
            "numeracy_q2": 0.0,
            "numeracy_q3": 0.0,
            "financial_literacy_q1": 0,
            "financial_literacy_q2": 0,
            "conscientiousness_q1": 1,
            "CRT_q1": 0.0,
            "CRT_q2": 0.0,
            "CRT_q3": 1,
            "future_orient_q1": 0,
            "future_orient_q2": 0,
            "future_orient_q3": 1,
            "risk_q1": 1,
            "risk_q2": 0,
            "locus_q1": 2,
            "locus_q2": 2,
            "locus_q3": 1,
            "social_capital_q1": 0,
            "social_capital_q2": 2,
            "social_capital_q3": 2,
            "resilience_q1": 1,
            "resilience_q2": 1,
            "resilience_q3": 3,
            "loss_aversion_q1": 0,
            "honesty_trap_q1": 5,
            "honesty_trap_q2": 5,
            "future_orient_repeat": 0,
            "locus_repeat": 2,
            "reciprocity_q1": 1,
            "reciprocity_q2": 2,
            "q27_resilience_text": "I felt completely helpless, ignored my bills, and did not know what to do.",
        },
        behavioral_updates={
            "avg_response_time_ms": 110000.0,
            "answer_change_rate": 0.9,
            "session_duration_sec": 7000.0,
            "dropout_count": 15,
            "scroll_hesitation_score": 0.95,
            "risk_response_speed_ratio": 4.5,
            "typing_speed_wpm": 5.0,
        },
    )
    poor_res = service.score_request(poor_req)

    print(
        f"  - Perfect Profile -> Score: {perfect_res.credit_score}, Band: {perfect_res.risk_band}, Prob: {perfect_res.repayment_probability:.4f}"
    )
    print(
        f"  - Poor Profile    -> Score: {poor_res.credit_score}, Band: {poor_res.risk_band}, Prob: {poor_res.repayment_probability:.4f}"
    )

    if perfect_res.credit_score <= poor_res.credit_score:
        raise ValueError("Perfect profile score is not higher than poor profile score!")

    if perfect_res.risk_band not in ["excellent", "good"]:
        raise ValueError(
            f"Perfect profile risk band should be 'excellent' or 'good', got '{perfect_res.risk_band}'"
        )

    if poor_res.risk_band != "poor":
        raise ValueError(
            f"Poor profile risk band should be 'poor', got '{poor_res.risk_band}'"
        )

    print("  [+] OK: Extreme profiles respond reasonably and yield correct risk bands.")


def check_golden_profiles(service) -> None:
    """Verify all 8 golden reference profiles produce outputs matching permanent design targets."""
    print("\nCheck 8: Golden Behavioral Profiles Assertions...")
    profiles = load_golden_profiles()

    for entry in profiles:
        name = entry["name"]
        payload = entry["payload"]
        exp = entry["expectations"]

        print(f"  - Testing golden profile '{name}'...")
        res = service.score_request(payload)

        score = res.credit_score
        band = res.risk_band
        eligibility = res.loan_eligibility
        print(f"    [DEBUG] Score: {score}, Band: {band}")

        # Verify score bounds
        if not (exp["score_min"] <= score <= exp["score_max"]):
            raise ValueError(
                f"Golden profile '{name}' score {score} fell outside expected range "
                f"[{exp['score_min']}, {exp['score_max']}]"
            )

        # Verify risk band
        if band != exp["risk_band"]:
            raise ValueError(
                f"Golden profile '{name}' risk band '{band}' did not match expected '{exp['risk_band']}'"
            )

        # Verify loan eligibility
        if eligibility.band != exp["loan_eligibility"]["band"]:
            raise ValueError(
                f"Golden profile '{name}' eligibility band '{eligibility.band}' did not match "
                f"expected '{exp['loan_eligibility']['band']}'"
            )

        if (
            eligibility.amount_min != exp["loan_eligibility"]["amount_min"]
            or eligibility.amount_max != exp["loan_eligibility"]["amount_max"]
        ):
            raise ValueError(
                f"Golden profile '{name}' eligibility amounts {eligibility.amount_min}-{eligibility.amount_max} "
                f"did not match expected {exp['loan_eligibility']['amount_min']}-{exp['loan_eligibility']['amount_max']}"
            )

    print(
        f"  [+] OK: All {len(profiles)} golden reference profiles scored and matched target specifications."
    )


def check_malformed_and_boundary_payloads(service, base_request) -> None:
    """Verify API schema guards and boundary resilience."""
    print("\nCheck 9: Malformed & Boundary Payload Resilience...")

    # 1. Missing Answers Component
    print("  - Testing missing answers payload...")
    try:
        service.score_request({"behavioral": base_request["behavioral"]})
        raise ValueError(
            "Failed to raise ValidationError for missing 'answers' component"
        )
    except ValidationError:
        pass  # Expected Pydantic validation error
    except Exception as e:
        raise ValueError(
            f"Unexpected exception for missing answers: {type(e).__name__}: {e}"
        )

    # 2. Invalid answer value type/out-of-bounds (Pydantic guard)
    print("  - Testing out-of-bounds input (conscientiousness_q1=10)...")
    try:
        bad_req = perturb_request(
            base_request, answers_updates={"conscientiousness_q1": 10}
        )
        service.score_request(bad_req)
        raise ValueError("Failed to raise ValidationError for conscientiousness_q1=10")
    except ValidationError:
        pass  # Expected Pydantic validation error
    except Exception as e:
        raise ValueError(
            f"Unexpected exception for invalid conscientiousness_q1: {type(e).__name__}: {e}"
        )

    # 3. Empty text q27_resilience_text (ensure robust fallback)
    print("  - Testing empty resilience text fallback...")
    empty_txt_req = perturb_request(
        base_request, answers_updates={"q27_resilience_text": ""}
    )
    empty_txt_res = service.score_request(empty_txt_req)
    # Ensure it maps to a valid score without crash
    if not (300 <= empty_txt_res.credit_score <= 850):
        raise ValueError(f"Empty text score {empty_txt_res.credit_score} out of bounds")

    # 4. Extreme timing boundary values
    print("  - Testing extreme fast avg response time (100ms)...")
    fast_time_req = perturb_request(
        base_request, behavioral_updates={"avg_response_time_ms": 100.0}
    )
    fast_time_res = service.score_request(fast_time_req)
    if not (300 <= fast_time_res.credit_score <= 850):
        raise ValueError(f"Fast time score {fast_time_res.credit_score} out of bounds")

    print("  - Testing extreme slow avg response time (120000ms)...")
    slow_time_req = perturb_request(
        base_request, behavioral_updates={"avg_response_time_ms": 120000.0}
    )
    slow_time_res = service.score_request(slow_time_req)
    if not (300 <= slow_time_res.credit_score <= 850):
        raise ValueError(f"Slow time score {slow_time_res.credit_score} out of bounds")

    # 5. Invalid device dropdown choice
    print("  - Testing invalid device type dropdown value...")
    try:
        bad_req = perturb_request(
            base_request, behavioral_updates={"device_type": "smartwatch"}
        )
        service.score_request(bad_req)
        raise ValueError(
            "Failed to raise ValidationError for invalid device_type 'smartwatch'"
        )
    except ValidationError:
        pass  # Expected
    except Exception as e:
        raise ValueError(
            f"Unexpected exception for invalid device_type: {type(e).__name__}: {e}"
        )

    print(
        "  [+] OK: Schema validation and boundary values behave correctly and robustly."
    )


def main() -> int:
    print("=" * 60)
    print("ALTERSCORE BACKEND BEHAVIORAL SANITY CHECK")
    print("=" * 60)

    try:
        # Load artifacts and service
        bundle = load_runtime_artifact_bundle(strict=True)
        service = ScoringService(bundle)
        base_request = load_base_request()

        # Run validations
        check_governance_and_loading(bundle)
        check_protected_features()
        check_score_semantics_and_risk_bands(service, base_request)
        check_monotonicity(service, base_request)
        check_explanations(service, base_request)
        check_counterfactual_realism(service, base_request)
        check_extreme_profiles(service, base_request)
        check_golden_profiles(service)
        check_malformed_and_boundary_payloads(service, base_request)

        print("\n" + "=" * 60)
        print(
            "[+] SUCCESS: All behavioral, golden regression, and schema checks passed!"
        )
        print("=" * 60)
        return 0

    except Exception as e:
        print("\n" + "=" * 60)
        print(f"[-] SANITY CHECK FAILED: {e}")
        print("=" * 60)
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
