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

## DEC-0012 - Runtime Scoring Loads A Manifest Bundle When Available And A Direct Model Fallback During Scaffold

- Status: accepted
- Date: 2026-05-13
- Owner: Codex
- Context: The PRD and deployment docs require a production manifest bundle at backend startup, but the current milestone only has baseline and classical model artifacts plus a shared preprocessor. The backend still needs a usable scoring stub before the final serving bundle exists.
- Decision: Implement runtime artifact loading in two layers: prefer the production manifest bundle when it exists, but allow a temporary direct runtime model path override for local scoring stubs until the full production artifact set is available.
- Consequences: Backend startup and health logic can be built now without blocking on the future ensemble manifest. The scoring stub remains model-agnostic, but temporary fallback behavior must be documented so it is not mistaken for the final production serving contract.
- Follow-ups: Add FastAPI startup caching and `/api/health` plus `/api/score` route stubs next, then retire the fallback path once the calibrated production bundle is promoted.

## DEC-0013 - Use A Bounded Counterfactual Fallback Until The Persisted DICE Artifact Exists

- Status: superseded
- Date: 2026-05-14
- Owner: Codex
- Context: The checked-in bundle now has a valid persisted SHAP explainer, but `models/explainers/dice_explainer.pkl` is still missing. Leaving `/api/score` counterfactual fields empty overstates implementation progress and weakens runtime smoke coverage, while blocking all actions on full DICE integration would stall repository-integrity remediation.
- Decision: Keep DICE-ML as the target production counterfactual interface, but use a bounded runtime fallback in the current score service that simulates documented actionable feature adjustments against the loaded model and returns only improving or probability-strengthening suggestions.
- Consequences: The checked-in bundle now returns non-empty score-response action fields without pretending a DICE artifact exists. Current fallback actions must stay clearly documented as interim behavior, and they do not satisfy the final DICE acceptance gate.
- Follow-ups: Completed as an interim mitigation and superseded by DEC-0014 once the checked-in bundle gained a validated persisted counterfactual artifact.

## DEC-0014 - Track A Curated Local Runtime Bundle And Persist The Counterfactual Artifact Contract

- Status: accepted
- Date: 2026-05-14
- Owner: Codex
- Context: The repository needed a portable runtime bundle that could be validated directly in smoke tests, but the default local environment did not include a production manifest or a preexisting persisted counterfactual artifact. Keeping the runtime bundle ignored in Git hid regressions, and overclaiming a third-party `dice_ml` object would have been inaccurate for the current logistic stub bundle.
- Decision: Intentionally source-control a small curated local runtime bundle under `models/` for backend portability and smoke coverage, and implement `models/explainers/dice_explainer.pkl` as a validated persisted actionable-counterfactual contract loaded from repository source rather than as an opaque third-party object.
- Consequences: Fresh clones can now validate the real local serving assets directly, `/api/health` can report `ok` for the checked-in bundle, and `/api/score` no longer depends on a non-persisted counterfactual fallback in the default path. Heavy future training outputs still remain ignored by default, and a richer production-model-specific counterfactual artifact can supersede this contract later if needed.
- Follow-ups: The first manifest-backed local serving bundle is now frozen. Next decide whether future production bundles should retain this lightweight persisted contract or migrate to a fuller `dice_ml`-backed artifact.

## DEC-0015 - Default Local Serving Now Uses A Checksum-Verified Manifest Bundle

- Status: accepted
- Date: 2026-05-14
- Owner: Codex
- Context: The repository already had a curated checked-in runtime artifact set, but backend startup still relied on candidate selection or explicit direct-model overrides by default. That kept serving behavior ambiguous and made it too easy for a copied or partially edited bundle to drift away from what health/readiness claimed to be loading.
- Decision: Freeze the checked-in local serving bundle behind `models/registry/production_manifest.json`, require an explicit manifest contract for the runtime model, preprocessor, text PCA, SHAP explainer, DICE explainer, metrics, baseline metrics, fairness report, PSI report, global-importance report, and population-percentiles artifact set, and verify SHA256 checksums for manifest-backed artifacts during startup loading.
- Consequences: Default local backend startup is now deterministic and visibly manifest-backed in `/api/health`, copied or tampered bundles surface as invalid instead of silently drifting, and direct runtime-model loading remains available only as an explicit dev/test override rather than the repository default.
- Follow-ups: Extend the governance reports with calibration parity and the individual-fairness proxy, then later replace the current logistic manifest bundle with a calibrated ensemble bundle once the offline model track is ready.
