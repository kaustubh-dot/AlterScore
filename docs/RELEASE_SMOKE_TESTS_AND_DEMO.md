# AlterScore Release Smoke-Tests, Stakeholder Demo & Rollback Runbook

This document defines the final release checks, the narrative stakeholder walkthrough script, and the manifest hot-rollback checklist.

---

## 1. Release Smoke-Test Checklist

Perform these checks on the serving host immediately prior to releasing a new deployment package:

### 1.1 Server Startup & Checksum Auditing
1. Boot the platform using the automated script:
   ```powershell
   powershell -ExecutionPolicy Bypass -File scripts\setup\start_alterscore.ps1
   ```
2. Verify uvicorn console output shows zero warning or checksum mismatches:
   * Expect: `INFO: Loaded artifact preprocessor_monotonic.pkl (SHA256 verified)`
   * Expect: `INFO: Loaded artifact xgboost_monotonic.pkl (SHA256 verified)`
   * Expect: `Uvicorn running on http://127.0.0.1:8000`

### 1.2 REST API Smoke Testing

#### Test Case A: Valid Prime Borrower
Submit a highly financially literate, patient applicant profile:
```powershell
# Send valid request
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/score" -Method Post -InFile "tests/fixtures/score_request_valid.json" -ContentType "application/json"
```
* **Expected Output:**
  * HTTP Status: `200 OK`
  * Score range: `700 - 850` (Good/Excellent risk band)
  * Repayment Probability: `> 80%`
  * Explainability: Exposes top 6 SHAP factors (positive contribution from `numeracy_score` and `future_orient_q1`)
  * Counterfactuals: Minimal actionable recommendations (due to low risk)

#### Test Case B: High-Risk Bounded Borrower
Submit an applicant profile with lower literacy and high impulsivity:
```json
{
  "answers": {
    "numeracy_q1": 0, "numeracy_q2": 0, "numeracy_q3": 0,
    "financial_literacy_q1": 0, "financial_literacy_q2": 0,
    "conscientiousness_q1": 0, "CRT_q1": 0, "CRT_q2": 0, "CRT_q3": 0,
    "future_orient_q1": 0, "future_orient_q2": 0, "future_orient_q3": 0,
    "risk_q1": 1, "risk_q2": 1, "loss_aversion_q1": 2,
    "locus_q1": 2, "locus_q2": 2, "locus_q3": 0,
    "social_capital_q1": 0, "social_capital_q2": 2, "social_capital_q3": 2,
    "resilience_q1": 0, "resilience_q2": 0, "resilience_q3": 3,
    "reciprocity_q1": 0, "reciprocity_q2": 2, "future_orient_repeat": 0,
    "locus_repeat": 2, "honesty_trap_q1": 0, "honesty_trap_q2": 0,
    "q27_resilience_text": "I faced a loss but i did not do anything about it. I just waited for things to get better."
  },
  "behavioral_telemetry": {
    "avg_response_time_ms": 12000,
    "answer_change_rate": 0.45,
    "session_duration_sec": 480,
    "dropout_count": 2,
    "scroll_hesitation_score": 0.65,
    "risk_response_speed_ratio": 1.8,
    "time_of_day": "night",
    "device_type": "mobile",
    "typing_speed_wpm": 15
  }
}
```
* **Expected Output:**
  * HTTP Status: `200 OK`
  * Score range: `300 - 540` (Poor risk band)
  * Repayment Probability: `< 40%`
  * Counterfactuals: Emits highly bounded, actionable improvements (e.g. *"Increase numeracy score by 1 point"*, *"Select future-oriented preferences on question B4"*).

---

## 2. Stakeholder Demo Walkthrough Script

Use this script to present AlterScore to investors, underwriters, or compliance teams.

### 🎬 Scene 1: Alternative Credit Scoring Philosophy
* **Action:** Open `http://127.0.0.1:5173` on a browser.
* **Talk Track:** 
  > *"Welcome to AlterScore. Traditional credit bureaus systematically exclude thin-file, unbanked, and younger borrowers who have never taken a bank loan. AlterScore bridges this gap. By evaluating psychometric thinking, behavioral telemetry, and local NLP cues, we build a robust, governed alternative risk score that unlocks capital safely without relying on credit histories."*

### 🎬 Scene 2: Interactive Assessment & Telemetry Capture
* **Action:** Click **Get Started** and navigate to `/assessment`. Complete Section A (Financial thinking numeracy and literacy) and Section B (Risk preference CRT questions). Highlight the open-text question at Section D (Q27 text prompt).
* **Talk Track:**
  > *"Instead of asking for bank logins, the borrower completes a 27-question gamified assessment covering core financial capability, resilience, and patience. As they answer, our frontend silently captures micromobility metrics—such as answer change rates, response hesitancy, and typing speed on open-ended questions—to verify applicant authenticity and check for robotic behavior."*

### 🎬 Scene 3: Calibrated Results Reveal
* **Action:** Submit the assessment. Observe the WebGL particle loading screen, then watch the score gauge spin to its final calibrated number (e.g., `720`). Point out the **SHAP Contribution Bars** and **WhatsApp Share** button.
* **Talk Track:**
  > *"AlterScore does not emit black-box decisions. Here is the borrower's calibrated score. Below it, the explainability engine exposes the top factors that influenced their result. More importantly, we provide bounded, actionable improvement tips. If they increase their scores, they can instantly share the certificate with local lending partners."*

### 🎬 Scene 4: Evaluator Dashboard Governance
* **Action:** Navigate to `http://127.0.0.1:5173/dashboard`. Show the Performance Tab, the line charts, and scroll to the new **Predictive Confusion Matrix** decision grid.
* **Talk Track:**
  > *"For risk underwriters, we provide the Governance Center. Here, we audit model fairness, population stability, and predictive quality in real-time. Notice our new Predictive Confusion Matrix panel—which visualizes actual versus predicted defaults alongside model Accuracy, Precision, and Recall under locked manifest thresholds, demonstrating that the system protects lender portfolios."*

---

## 3. Rollback Checklist Tied to Manifest Versions

If the active model manifest exhibits unexpected drift or subgroup bias, follow this checklist to safely swap manifest versions:

- [ ] **1. Identify Rollback Target:** Select the stable calibrated stacking ensemble manifest configuration:
  * Target manifest: `models/registry/production_manifest.json` (Replace with backup meta-learner config)
- [ ] **2. Swap Environment Configs:** Edit the `.env` file to redirect the serving path:
  ```bash
  ALTERSCORE_MODEL_MANIFEST=models/registry/stacking_ensemble_manifest.json
  ```
- [ ] **3. Reload Services:** Restart the FastAPI uvicorn daemon.
- [ ] **4. Audit Logs:** Check console logs to verify the backend successfully lazily loads all 6 base models and the stacking meta-learner:
  ```text
  INFO: Loaded stacking ensemble configuration
  INFO: Loaded base model rf_best.pkl
  INFO: Loaded base model lgbm_best.pkl
  INFO: Loaded base model mlp_best.pt
  INFO: Expected 18 artifacts, loaded 18 successfully
  ```
- [ ] **5. Verification REST Check:** Execute Test Case A (Prime Borrower) to verify score responses resolve successfully through the stacking meta-learner adapter.
