# TabNet Monotonic Design Follow-Up

Date: 2026-05-22

## Scope

This follow-up did not promote any artifact. It extended the standalone TabNet
repair experiment with three guarded monotonicity levers:

- TabNet-only masking of brittle derived composites
- counterfactual curriculum augmentation rows
- a diagnostic monotonic post-processing baseline over critical features

The runtime TabNet disagreement mitigation remains enabled in production.

## Design Changes

The monotonic-design experiment is implemented in:

- `scripts/retrain_tabnet_repair_experiment.py`

The new controls are explicit and reversible:

- `--mask-features`
- `--curriculum-features`
- `--counterfactual-augmentation-repeats`
- `--counterfactual-step`
- `--counterfactual-max-violation-rate`
- `--counterfactual-max-worst-delta`
- `--postprocess-features`

Promotion now requires all of the following:

- anchor-style monotonic sensitivity gates
- metadata stability gate
- pairwise counterfactual acceptance gate

## Candidate Run

Run directory:

- `runtime/research_archive/tabnet_repair/monotonic/`

Training setup:

- TabNet capacity: `n_d=8`, `n_a=8`, `n_steps=2`, `gamma=1.0`
- Masked features:
  - `psychological_credit_index`
  - `repayment_intention_score`
  - `engagement_score`
  - `behavioral_trust_score`
- Counterfactual curriculum features:
  - `resilience_score`
  - `future_orientation`
  - `numeracy_score`
  - `scroll_hesitation_score`
- Curriculum rows added: `27,200`
- Base train rows: `6,800`

Follow-up targeted run:

- `runtime/research_archive/tabnet_repair/monotonic_targeted/`
- narrower hard-slice reinforcement with:
  - `targeted_counterfactual_step_grid = [0.04, 0.08]`
  - `targeted_strong_threshold = 0.8`
  - `targeted_low_hesitation_threshold = 0.2`

## Results

Raw candidate metrics on repaired labels:

- AUC: `0.7802`
- Brier: `0.1642`
- ECE: `0.0568`

The raw candidate improved local anchor sweeps enough to pass the original
monotonic acceptance gate:

- `acceptance_gates_passed: true`
- `metadata_stability_gate_passed: true`

However it still failed the stronger counterfactual gate:

- `promotion_eligible: false`
- `counterfactual_gate_passed: false`

## Why Promotion Is Still Blocked

Sampled counterfactual audit on 256 repaired test rows still found too many
pairwise violations where a favorable feature change reduced predicted repayment
probability.

Violation summary:

- `resilience_score`: violation rate `0.1328`, worst delta `-0.2238`
- `future_orientation`: violation rate `0.0391`, worst delta `-0.0739`
- `numeracy_score`: violation rate `0.0742`, worst delta `-0.1014`
- `scroll_hesitation_score`: violation rate `0.0820`, worst delta `-0.1004`

Current hard thresholds:

- max violation rate: `0.02`
- max worst delta magnitude: `0.05`

This means the candidate is smoother on a single anchor profile, but still not
stable enough across a broader local counterfactual surface.

## Follow-Up Targeted Iteration

The narrower targeted curriculum improved the pairwise counterfactual audit
materially while preserving the local monotonic sweep pass.

Targeted run metrics:

- AUC: `0.7694`
- Brier: `0.1717`
- ECE: `0.0819`
- `acceptance_gates_passed: true`
- `metadata_stability_gate_passed: true`
- `counterfactual_gate_passed: false`

Counterfactual violation summary improved to:

- `resilience_score`: violation rate `0.1133`, worst delta `-0.1067`
- `future_orientation`: violation rate `0.0586`, worst delta `-0.0787`
- `numeracy_score`: violation rate `0.0273`, worst delta `-0.0269`
- `scroll_hesitation_score`: violation rate `0.0352`, worst delta `-0.0438`

Compared with the earlier monotonic-design run, this is a meaningful reduction
in the worst local reversals for `numeracy_score` and `scroll_hesitation_score`,
and a moderate improvement for `future_orientation`. `resilience_score` remains
the dominant blocker.

The promotion decision did not change:

- raw standalone TabNet is still blocked from reintegration
- ensemble variants remain intentionally unevaluated
- runtime disagreement mitigation remains the production safeguard

## Post-Processing Diagnostic

The critical-feature monotonic postprocessor passed the gate:

- gate passed: `true`
- test AUC: `0.7694`
- Brier: `0.1725`
- ECE: `0.0715`

That is useful evidence that monotonic post-processing can enforce the desired
ordering, but it does **not** satisfy the current promotion rule because raw
TabNet itself still fails the counterfactual stability requirement.

## Interpretation

The monotonic-design path is working in the right direction:

