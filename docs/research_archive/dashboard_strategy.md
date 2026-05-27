# AlterScore: Evaluator Dashboard Strategy

This document defines the interface layout, charting specifications, and analytical monitoring systems for the AlterScore Model Governance Center & Evaluator HUD.

---

## 1. Information Hierarchy & Tab Structure

The Evaluator HUD, implemented in [Dashboard.jsx](file:///c:/Kaustubh/Projects/AlterScore/frontend/src/pages/Dashboard.jsx), is structured into four primary diagnostics views:

```
+--------------------------------------------------------------------------------+
| HUD Header: Server Health | manifest_version | locked model version            |
+--------------------------------------------------------------------------------+
| TAB SELECTOR: [ Performance ]  [ Drift Monitoring ]  [ Fairness Audit ]  [ Logs ]|
+--------------------------------------------------------------------------------+
| PERFORMANCE:                         | DRIFT MONITORING:                       |
| - ROC, PR, Calibration Curves        | - Feature table with PSI metrics        |
| - Score Distribution Histogram       | - Stable / Watch / Action alerts        |
+--------------------------------------------------------------------------------+
| FAIRNESS AUDIT:                      | LOGS / AUDIT TRAIL:                     |
| - Disparity metrics per proxy group  | - Immutable session logs                |
| - Subgroup AUC and approval rates    | - Scoring manifest registry             |
+--------------------------------------------------------------------------------+
```

---

## 2. Diagnostics Charting Specification (Recharts)

To maintain a clean, research-grade appearance, all charts use unified color variables (`var(--accent)` for main data series, `var(--accent-purple)` for baseline comparisons) and dark backgrounds:

### Receiver Operating Characteristic (ROC) & Precision-Recall (PR) Curves
* **Plot Component**: Built as a reusable `<CurvePlot>` utilizing SVG-based line series.
* **Fittings**: X-axis and Y-axis bounds are locked strictly to the `[0, 1]` probability range.
* **Tooltips**: Display floating precision hover values format (`value.toFixed(4)`) in custom-styled CSS containers matching the theme.

### Expected Calibration Curve
* **Utility**: Diagnostic tool to verify that predicted default probabilities align with actual historical subgroup defaults.
* **UX Treatment**: Plots actual class frequencies against mean predicted probability buckets. Perfect calibration is represented by a dotted gray diagonal line.

### Score Distribution Histogram
* **Utility**: Visualizes the density of credit scores across the applicant population.
* **UX Treatment**: Renders score ranges in 10-point buckets. Highlights the average and median scores using a subtle dashed indicator.

---

## 3. Drift & Feature Stability Monitoring

The **Drift Monitoring** view renders features in a dense, sorted data table matching strict threshold rules:

| PSI Value Range | Metric Status | UI Badge | Warning Level |
| :--- | :--- | :--- | :--- |
| **$\text{PSI} < 0.10$** | Stable | **STABLE** (Green) | Normal system monitoring. |
| **$0.10 \le \text{PSI} < 0.25$** | Moderate Shift | **WATCH** (Yellow) | Alert analyst for potential drift in text or risk responses. |
| **$\text{PSI} \ge 0.25$** | High Drift | **ACTION** (Red) | Trigger alert badge in main HUD banner. Model recalibration recommended. |

---

## 4. Subgroup Fairness & Disparity Breakdown

The **Fairness Audit** tab lists protected subgroup attributes (e.g. gender, rural-vs-urban locations proxy features) to monitor algorithmic bias:
* **Worst AUC Gap**: Exposes the disparity between the highest-performing subgroup and the lowest-performing subgroup.
* **Approval Rate Parity**: Displays the percentage of approvals per group. Large gaps are highlighted in yellow to notify the auditor of potential disparate impact risks.
* **Parity Verdict**: A summary alert displays **"FAIR"** (worst gap $<5\%$) or **"WARNING"** (worst gap $\ge 5\%$) based on audit guidelines.
