# AlterScore: Frontend UX Strategy

This document defines the client UX strategy for AlterScore, mapping user journeys, cognitive constraints, and interface guidelines to cultivate trust, clarity, and agency.

---

## 1. Persona Experience Matrix

AlterScore addresses four distinct user groups, each requiring different presentation layers:

| Persona | Primary Goal | Emotional State | UX Focus |
| :--- | :--- | :--- | :--- |
| **1. Credit Applicant** | Understand eligibility, view credit score, learn how to improve. | Anxious, cautious, seeking respect and transparency. | Clear plain-language interface, interactive counterfactual simulator, progressive disclosure. |
| **2. Risk Evaluator** | Monitor applicant scoring patterns, check model integrity. | Analytical, compliance-oriented, focused on risk limits. | Density-optimized dashboard, Recharts visualizations, clear feature sorting. |
| **3. Compliance Auditor** | Verify ethical lending compliance, check subgroup disparities. | Skeptical, detail-oriented, auditing fairness models. | Disparate impact subgroups breakdown tables, manifest hashes, immutable metadata. |
| **4. Demo Presenter** | Demonstrate platform capabilities in real-time presentations. | Focused on clarity, speed, and visual appeal. | Clean navigation, instant preset triggers, responsive UI updates. |

---

## 2. Journey Mapping & Emotional Milestones

```
   [ Landing / Opt-In ]          [ Assessment ]          [ Processing / Audits ]         [ Reveal & Agency ]
     Transparency &            Pacing, Focus, &           Fairness Validation &           Credit Score Reveal,
     Privacy Consent            Clear Instructions           System Tickers               Explainers, & Boosters
```

### Milestone A: Landing & Privacy Opt-in
* **Applicant Emotion**: Skepticism regarding digital telemetry and how data will be used.
* **UX Strategy**: Display a clear, plain-language disclosure statement. Require explicit consent before tracking keyboard or scrolling behavior. Reassure the user that their data is protected.

### Milestone B: Guided Assessment
* **Applicant Emotion**: Fatigue and confusion over math/logic puzzles.
* **UX Strategy**: Focus attention on one question at a time using elegant slide animations. Provide helpful context hints on difficult CRT questions to reduce cognitive strain. Give clear writing suggestions for the open-text resilience question.

### Milestone C: Score Revealing
* **Applicant Emotion**: Anxiety about the decision and risk band.
* **UX Strategy**: Animate the score counter from 300 to the calculated score. Color-code the risk band immediately using intuitive green-to-red stops. Position the rating within a clear percentile bracket to provide relative context.

### Milestone D: Explainability & Actionable Boosters
* **Applicant Emotion**: Frustration or confusion (if rejected/Fair) or excitement (if Excellent).
* **UX Strategy**: Present SHAP factors in a plain-language list. Use checkboxes on the **Interactive Booster Simulator** so they can select habits and immediately see their potential score increase, giving them a clear path forward.

---

## 3. Cognitive Load & Abandonment Mitigation

* **Progressive Disclosure**: Keep technical feature details hidden by default. Allow users to expand specific SHAP rows to view underlying mathematical coefficients or governance notes.
* **Pacing Buffers**: Build in smooth GSAP card-sliding transitions. Avoid immediate automatic transitions on text entries, allowing users to review their input before clicking "Continue."
* **Plain Language Mapping**: Translate model feature names into user-friendly terms:
  * `numeracy_score` $\rightarrow$ **Financial Math Accuracy**
  * `future_orientation` $\rightarrow$ **Long-term Planning Habit**
  * `locus_of_control` $\rightarrow$ **Personal Accountability**
  * `social_capital_score` $\rightarrow$ **Community Support Network**
