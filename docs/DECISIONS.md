# AlterScore Architecture Decisions

## How To Use This File

Record every architecture-level decision here. Small implementation choices can live in code comments or pull request notes, but anything that affects project structure, data schema, model behavior, API contract, deployment, or testing policy belongs here.

## Decision Template

```markdown
## DEC-XXXX - Title

- Status: proposed | accepted | superseded
- Date: YYYY-MM-DD
- Owner: name or AI session
- Context:
- Decision:
- Consequences:
- Follow-ups:
```

## DEC-0001 - Local NLP Instead Of External LLM API

- Status: accepted
- Date: 2026-05-13
- Owner: PRD
- Context: The PRD explicitly disallows requiring an external LLM API. NLP must be auditable and runnable locally.
- Decision: Use sentence-transformers, VADER, and spaCy for Q27 text features.
- Consequences: No API key is needed. Semantic richness is limited compared with hosted LLMs, but interpretability and reproducibility improve.
- Follow-ups: Pin model names and document local model download behavior.

## DEC-0002 - FastAPI Backend With Pydantic Contracts

- Status: accepted
- Date: 2026-05-13
- Owner: PRD
- Context: The backend must expose scoring and analytics endpoints with strict validation.
- Decision: Use FastAPI and Pydantic v2 schemas for all request and response contracts.
- Consequences: Runtime validation becomes explicit and API tests can target schema behavior.
- Follow-ups: Implement schemas before route business logic.

## DEC-0003 - React Frontend With Separate Assessment, Results, And Dashboard Workflows

- Status: accepted
- Date: 2026-05-13
- Owner: PRD
- Context: The user experience includes borrower assessment and evaluator analytics.
- Decision: Use React pages for Landing, Assessment, Results, and Dashboard.
- Consequences: Assessment telemetry and dashboard analytics remain separate concerns.
- Follow-ups: Build dashboard only after analytics endpoints stabilize.

## DEC-0004 - Temporal Split Is The Final Validation Strategy

- Status: accepted
- Date: 2026-05-13
- Owner: PRD
- Context: The model must demonstrate generalization to future cohorts.
- Decision: Use months 1-8 for training, months 9-10 for validation/calibration, and months 11-12 for final testing.
- Consequences: Random split metrics are not sufficient for final acceptance.
- Follow-ups: Add tests that `cohort_month` and `application_date` never enter model inputs.

## DEC-0005 - Production Model Is A Calibrated Stacking Ensemble

- Status: accepted
- Date: 2026-05-13
- Owner: PRD
- Context: The PRD requires logistic regression, RF, XGBoost, LightGBM, TabNet, MLP, and stacking.
- Decision: Promote an isotonic-calibrated stacking ensemble as the production model if it clears acceptance gates.
- Consequences: Training is more complex, but the dashboard can demonstrate ensemble lift over simpler baselines and simulated loan officer behavior.
- Follow-ups: Keep baseline and individual model metrics available for comparison.

## DEC-0006 - Protected Attributes Are Audit-Only

- Status: accepted
- Date: 2026-05-13
- Owner: PRD
- Context: Fairness must be measured without using demographic attributes as model inputs.
- Decision: Store gender, age group, region, and education level separately from model feature arrays.
- Consequences: Training and inference code must have explicit safeguards.
- Follow-ups: Add tests ensuring protected fields are absent from `NUMERIC_FEATURES`, `CATEGORICAL_FEATURES`, and runtime feature dataframes.

## DEC-0007 - SHAP And DICE Are Required Explainability Interfaces

- Status: accepted
- Date: 2026-05-13
- Owner: PRD
- Context: Borrower results must include explanations and improvement actions.
- Decision: Use SHAP for feature contribution explanations and DICE-ML for actionable counterfactuals.
- Consequences: Explanation artifacts become required production dependencies.
- Follow-ups: Define actionable and immutable feature lists before DICE implementation.

## DEC-0008 - PSI Is The Drift Metric For The Dashboard

- Status: accepted
- Date: 2026-05-13
- Owner: PRD
- Context: Evaluators need a lightweight stability signal.
- Decision: Use Population Stability Index between training months and future test cohorts.
- Consequences: PSI can be generated offline and served from JSON.
- Follow-ups: Document thresholds: stable below 0.20, watch 0.20-0.30, alert above 0.30.

## DEC-0009 - Artifact Bundles Are Separated From Source Code

- Status: accepted
- Date: 2026-05-13
- Owner: Engineering scaffold
- Context: Generated data and trained binaries should not pollute source history.
- Decision: Store generated datasets under `data/` and artifacts under `models/`; ignore heavy outputs by default.
- Consequences: Deployment must explicitly package required artifacts.
- Follow-ups: Add `.gitignore` before generating data or training.

## DEC-0010 - Public API Remains PRD-Compatible

- Status: accepted
- Date: 2026-05-13
- Owner: Engineering scaffold
- Context: The PRD names public endpoints under `/api/*`, while scalable code organization benefits from internal versioning.
- Decision: Organize backend route modules under `api/v1` internally, while preserving PRD-compatible public paths unless a breaking version decision is made.
- Consequences: Frontend and tests can follow the PRD contracts.
- Follow-ups: If `/api/v1/*` becomes public, document backward compatibility or migration.

## DEC-0011 - Use 35 Explicitly Named Model Inputs

- Status: accepted
- Date: 2026-05-13
- Owner: User direction and engineering scaffold
- Context: The PRD states 39 model features, but the explicit feature list names 35 model input columns when categorical columns are included.
- Decision: Use the 35 explicitly named model inputs as the canonical implementation feature set: 33 numeric and 2 categorical features. Do not invent four additional psychometric features.
- Consequences: Data generation, preprocessing, inference, SHAP, DICE, dashboard feature importance, and tests must target 35 model inputs. Documentation should describe the earlier 39-feature PRD narrative as superseded by the explicit named registry.
- Follow-ups: Implement `feature_registry.py` with exactly these named inputs and tests for count, ordering, and protected/temporal exclusions.
