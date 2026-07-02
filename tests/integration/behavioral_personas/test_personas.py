import pytest
from backend.app.services.scoring import score_request_with_bundle
from backend.app.core.artifact_loader import load_runtime_artifact_bundle
from backend.app.core.settings import load_settings


@pytest.fixture
def runtime_artifacts(tmp_path):
    from backend.app.core.paths import REPO_ROOT
    import shutil

    model_directories = (
        "artifacts",
        "explainers",
        "preprocessors",
        "registry",
        "reports",
    )
    for directory_name in model_directories:
        source_dir = REPO_ROOT / "models" / directory_name
        target_dir = tmp_path / "models" / directory_name
        target_dir.mkdir(parents=True, exist_ok=True)
        for source_path in source_dir.iterdir():
            if source_path.name == ".gitkeep":
                continue
            shutil.copy2(source_path, target_dir / source_path.name)

    settings = load_settings(
        {
            "ALTERSCORE_REPO_ROOT": str(tmp_path),
        }
    )
    return load_runtime_artifact_bundle(settings, strict=True)


def _build_request(preset: dict) -> dict:
    answers = preset["answers"].copy()
    scenario_least_candidates = {
        "scenario_s1": ("s1_b", "s1_a", "s1_c", "s1_d"),
        "scenario_s2": ("s2_d", "s2_b", "s2_c", "s2_a"),
        "scenario_s3": ("s3_d", "s3_b", "s3_c", "s3_a"),
        "scenario_s4": ("s4_c", "s4_b", "s4_a", "s4_d"),
        "scenario_s5": ("s5_c", "s5_b", "s5_a", "s5_d"),
        "scenario_s6": ("s6_d", "s6_a", "s6_b", "s6_c"),
        "scenario_s8": ("s8_b", "s8_a", "s8_c", "s8_d"),
    }
    for k, v in answers.items():
        if k.startswith("scenario_") and isinstance(v, str):
            least = next(
                candidate
                for candidate in scenario_least_candidates[k]
                if candidate != v
            )
            answers[k] = {"primary": v, "least": least}

    return {
        "session_id": f"test_{preset['id']}",
        "answers": answers,
        "behavioral": preset["behavioral"],
    }


# Presets from frontend (subset for regression testing)
PRESETS = {
    "thoughtful": {
        "id": "thoughtful",
        "answers": {
            "numeracy_q1": 6600,
            "numeracy_q2": 1120,
            "financial_literacy_q1": 1,
            "CRT_q1": 5,
            "CRT_q2": 47,
            "scenario_s1": "s1_a",
            "scenario_s2": "s2_b",
            "scenario_s3": "s3_c",
            "scenario_s4": "s4_a",
            "scenario_s5": "s5_b",
            "scenario_s6": "s6_a",
            "honesty_trap_q1": 2,
            "scenario_s8": "s8_a",
            "open_response_text": (
                "We faced a significant agricultural price decline during harvest season. "
                "I compared price variations, negotiated store inventory terms with key "
                "suppliers, and planned better grain sale timing."
            ),
        },
        "behavioral": {
            "avg_response_time_ms": 5300.0,
            "answer_change_rate": 0.018,
            "session_duration_sec": 210.0,
            "dropout_count": 0,
            "scroll_hesitation_score": 0.037,
            "risk_response_speed_ratio": 0.98,
            "time_of_day": "morning",
            "device_type": "desktop",
            "typing_speed_wpm": 56.0,
        },
    },
    "impulsive": {
        "id": "impulsive",
        "answers": {
            "numeracy_q1": 6000,
            "numeracy_q2": 100,
            "financial_literacy_q1": 0,
            "CRT_q1": 100,
            "CRT_q2": 10,
            "scenario_s1": "s1_d",
            "scenario_s2": "s2_d",
            "scenario_s3": "s3_d",
            "scenario_s4": "s4_d",
            "scenario_s5": "s5_a",
            "scenario_s6": "s6_d",
            "honesty_trap_q1": 3,
            "scenario_s8": "s8_d",
            "open_response_text": (
                "I faced a sudden cash crisis, cut extra spending, asked my family "
                "for help, and paid the urgent bill."
            ),
        },
        "behavioral": {
            "avg_response_time_ms": 550.0,
            "answer_change_rate": 0.0,
            "session_duration_sec": 22.0,
            "dropout_count": 0,
            "scroll_hesitation_score": 0.0,
            "risk_response_speed_ratio": 1.0,
            "time_of_day": "morning",
            "device_type": "mobile",
            "typing_speed_wpm": 15.0,
        },
    },
    "manipulated": {
        "id": "manipulated",
        "answers": {
            "numeracy_q1": 6600,
            "numeracy_q2": 1120,
            "financial_literacy_q1": 1,
            "CRT_q1": 5,
            "CRT_q2": 47,
            "scenario_s1": "s1_a",
            "scenario_s2": "s2_a",
            "scenario_s3": "s3_a",
            "scenario_s4": "s4_a",
            "scenario_s5": "s5_a",
            "scenario_s6": "s6_a",
            "honesty_trap_q1": 5,
            "scenario_s8": "s8_b",
            "open_response_text": "Everything was perfectly fine and we had no difficulties. I handled it instantly because my finances are perfect.",
        },
        "behavioral": {
            "avg_response_time_ms": 1800.0,
            "answer_change_rate": 0.0,
            "session_duration_sec": 75.0,
            "dropout_count": 0,
            "scroll_hesitation_score": 0.0,
            "risk_response_speed_ratio": 1.0,
            "time_of_day": "night",
            "device_type": "desktop",
            "typing_speed_wpm": 92.0,
        },
    },
    "average": {
        "id": "average",
        "answers": {
            "numeracy_q1": 6600,
            "numeracy_q2": 1120,
            "financial_literacy_q1": 1,
            "CRT_q1": 5,
            "CRT_q2": 24,
            "scenario_s1": "s1_c",
            "scenario_s2": "s2_c",
            "scenario_s3": "s3_b",
            "scenario_s4": "s4_b",
            "scenario_s5": "s5_c",
            "scenario_s6": "s6_b",
            "honesty_trap_q1": 3,
            "scenario_s8": "s8_c",
            "open_response_text": (
                "I had a sudden emergency when my laptop broke, so I contacted a repair "
                "shop, planned my payments, and saved client work first."
            ),
        },
        "behavioral": {
            "avg_response_time_ms": 3200.0,
            "answer_change_rate": 0.111,
            "session_duration_sec": 220.0,
            "dropout_count": 1,
            "scroll_hesitation_score": 0.148,
            "risk_response_speed_ratio": 1.05,
            "time_of_day": "morning",
            "device_type": "tablet",
            "typing_speed_wpm": 42.0,
        },
    },
}


