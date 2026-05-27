# AlterScore: Governance & Trust UX Strategy

This document defines how fairness, monotonic constraints, responsible AI guidelines, and behavioral telemetry are communicated to applicants and evaluators to ensure transparency and trust.

---

## 1. Monotonicity as a Trust Multiplier

Unlike traditional ML models that suffer from unpredictable feedback loops, AlterScore uses monotonic XGBoost models. This is a core selling point that should be highlighted on the Results page:
* **The "No Arbitrary Penalty" Lock**: If an applicant improves a specific behavioral habit (e.g. keeping expense records or answering more patient options), their score is mathematically guaranteed **not to drop**.
* **Visualizing Monotonicity**:
  * On SHAP explanation detail panels, state explicitly: *"Monotonic Constraint Lock: Active. Improving this habit is locked to only benefit your overall credit health."*
  * On counterfactual cards, frame actions as positive boosters (e.g., `+25 PTS`) that are mathematically protected from negative interactions.

---

## 2. Telemetry Transparency & Disclosure

Behavioral telemetry is a sensitive data category. AlterScore must maintain absolute transparency regarding what is captured:

### The Consent Overlay (Telemetry Opt-In)
Before any tracking events initialize, the user must view and accept the Telemetry Agreement:
1. **Explain the 'Why'**: Telemetry (like pacing and response focus) is used to verify application authenticity and prevent identity theft, bypassing traditional credit bureaus.
2. **Explicit Disclosures**:
   * *We track*: Time spent per question card, choice modifications, and page focus shifts.
   * *We DO NOT track*: Keystrokes on math inputs, personal passwords, or camera feeds.
3. **Opt-Out Control**: If a user opts out, telemetry features default to neutral placeholders, and the scoring logic operates purely on questionnaire answers.

---

## 3. Explaining Subgroup Fairness (Auditor View)

To build institution-grade credibility, the platform exposes fairness indicators:
* **The Worst AUC Gap**: Shows the difference in model accuracy between protected subgroups (e.g., gender, age, rural-vs-urban location proxies). The UI displays a prominent green **"PASS"** label if this gap remains below the governance threshold ($<5\%$).
* **Approval Rate Parity**: Visualizes the proportion of approvals across subgroups to confirm that the model does not introduce systemic bias against vulnerable populations.

---

## 4. Manifest Signatures & Model Lock

To prove that scoring outcomes are reproducible and audited:
* **Verifiable Manifest Hashes**: The top HUD banner on all dashboards and print views exposes the active model's manifest version (e.g., `manifest_v2.1.0-prod` with its SHA-256 hash).
* **Audit Trail Registry**: A dedicated tab logs the exact date, time, and server version used to compile the score, proving that no ad-hoc changes can be made to score logic during an active evaluation window.
