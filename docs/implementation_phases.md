# AlterScore: Implementation Phases & Task Checklist

This document structures the AlterScore frontend roadmap into six development phases (A through F), scoring task complexity, establishing dependencies, and detailing product impacts.

---

## Phase A: Core Product UX (Onboarding & Pacing)

* **Objective**: Re-architect base routing, integrate unified state management, and introduce tracking safety metrics.
* **Complexity**: Medium.
* **Dependencies**: None.

| Task Description | Complexity | Demo Value | UX Impact | Trust Impact |
| :--- | :---: | :---: | :---: | :---: |
| **1. Create `AssessmentContext`**<br>Refactor state from local variables to global Context. | Low | Low | Medium | High |
| **2. Build Privacy Opt-In Modal**<br>Collect explicit consent before starting telemetry. | Low | Medium | Low | Critical |
| **3. Implement `useTelemetry` Hooks**<br>Track page visibility focus, scroll direction changes, and input changes. | Medium | Low | Low | High |
| **4. Smooth Card Transitions**<br>Integrate GSAP card slide-ins. | Low | High | High | Medium |

* **Verification**: Verify that telemetry payloads match Pydantic constraints and prevent API 422 errors.

---

## Phase B: Results & Explainability UX

* **Objective**: Build a premium, educational credit score reveal screen.
* **Complexity**: Medium.
* **Dependencies**: Phase A.

| Task Description | Complexity | Demo Value | UX Impact | Trust Impact |
| :--- | :---: | :---: | :---: | :---: |
| **1. Score Reveal Animation**<br>Animate score counter digit increments with HSL gradients. | Low | High | Critical | Medium |
| **2. Human-Centric SHAP Bars**<br>Replace float numbers with plain-language impact bars. | Medium | High | Critical | High |
| **3. Counterfactual Simulator**<br>Enable interactive checks to calculate simulated points gains. | Medium | Critical | Critical | Critical |

* **Verification**: Compositions render cleanly on mobile viewport sizes without text truncation.

---

## Phase C: Governance & Transparency UX

* **Objective**: Integrate compliance indicators, manifest footprints, and explain model constraints.
* **Complexity**: Low.
* **Dependencies**: Phase B.

| Task Description | Complexity | Demo Value | UX Impact | Trust Impact |
| :--- | :---: | :---: | :---: | :---: |
| **1. Monotonic Constraint Lock**<br>Expose active monotonicity tags on SHAP feature drawers. | Low | Medium | Medium | Critical |
| **2. Verifiable Manifest Footprint**<br>Display SHA-256 model hashes on all result exports. | Low | Low | Low | High |
| **3. Plain Language AI Policy**<br>Create a responsible AI policy modal link in footer. | Low | Low | Medium | High |

* **Verification**: Verify that model hash values match backend metadata manifests exactly.

---

## Phase D: Dashboard & Risk Center HUD

* **Objective**: Build the risk manager HUD to monitor model performance, drift, and subgroup fairness.
* **Complexity**: High.
* **Dependencies**: Phase A.

| Task Description | Complexity | Demo Value | UX Impact | Trust Impact |
| :--- | :---: | :---: | :---: | :---: |
| **1. Subgroup Fairness Table**<br>List disparate impact comparisons and group AUC levels. | Medium | High | Medium | Critical |
| **2. Feature PSI Drift Table**<br>Color-code drift indicators using Stable/Watch thresholds. | Medium | Medium | Low | High |
| **3. Recharts Curve Fitting**<br>Plot ROC, PR, and Calibration curves with tooltips. | High | Critical | High | High |
| **4. Pacing Anomaly Highlights**<br>Flag profiles with fast pasting or under-1000ms clicks. | Medium | High | Low | High |

* **Verification**: Recharts curves match reference JSON coordinate matrices successfully.

---

## Phase E: Frontend Engineering Cleanup

* **Objective**: Remove styling duplicates, enforce clean data type checks, and handle offline fallbacks.
* **Complexity**: Medium.
* **Dependencies**: Phase C, Phase D.

| Task Description | Complexity | Demo Value | UX Impact | Trust Impact |
| :--- | :---: | :---: | :---: | :---: |
| **1. CSS Refactoring**<br>Consolidate custom CSS tokens, clean up duplicated properties. | Medium | Low | Medium | Low |
| **2. Error Boundaries lock**<br>Isolate chart rendering errors to avoid crashing layout shells. | Low | Low | High | Medium |
| **3. Preset Profiles Selector**<br>Add UI controls to inject test profiles easily during audits. | Low | High | Medium | Low |

* **Verification**: Audit index.css to verify all spacing uses design-system scale variables.

---

## Phase F: Visual Polish & Micro-interactions

* **Objective**: Elevate the UI atmosphere with premium animations and responsive highlights.
* **Complexity**: Low.
* **Dependencies**: Phase B, Phase D.

| Task Description | Complexity | Demo Value | UX Impact | Trust Impact |
| :--- | :---: | :---: | :---: | :---: |
| **1. Ambient Lighting vignette**<br>Integrate radial vignettes following mouse positions on screen. | Low | High | Medium | Low |
| **2. Magnetic Controls**<br>Apply magnetic physics adjustments to main CTA actions. | Low | High | High | Low |
| **3. Hover Border transitions**<br>Add smooth CSS glow indicators to active panels. | Low | Medium | High | Medium |

* **Verification**: Confirm layout animations maintain steady 60 FPS speeds on mobile clients.
