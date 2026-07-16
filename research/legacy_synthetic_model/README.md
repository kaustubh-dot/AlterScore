# Legacy synthetic model archive

This directory is offline research material preserved from the pre-v3
model-backed scorer. It is not part of the public serving import graph or the
production image.

The archived labels and fairness reports are synthetic. Any archived AUC or
calibration value measures recovery of generated data, not repayment,
creditworthiness, external validation, or real-world fairness. The archived
model does not score public assessments.

Contents include the former ML source tree, model artifacts, training and
validation scripts, legacy API/scoring modules, client question bank, Admin
surface, and their legacy tests. They are retained for provenance and research
reference only; the v2 assessment uses the canonical instrument, branching
engine, unified scorer, and anonymous signing boundary under `backend/app/`.

Do not import this archive from production code. If future research work needs
to execute it, install its dependencies in a separate environment and adapt
the historical imports to this archive namespace rather than adding them back
to the public runtime.
