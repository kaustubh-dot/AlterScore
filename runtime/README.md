# Runtime Outputs

This directory holds local runtime files that are useful while developing but
should not be treated as source artifacts.

- `logs/`: local request and execution logs
- `pytest-*` and `pytest-workspace/`: local test scratch space

Most generated contents under `runtime/` are ignored by git. The public v2
Docker image is artifact-free and does not consume a deployable model bundle;
it copies only `backend/app` plus its serving requirements. Durable setup and
release/rollback documentation lives under `docs/`.
