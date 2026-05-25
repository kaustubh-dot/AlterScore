# Monotonic Tree Governed Comparison

## Summary

The constrained-tree production track completed its first full governed
comparison run at `10,000` synthetic rows using
[scripts/train_monotonic_tree_candidates.py](C:/Kaustubh/Projects/AlterScore/scripts/train_monotonic_tree_candidates.py).

Primary outcome:

- `xgboost_monotonic` is the first constrained-tree candidate to clear the
  current promotion gate stack in this governed track
- `lightgbm_monotonic` remains blocked by fairness findings
- the current production ensemble baseline underperforms both constrained-tree
  candidates on discrimination and calibration
- research TabNet remains behaviorally less stable than the constrained-tree
  candidates despite competitive aggregate AUC

Full report artifact:

- [runtime/governed_reports/monotonic_tree_candidates/full/monotonic_tree_candidate_report.json](C:/Kaustubh/Projects/AlterScore/runtime/governed_reports/monotonic_tree_candidates/full/monotonic_tree_candidate_report.json)

## Governed Comparison

### Current Runtime Ensemble

- test AUC: `0.7242`
- Brier: `0.1939`
- ECE: `0.0998`

### Research TabNet Baseline

- test AUC: `0.7462`
- Brier: `0.1760`
- ECE: `0.0661`
- fairness gate: passed
- monotonic acceptance gate: failed
- counterfactual gate: failed

Counterfactual violation summary:

- `resilience_score`: violation rate `0.1667`, worst delta `-0.0834`
- `future_orientation`: violation rate `0.1771`, worst delta `-0.0697`
- `numeracy_score`: violation rate `0.1250`, worst delta `-0.0511`
- `scroll_hesitation_score`: violation rate `0.3542`, worst delta `-0.2339`
- `text_agency_score`: violation rate `0.1563`, worst delta `-0.0908`

Interpretation:

- TabNet still shows the same governance failure mode identified earlier
- aggregate ranking is acceptable, but local behavioral stability remains
  unsuitable for the primary trusted production path

### Monotonic XGBoost

- test AUC: `0.8090`
- Brier: `0.1496`
- ECE: `0.0207`
- fairness gate: passed
- monotonic acceptance gate: passed
- counterfactual gate: passed
- promotion eligible: `true`

Counterfactual audit:

- all monitored features passed with `0.0` violation rate and `0.0` worst delta

Fairness summary:

- worst AUC gap: `0.0379`
- flagged groups: none

Important note:

- calibration parity still shows a meaningful ECE gap for `gender=non_binary`
  at small sample count (`n=57`), even though the subgroup AUC gap remains under
  the fairness flag threshold

Top modeled drivers:

- `session_duration_sec`
- `answer_change_rate`
- `conscientiousness_score`
- `scroll_hesitation_score`
- `numeracy_score`

### Monotonic LightGBM

- test AUC: `0.8036`
- Brier: `0.1531`
- ECE: `0.0454`
- fairness gate: failed
- monotonic acceptance gate: passed
- counterfactual gate: passed
- promotion eligible: `false`

Fairness blocker:

- `gender=non_binary`
- subgroup AUC gap from overall: `0.0594`
- subgroup ECE: `0.1377`

Interpretation:

- LightGBM is competitive on aggregate metrics and stability
- but it remains blocked by a subgroup fairness issue concentrated in the
  smallest gender subgroup

## Fairness Diagnostics

The strongest remaining fairness sensitivities for the production-track
XGBoost candidate are not broad AUC failures, but subgroup calibration and
proxy-feature concentration.

Observed proxy-risk concentrations for `gender=non_binary` include:

- `session_duration_sec`
- `financial_literacy_score`
- `numeracy_score`
- `avg_response_time_ms`
- `locus_of_control`

Observed proxy-risk concentrations for `education_level=none` include:

- `delay_discounting_rate`
- `future_orientation`
- `answer_change_rate`
- `risk_attitude`
- `resilience_score`

Interpretation:

- the candidate passes the current fairness gate, but fairness work is not done
- the next fairness hardening step should focus on subgroup calibration and
  proxy-sensitive behavioral features rather than reopening monotonic design

## Architectural Conclusion

This comparison supports the updated architecture direction:

- constrained monotonic tree systems are now the strongest production-track
  candidates
- governance-aware evaluation materially changes which models are trustworthy
- unconstrained high-capacity tabular neural models can still hide severe local
  behavioral failures behind acceptable aggregate AUC

## Next Recommended Step

That targeted fairness-hardening pass has now been completed in
[scripts/fairness_harden_xgboost_candidate.py](C:/Kaustubh/Projects/AlterScore/scripts/fairness_harden_xgboost_candidate.py)
with the detailed results recorded in
[docs/governance/XGBOOST_FAIRNESS_HARDENING_PROMOTION_REVIEW.md](C:/Kaustubh/Projects/AlterScore/docs/governance/XGBOOST_FAIRNESS_HARDENING_PROMOTION_REVIEW.md).

Current practical interpretation:

- `xgboost_monotonic` remains the governed constrained-tree choice and has
  since become the checked-in manifest runtime
- conservative fairness-hardening variants improved the `gender=non_binary`
  subgroup calibration gap somewhat
- however, the baseline raw `xgboost_monotonic` still remains the strongest
  production-safe operating point overall