def test_thoughtful_applicant_scores_well(runtime_artifacts):
    req = _build_request(PRESETS["thoughtful"])
    res = score_request_with_bundle(req, runtime_artifacts)
    assert res.credit_score > 450, "Thoughtful applicant should score reasonably well."
    assert (
        res.repayment_probability > 0.3
    ), "Thoughtful applicant should have solid probability."


def test_impulsive_applicant_is_penalized(runtime_artifacts):
    req = _build_request(PRESETS["impulsive"])
    res = score_request_with_bundle(req, runtime_artifacts)
    assert res.risk_band == "poor", "Impulsive applicant should stay in poor band."
    assert (
        res.credit_score < 550
    ), "Impulsive applicant should remain below fair-band eligibility."
    assert (
        res.repayment_probability < 0.2
    ), "Impulsive applicant should be heavily penalized by governance."


def test_manipulated_applicant_triggers_consistency_penalty(runtime_artifacts):
    req = _build_request(PRESETS["manipulated"])
    res = score_request_with_bundle(req, runtime_artifacts)
    # The manipulated profile hits the honesty trap (5) and inconsistency (S1 vs S8).
    # Its score should be lower than a thoughtful applicant despite identical cognitive metrics.
    req_thoughtful = _build_request(PRESETS["thoughtful"])
    res_thoughtful = score_request_with_bundle(req_thoughtful, runtime_artifacts)

    assert (
        res.credit_score < res_thoughtful.credit_score
    ), "Manipulated applicant must score lower than thoughtful."
    assert (
        res.repayment_probability < res_thoughtful.repayment_probability
    ), "Governance penalty must reduce probability."


def test_average_applicant_falls_in_middle_tier(runtime_artifacts):
    req = _build_request(PRESETS["average"])
    res = score_request_with_bundle(req, runtime_artifacts)
    req_impulsive = _build_request(PRESETS["impulsive"])
    res_impulsive = score_request_with_bundle(req_impulsive, runtime_artifacts)
    req_thoughtful = _build_request(PRESETS["thoughtful"])
    res_thoughtful = score_request_with_bundle(req_thoughtful, runtime_artifacts)

    assert (
        res.repayment_probability > res_impulsive.repayment_probability
    ), "Average should beat impulsive."
    assert res.risk_band in {
        "fair",
        "good",
    }, "Average should stay in the middle bands."
    assert (
        res.credit_score < 750
    ), "Average should remain below excellent-band eligibility."
    assert (
        abs(res.repayment_probability - res_thoughtful.repayment_probability) < 0.05
    ), "Average should stay close to, not materially exceed, thoughtful."
