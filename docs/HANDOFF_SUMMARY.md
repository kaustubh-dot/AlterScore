# Handoff Summary: Backend Freeze & Frontend Transition

**Date:** May 2026
**Target Audience:** Frontend/Full-Stack Developer taking over the project.

## 1. Backend Status: FROZEN

The backend architecture, API endpoints, machine learning models, explainability tools (SHAP/DICE), and artifact management systems are now **FROZEN**.

The backend operates on a Calibrated Stacking Ensemble runtime with 35 predefined features. Do not attempt to add features, retrain models, or modify `production_manifest.json` without rigorous review.

## 2. API Contracts

The API is fully ready for integration. Refer to `API_CONTRACTS.md` for schemas.

Key endpoints for the Frontend:
*   `POST /api/score` - The main borrower assessment endpoint. Submit answers, receive a score (300-850), SHAP explanations, and DICE counterfactuals.
*   `GET /api/health` - Use this to verify the backend is running and the models are fully loaded before allowing users to take the assessment.
*   `GET /api/fairness-report`, `GET /api/drift-report`, etc. - For the analytics dashboard.

## 3. Explainability

We provide two forms of explainability in the `/api/score` response:
1.  **SHAP (Global/Local Importance):** Returns the top 6 factors that influenced the score. Use these to display "What drove your score?"
2.  **DICE (Counterfactual Actions):** Returns 2-3 actionable steps the applicant can take to improve their tier. Display these as "How to improve your score."

## 4. Frontend Expectations

For Track E (Frontend), your primary focus should be:
*   Building a premium, dynamic, and accessible UI.
*   Implementing the 27-question assessment flow logically and beautifully.
*   Rendering the `ScoreResponse` payload into an intuitive Results Dashboard.
*   Integrating the analytics endpoints into a Model Governance Dashboard.

The backend is fully unblocked and ready for your requests.
