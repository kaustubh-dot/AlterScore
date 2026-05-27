# AlterScore: Results Page Strategy

This document details the visual design, interactive features, and layout hierarchy for the AlterScore Results screen—the core user-facing touchpoint.

---

## 1. Visual Hierarchy & Progressive Disclosure

The Results screen uses a top-down information hierarchy to manage cognitive load:

```
+-------------------------------------------------------------+
| 1. The Score Reveal (Gauge Arc & Large Score: 300 - 850)     |
|    - Shows Risk Band (e.g. "Good") and Percentile Context    |
+-------------------------------------------------------------+
| 2. SHAP Impact Bars (Factors Influencing Your Score)        |
|    - Expandable rows for plain-language detail drawers      |
+-------------------------------------------------------------+
| 3. Interactive Counterfactual Booster Simulator             |
|    - Selectable checkboxes to simulate score improvement     |
+-------------------------------------------------------------+
| 4. Loan Eligibility Range & Specific Improvement Tips        |
|    - Approved loan bounds & basic financial coaching cards   |
+-------------------------------------------------------------+
| 5. Action Bar (PDF Certificate Export, Share Result)        |
+-------------------------------------------------------------+
```

---

## 2. The Score Reveal & Color-Token System

### Reveal Animation Flow (GSAP-powered)
1. **Sweep**: A high-speed scanning line sweeps horizontally across the interface.
2. **Count**: The credit score digits count rapidly upward from `300` to the final score over 2.0 seconds with a smooth ease-out curve.
3. **Fade**: Detailed panels (SHAP, counterfactuals) fade in sequentially with a stagger delay of `0.12s`.

### Curated Color Stops
To avoid harsh default colors, we map the credit score to a smooth gradient interpolation system:
* **Poor** ($300 - 549$): Coral/Red (`rgb(255, 77, 77)`)
* **Fair** ($550 - 649$): Orange/Yellow (`rgb(255, 154, 60)`)
* **Good** ($650 - 749$): Aquamarine/Teal (`rgb(61, 255, 200)`)
* **Excellent** ($750 - 850$): Lavender/Indigo (`rgb(167, 139, 255)`)

---

## 3. Human-Centric SHAP Impact Visualizer

The SHAP visualizer replaces raw mathematical values with plain-language, color-coded bars:
* **Direction Indicators**: Features that supported the score show green badges (`+ 0.45`); features that pulled it down show coral/red badges (`- 0.12`).
* **Progressive Detail Drawers**: Clicking on any feature row expands a detailed drawer containing:
  * The underlying technical feature key (e.g., `locus_of_control`).
  * The raw SHAP influence coefficient.
  * A clear explanation of the mathematical constraints (e.g., monotonicity locking).

---

## 4. Interactive Counterfactual Booster Simulator

The counterfactual card container in [CounterfactualCards.jsx](file:///c:/Kaustubh/Projects/AlterScore/frontend/src/components/results/CounterfactualCards.jsx) acts as a simulator:
* **Habit Checkboxes**: Each recommended habit (e.g., *"Wait longer for better outcomes to show future planning"*) is presented as a card with an estimated points gain (e.g., `+18 POINTS`).
* **Live Score Accumulator**: When the applicant checks a card, the header updates dynamically with a pulsing animation: `SIMULATED GAIN: +18 PTS`. This gives applicants agency and control over their financial path.

---

## 5. Share and Verifiable Export

* ** verifiably Signed Certificate**: The "Download Certificate" action uses `html2canvas` to render the certificate card into a clean image.
* **Metadata Footprint**: The image footer contains the unique `session_id`, the timestamp, and the locked model version, allowing bank officials to verify the assessment hash.
