# API contracts

AlterScore is a synthetic, answer-based Financial Decision Readiness
demonstration. It is not a lender, credit bureau, underwriting service,
repayment predictor, approval system, or source of financial offers.

## Public runtime endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/api/live` | Artifact-independent process liveness. |
| `GET` | `/api/health` | Temporary liveness-compatible probe for existing monitors. |
| `GET` | `/api/ready` | v2 readiness with six serving checks. |
| `GET` | `/api/v2/assessment/form` | Issue one anonymous, single-use assessment form. |
| `POST` | `/api/v2/assessment/score` | Score an issued form over HTTPS. |
| `GET` | `/api/v2/results/verify/{result_id}` | Verify the redacted signed result projection. |
| `POST` | `/api/score` | Retired model-backed route; always `410 Gone`. |
| `POST` | `/api/debug-score` | Retired model-backed debug route; always `410 Gone`. |

There is no `/api/v1/score` compatibility alias. The former analytics paths
are not registered and return `404`; research material cannot affect public
results.

## Frozen versions

Successful v2 form, score, readiness, liveness, and verification responses use:

```text
contract_version: 2.0
assessment_version: india-en-3.0.0
scoring_policy_version: readiness-rubric-1.0.0
```

The public contract is defined by the Pydantic models in
`backend/app/api/v2/models.py`. Extra fields are forbidden. Forms contain
server-issued opaque item and option identifiers; answer keys, generation
rules, branch transition constants, and rubrics are never issued.

## Transport and lifecycle

`GET /api/v2/assessment/form` requires a trusted HTTPS ASGI scheme and returns
an opaque `attempt_token`. The token is accepted only as a bearer header on the
matching score request. Attempts are single-use and expire after the frozen
server TTL. The score response is signed and kept in a bounded in-memory
verification store for the frozen 24-hour result lifetime.

The frontend may retain a bounded detailed display projection in
`sessionStorage` for that result lifetime. It never stores the bearer token,
raw submission map, or narrative in persistent storage. Verification returns
only the redacted signed projection, never worked evidence or behavior values.

## Public score

The successful score response contains:

- `financial_decision_index`, an integer from 0 through 100;
- `legacy_demo_score`, an illustrative integer from 300 through 850;
- decimal-2 `objective_score` and `judgment_score` display values;
- `behavior_profile`, which is unscored self-reflection;
- `limitations`, integrity metadata, signature, explanation digest, and the
  frozen public `explanation` object.

The explanation reconciles the exact objective and judgment contributions,
worked evidence for all eight objective concepts, principle-level records for
four static judgment items, two branching replays with state deltas and
terminal dimensions, and evidence-linked maintenance/recommendation guidance.

The scorer must not return repayment probability, synthetic percentile, risk
band, approval, eligibility, pricing, loan amount, SHAP attribution, or a
complete hidden rubric.
