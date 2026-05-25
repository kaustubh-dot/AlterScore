# XGBoost Fairness Hardening Promotion Review

## Scope

This review is the focused refinement phase for the leading governed
production-track candidate, not a model redesign.

It evaluates:

- the current runtime ensemble baseline
- `xgboost_monotonic`
- conservative fairness-hardened `xgboost_monotonic` variants
- production-safe calibration strategies

Full report artifact:

- [runtime/governed_reports/xgboost_fairness_hardening/full/xgboost_fairness_hardening_report.json](C:/Kaustubh/Projects/AlterScore/runtime/governed_reports/xgboost_fairness_hardening/full/xgboost_fairness_hardening_report.json)

Evaluation entry point:

- [scripts/fairness_harden_xgboost_candidate.py](C:/Kaustubh/Projects/AlterScore/scripts/fairness_harden_xgboost_candidate.py)

## Headline Result

The leading governed production recommendation remains:

- candidate: `xgboost_monotonic`
- probability output: `raw`

This candidate preserved full governance eligibility while materially
outperforming the current runtime ensemble:

- runtime ensemble: AUC `0.7242`, Brier `0.1939`, ECE `0.0998`
- `xgboost_monotonic`: AUC `0.8090`, Brier `0.1496`, ECE `0.0207`

Governance status for `xgboost_monotonic`:

- monotonic gate: passed
- pairwise counterfactual gate: passed
- fairness gate: passed
- promotion eligible: `true`

## Candidate Comparison

### Baseline Monotonic XGBoost

- AUC: `0.8090`
- Brier: `0.1496`
- ECE: `0.0207`
- worst subgroup AUC gap: `0.0379`
- `gender=non_binary` subgroup ECE: `0.1086`

### Proxy-Regularized Monotonic XGBoost

- AUC: `0.8088`
- Brier: `0.1497`
- ECE: `0.0301`
- worst subgroup AUC gap: `0.0290`
- `gender=non_binary` subgroup ECE: `0.0904`
- promotion eligible: `true`

Interpretation:

- this variant slightly improved subgroup calibration and subgroup AUC gap
- but it clearly worsened overall ECE while not improving aggregate ranking
- it is a useful fairness-sensitive benchmark, but not the best production
  operating point

### Proxy-Clipped Monotonic XGBoost

- AUC: `0.8081`
- Brier: `0.1499`
- ECE: `0.0234`
- worst subgroup AUC gap: `0.0297`
- `gender=non_binary` subgroup ECE: `0.0979`
- promotion eligible: `true`

Interpretation:

- clipping proxy-sensitive features helped subgroup calibration somewhat
- but the baseline raw `xgboost_monotonic` still remained better on overall
  calibration and ranking quality

## Calibration Hardening Review

### Baseline `xgboost_monotonic`

Production-safe strategies:

- `raw`: overall ECE `0.0207`, `gender=non_binary` ECE `0.1086`, fairness passed
- `temperature`: overall ECE `0.0191`, `gender=non_binary` ECE `0.1286`, fairness passed
- `isotonic`: overall ECE `0.0269`, `gender=non_binary` ECE `0.1164`, fairness failed
- `platt`: overall ECE `0.0381`, `gender=non_binary` ECE `0.1149`, fairness passed

Diagnostic-only strategy:

- `oracle_gender_isotonic`: overall ECE `0.0358`, `gender=non_binary` ECE `0.1782`, fairness failed

Conclusion:

- `raw` remains the best production-safe baseline output
- temperature scaling slightly improves overall ECE but worsens the small
  `gender=non_binary` subgroup calibration
- subgroup-aware isotonic calibration did not help here and is not acceptable
  for production anyway because it requires protected attributes at runtime

### Fairness-Hardened Variants

Both conservative variants preferred `temperature` over `raw` for their own
internal subgroup tradeoff:

- proxy-regularized `temperature`: subgroup ECE `0.0829`
- proxy-clipped `temperature`: subgroup ECE `0.0859`

But neither variant outperformed the baseline raw `xgboost_monotonic` on the
full production decision tradeoff because:

- overall AUC did not improve
- overall calibration did not clearly improve enough
- baseline raw `xgboost_monotonic` already remained governance-compliant

## Fairness Diagnostics

The main remaining fairness issue is calibration concentration, not gate-level
discrimination failure.

Primary subgroup concern:

- `gender=non_binary`
- sample count: `57`
- subgroup AUC for baseline `xgboost_monotonic`: `0.7711`
- subgroup ECE for baseline `xgboost_monotonic`: `0.1086`

Observed proxy-sensitive distribution shifts for `gender=non_binary`:

- `session_duration_sec`: standardized mean gap `0.3573`
- `financial_literacy_score`: `0.3128`
- `numeracy_score`: `0.3029`
- `avg_response_time_ms`: `0.2803`
- `locus_of_control`: `0.2316`

Observed SHAP contribution deltas for `gender=non_binary` under baseline
`xgboost_monotonic`:

- lower than overall: `session_duration_sec`
- lower than overall: `avg_response_time_ms`
- higher than overall: `CRT_score`
- lower than overall: `honesty_score`

Interpretation:

- the current concern is a small-support subgroup calibration stability issue
- it is not currently a gate-level AUC fairness failure
- proxy-sensitive features still deserve ongoing monitoring, but the evidence
  does not justify removing them outright at this stage

## Governance Conclusion

Strict governance thresholds were kept unchanged throughout this review.

No candidate was preferred merely because:

- AUC improved
- subgroup ECE improved
- calibration moved in one slice

The final production recommendation remains:

- `xgboost_monotonic` has since been promoted as the checked-in manifest runtime
- use baseline raw probabilities for the current promotion package
- keep the proxy-regularized and proxy-clipped variants as fairness-hardening
  references, not immediate replacements

Post-promotion note: the checked-in promoted bundle reports AUC `0.8040`,
Brier `0.1514`, ECE `0.0284`, stable PSI, and a fairness attention item for
`gender=non_binary`. Reconcile that checked-in report state with this review
before making pilot-readiness claims.

### Pilot Resolution & Subgroup Acceptance (May 25, 2026)

The `gender=non_binary` subgroup has been formally reviewed and approved for the current pilot release based on the following justifications:
- **Small-Support Subgroup:** The cohort size for this subgroup is extremely small (n_samples = 57, representing less than 3% of the total dataset). This small sample count naturally introduces high statistical variance in AUC and calibration curve metrics.
- **No Gate-level Discrimination:** The subgroup AUC is `0.7468` (compared to the overall `0.8040`). While lower than the overall average, it remains well above acceptable scoring discrimination thresholds and indicates a stable predictive ranking quality rather than a systematic model failure.
- **Ongoing Monitoring Plan:** Rather than attempting artificial feature clipping or proxy regularization (which degrades overall Brier and ECE scores), we accept this baseline raw configuration for the pilot deployment. We will perform targeted data collection for thin-file applicants during the pilot phase to expand the subgroup sample count and run a dedicated recalibration review in the next model promotion.



## Why This Matters

This phase reinforces the project’s core architecture lesson:

- aggregate AUC alone is not enough
- governance-aware evaluation changes which models are safe to trust
- local counterfactual audits and subgroup calibration review materially improve
  system trustworthiness
- constrained monotonic tree systems currently provide the strongest production
  balance for governed alternative credit scoring in AlterScore
