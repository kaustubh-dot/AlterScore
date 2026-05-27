import json
import logging
from backend.app.core.artifact_loader import load_runtime_artifact_bundle
from backend.app.services.scoring import score_request_with_bundle
import sys
import re

logging.basicConfig(level=logging.ERROR)

# Minimal mock of presets from frontend
presets = [
  {
    "id": "strong",
    "name": "High Literacy / Strong Applicant",
    "answers": {
      "numeracy_q1": 6600, "numeracy_q2": 1120, "financial_literacy_q1": 1,
      "CRT_q1": 5, "CRT_q2": 47,
      "scenario_s1": "s1_a", "scenario_s2": "s2_b", "scenario_s3": "s3_c", "scenario_s4": "s4_a", "scenario_s5": "s5_b", "scenario_s6": "s6_a",
      "honesty_trap_q1": 2, "scenario_s8": "s8_a",
      "open_response_text": "During a sudden business inventory crisis, we lost key supply contacts. I immediately drafted a contingency budget, cut discretionary overhead, and built direct relations with two local distributors. We recovered operations in three weeks and kept all payments fully on time."
    },
    "behavioral": {
      "avg_response_time_ms": 4800.0, "answer_change_rate": 0.037, "session_duration_sec": 195.0, "dropout_count": 0, "scroll_hesitation_score": 0.037, "risk_response_speed_ratio": 0.92, "time_of_day": "afternoon", "device_type": "desktop", "typing_speed_wpm": 68.0
    }
  },
  {
    "id": "manipulated",
    "name": "Manipulated / Inconsistent Applicant",
    "answers": {
      "numeracy_q1": 6600, "numeracy_q2": 1120, "financial_literacy_q1": 1,
      "CRT_q1": 5, "CRT_q2": 47,
      "scenario_s1": "s1_a", "scenario_s2": "s2_a", "scenario_s3": "s3_a", "scenario_s4": "s4_a", "scenario_s5": "s5_a", "scenario_s6": "s6_a",
      "honesty_trap_q1": 5, "scenario_s8": "s8_b",
      "open_response_text": "Everything was perfectly fine and we had no difficulties. I handled it instantly because my finances are perfect and I am the best loan candidate ever."
    },
    "behavioral": {
      "avg_response_time_ms": 1800.0, "answer_change_rate": 0.0, "session_duration_sec": 75.0, "dropout_count": 0, "scroll_hesitation_score": 0.0, "risk_response_speed_ratio": 1.0, "time_of_day": "night", "device_type": "desktop", "typing_speed_wpm": 92.0
    }
  },
  {
    "id": "impulsive",
    "name": "Impulsive Fast Responder",
    "answers": {
      "numeracy_q1": 6000, "numeracy_q2": 100, "financial_literacy_q1": 0,
      "CRT_q1": 100, "CRT_q2": 10,
      "scenario_s1": "s1_d", "scenario_s2": "s2_d", "scenario_s3": "s3_d", "scenario_s4": "s4_d", "scenario_s5": "s5_a", "scenario_s6": "s6_d",
      "honesty_trap_q1": 3, "scenario_s8": "s8_d",
      "open_response_text": "I had a crisis and solved it. Standard situation."
    },
    "behavioral": {
      "avg_response_time_ms": 550.0, "answer_change_rate": 0.0, "session_duration_sec": 22.0, "dropout_count": 0, "scroll_hesitation_score": 0.0, "risk_response_speed_ratio": 1.0, "time_of_day": "morning", "device_type": "mobile", "typing_speed_wpm": 15.0
    }
  },
  {
    "id": "thoughtful",
    "name": "Thoughtful Stable Applicant",
    "answers": {
      "numeracy_q1": 6600, "numeracy_q2": 1120, "financial_literacy_q1": 1,
      "CRT_q1": 5, "CRT_q2": 47,
      "scenario_s1": "s1_a", "scenario_s2": "s2_b", "scenario_s3": "s3_c", "scenario_s4": "s4_a", "scenario_s5": "s5_b", "scenario_s6": "s6_a",
      "honesty_trap_q1": 2, "scenario_s8": "s8_a",
      "open_response_text": "We faced a significant agricultural price decline during harvest season. I analyzed price variations, renegotiated store inventory terms with key suppliers, and held key grains for better trade prices. The strategy paid off within two months."
    },
    "behavioral": {
      "avg_response_time_ms": 5300.0, "answer_change_rate": 0.018, "session_duration_sec": 210.0, "dropout_count": 0, "scroll_hesitation_score": 0.037, "risk_response_speed_ratio": 0.98, "time_of_day": "morning", "device_type": "desktop", "typing_speed_wpm": 56.0
    }
  }
]

def main():
    try:
        artifacts = load_runtime_artifact_bundle()
    except Exception as e:
        print(f"Error loading artifacts: {e}")
        sys.exit(1)
        
    for p in presets:
        # Update scenario answers to match backend ScenarioAnswer schema
        updated_answers = p["answers"].copy()
        for k, v in updated_answers.items():
            if k.startswith("scenario_") and isinstance(v, str):
                updated_answers[k] = {"primary": v}
                
        req = {
            "session_id": f"test_{p['id']}",
            "answers": updated_answers,
            "behavioral": p["behavioral"]
        }
        res = score_request_with_bundle(req, artifacts)
        print(f"--- Profile: {p['name']} ---")
        print(f"Score: {res.credit_score}")
        print(f"Risk Band: {res.risk_band}")
        print(f"Probability: {res.repayment_probability}")
        print(f"Explanations (Top 2):")
        for exp in res.explanation[:2]:
            print(f"  - {exp.display_name}: {exp.shap_value} ({exp.direction})")
        print("\n")

if __name__ == "__main__":
    main()
