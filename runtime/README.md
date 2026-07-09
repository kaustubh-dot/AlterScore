# Runtime Outputs

This directory holds local runtime files that are useful while developing but
should not be treated as source artifacts.

- `logs/`: local request and execution logs
- `pytest-*` and `pytest-workspace/`: local test scratch space

Most generated contents under `runtime/` are ignored by git. The deployable
model bundle lives under `models/`, and durable setup/deployment documentation
lives under `docs/`.