- brittle composites were successfully suppressed
- anchor-level local monotonicity improved materially
- counterfactual curriculum rows improved raw stability
- but broader sampled counterfactual stability is still not good enough

This is exactly the sort of failure AUC alone would miss.

## Next Recommended Iteration

Stay in standalone TabNet mode and do not evaluate ensemble variants yet.

Next safe steps:

- increase targeted counterfactual coverage around the still-failing slices, especially high-resilience and low-hesitation neighborhoods
- add harder pair construction so favorable perturbations are represented more densely near the current violation regions
- consider masking or simplifying additional nonlinear interactions if they keep reintroducing reversals through unmasked features
- keep the monotonic postprocessor only as a diagnostic baseline unless the promotion policy is intentionally changed

Given the targeted run results, the next concrete iteration should focus on:

- adaptive hard-pair mining around the remaining resilience-heavy violations
- denser future-orientation pairs in the residual failing pockets
- preserving the narrower targeted numeracy / hesitation curriculum, since that direction was helpful

## Adaptive Hard-Pair Mining Iterations

Two follow-up mining runs were evaluated after the targeted curriculum result.

### 1. Resilience/Future Hard-Pair Mining

Run:

- `runtime/research_archive/tabnet_repair/hardmined_light/`

Setup:

- hard-pair features: `resilience_score`, `future_orientation`
- mining sample size: `512`
- max mined violations per feature: `128`
- repeats: `1`
- mined rows added: `52`

Result:

- AUC: `0.7647`
- Brier: `0.1702`
- ECE: `0.0831`
- local monotonic gate: passed
- counterfactual gate: failed

Counterfactual violation summary:

- `resilience_score`: violation rate `0.0417`, worst delta `-0.0495`
- `future_orientation`: violation rate `0.0521`, worst delta `-0.1002`
- `numeracy_score`: violation rate `0.0521`, worst delta `-0.1124`
- `scroll_hesitation_score`: violation rate `0.0313`, worst delta `-0.0981`

Interpretation:

- resilience improved substantially and nearly met the hard thresholds
- hesitation also improved slightly
- numeracy and future remained unstable enough to block promotion

### 2. All-Feature Hard-Pair Mining

Run:

- `runtime/research_archive/tabnet_repair/hardmined_allfeatures/`

Setup:

- hard-pair features:
  - `resilience_score`
  - `future_orientation`
  - `numeracy_score`
  - `scroll_hesitation_score`
- mining sample size: `384`
- max mined violations per feature: `96`
- repeats: `1`
- mined rows added: `161`

Result:

- AUC: `0.7871`
- Brier: `0.1615`
- ECE: `0.0551`
- local monotonic gate: failed
- counterfactual gate: failed

Counterfactual violation summary:

- `resilience_score`: violation rate `0.1563`, worst delta `-0.1701`
- `future_orientation`: violation rate `0.0313`, worst delta `-0.0711`
- `numeracy_score`: violation rate `0.0208`, worst delta `-0.0165`
- `scroll_hesitation_score`: violation rate `0.0469`, worst delta `-0.0980`

It also reintroduced a local monotonic failure on `text_agency_score`.

Interpretation:

- widening hard-pair mining improved aggregate AUC and helped numeracy materially
- but it destabilized other local surfaces, especially resilience and text-agency behavior
- that is a sign we are starting to trade one monotonic surface against another inside TabNet

## Current Best Read

The current best candidate for monotonic robustness is still not promotable.

If we optimize for the counterfactual blocker that mattered most in the targeted run:

- the resilience/future hard-mined candidate is the most encouraging

If we optimize for aggregate AUC:

- the all-feature hard-mined candidate is strongest

But under the actual promotion policy, neither is acceptable:

- no candidate passes both the local monotonic gate and the pairwise counterfactual gate

## Next Recommended Iteration

The next safe iteration should stay narrow and asymmetric rather than broader:

- keep the targeted numeracy / hesitation curriculum, since it reduced those violations meaningfully
- keep resilience-focused hard-pair mining, because it nearly met threshold there
- do **not** widen mining across every feature at once again, because that reintroduced local instability on another surface
- add an explicit text-agency guard or text-feature stability audit when mining beyond resilience/future, since that was the first collateral failure to reappear

## Collateral Guard Follow-Up

Two guarded follow-up runs were evaluated after adding an explicit pairwise
`text_agency_score` audit to the promotion policy.

### 1. Resilience-Only Guarded Mining

Run:

- `runtime/research_archive/tabnet_repair/resilience_guarded/`

Setup:

- hard-pair features: `resilience_score`
- mining sample size: `768`
- max mined violations per feature: `192`
- repeats: `2`
- collateral guard feature: `text_agency_score`

