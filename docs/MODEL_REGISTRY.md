# Model registry

There is no active model registry in the public AlterScore serving path. The
former synthetic XGBoost manifest, serialized artifacts, explainers, and
reports are archived under `research/legacy_synthetic_model/models/`.

## Archive boundary

The archive is retained for provenance and offline research reference. Its
labels and fairness reports are synthetic. Its AUC values measure recovery of
generated data and are not external validation, repayment prediction,
creditworthiness, or lending evidence. The archived model does not score
public assessments.

## Public runtime rules

- Production imports must not load archived model modules or artifacts.
- `backend/requirements.txt` contains only public serving dependencies.
- The Dockerfile copies only `backend/app` and never copies model files.
- Public readiness must not depend on an artifact manifest or report.
- No model artifact may be regenerated or promoted as part of a public v2
  release.

Future model research requires a separate environment, dependency file, review
boundary, and explicit product authorization. It must not be reattached to
the public assessment contract implicitly.