Result:

- AUC: `0.7761`
- Brier: `0.1650`
- ECE: `0.0684`
- local monotonic gate: passed
- core counterfactual gate: failed
- collateral guard gate: failed

Counterfactual violation summary:

- `resilience_score`: violation rate `0.0990`, worst delta `-0.2434`
- `future_orientation`: violation rate `0.1146`, worst delta `-0.3910`
- `numeracy_score`: violation rate `0.0677`, worst delta `-0.4180`
- `scroll_hesitation_score`: violation rate `0.0729`, worst delta `-0.1319`
- `text_agency_score`: violation rate `0.2292`, worst delta `-0.1467`

Interpretation:

- increasing resilience-only mining pressure did not preserve the earlier resilience gains
- stronger mining also triggered a severe pairwise `text_agency_score` regression
- this indicates that mining intensity alone can create collateral instability even when anchor sweeps still look clean

### 2. Future-Only Guarded Mining

Run:

- `runtime/research_archive/tabnet_repair/future_guarded/`

Setup:

- hard-pair features: `future_orientation`
- mining sample size: `768`
- max mined violations per feature: `192`
- repeats: `2`
- collateral guard feature: `text_agency_score`

Result:

- AUC: `0.7776`
- Brier: `0.1675`
- ECE: `0.0740`
- local monotonic gate: passed
- core counterfactual gate: failed
- collateral guard gate: failed

Counterfactual violation summary:

- `resilience_score`: violation rate `0.0625`, worst delta `-0.0741`
- `future_orientation`: violation rate `0.1042`, worst delta `-0.1333`
- `numeracy_score`: violation rate `0.0313`, worst delta `-0.0383`
- `scroll_hesitation_score`: violation rate `0.0781`, worst delta `-0.0721`
- `text_agency_score`: violation rate `0.2344`, worst delta `-0.1482`

Interpretation:

- future-only mining improved numeracy and bounded the worst numeracy delta below the hard threshold
- however, future stability itself remained far from promotable
- the collateral `text_agency_score` failure persisted almost unchanged, suggesting it is a structural side effect of the harder mining regime rather than a resilience-only artifact

## Trainable Collateral Surface Experiment

The experiment harness was then extended so curriculum augmentation and
hard-pair mining can explicitly operate on a broader trainable monotonic
feature set, including:

- `text_agency_score`
- `text_sentiment_compound`
- `conscientiousness_score`

This was done to test whether `text_agency_score` should be stabilized through
training rather than treated only as a post hoc promotion guard.

### 3. Future Mining + Text-Agency Curriculum

Run:

- `runtime/research_archive/tabnet_repair/future_textcurriculum/`

Setup:

- curriculum features:
  - `resilience_score`
  - `future_orientation`
  - `numeracy_score`
  - `scroll_hesitation_score`
  - `text_agency_score`
- hard-pair features: `future_orientation`
- mining sample size: `768`
- max mined violations per feature: `192`
- repeats: `2`

Result:

- AUC: `0.7892`
- Brier: `0.1571`
- ECE: `0.0464`
- local monotonic gate: failed
- core counterfactual gate: failed
- collateral guard gate: failed

Key failures:

- `resilience_score`: endpoint delta `-0.0550`
- `future_orientation`: worst local step `-0.1116`
- `numeracy_score`: worst local step `-0.0855`
- `text_agency_score`: worst local step `-0.3788`
- `text_sentiment_compound`: endpoint delta `-0.1071`
- `conscientiousness_score`: endpoint delta `-0.0406`

Counterfactual violation summary:

- `resilience_score`: violation rate `0.1875`, worst delta `-0.1729`
- `future_orientation`: violation rate `0.1510`, worst delta `-0.2452`
- `numeracy_score`: violation rate `0.0417`, worst delta `-0.0344`
- `scroll_hesitation_score`: violation rate `0.0833`, worst delta `-0.1290`
- `text_agency_score`: violation rate `0.2031`, worst delta `-0.1779`

Interpretation:

- aggregate discrimination improved again, but monotonic behavior degraded sharply
- directly inserting `text_agency_score` into the core curriculum destabilized several surfaces at once
- collateral features should remain guarded separately for now rather than being folded directly into the core curriculum recipe

## Updated Best Read

The strongest promotable-looking direction is still the earlier narrow
resilience/future hard-mined path, not the newer guarded or collateral-trained
variants.

Current conclusion:

- guard audits were worth adding because they exposed a failure that anchor sweeps alone missed
- direct collateral-feature curriculum is too aggressive for the current TabNet regime
- the next safe iteration should focus on lighter-weight collateral regularization or guarded post-processing diagnostics, not broader curriculum expansion
