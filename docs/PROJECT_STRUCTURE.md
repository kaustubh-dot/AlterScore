# Project Structure

## Purpose

This repository is organized around a governed production scoring path plus a
preserved research trail.

The goal is to make it easy to distinguish:

- active production-grade scoring architecture
- governance infrastructure and reports
- research-only experiments
- archived generated outputs

## Top-Level Layout

| Path | Role |
|---|---|
| `backend/` | FastAPI runtime, inference, offline ML, governance logic |
| `frontend/` | React/Vite borrower UI and evaluator-facing frontend |
| `models/` | Checked-in production runtime bundle, manifest, explainers, and core reports |
| `scripts/` | Active setup, training, governance, and maintenance entrypoints |
| `tests/` | Unit and integration coverage |
| `docs/` | Active architecture, governance, setup, decisions, and project memory |
| `runtime/` | Local generated outputs, split into governed reports and research archive |
| `archive/` | Repository-level archive notes and historical experiment guidance |
| `data/` | Generated datasets and validation artifacts |
| `experiments/` | Reserved space for future experiment configs and run bookkeeping |

## Documentation Layout

| Path | Role |
|---|---|
| `docs/governance/` | Production-track architecture, governed comparisons, fairness hardening reviews |
| `docs/research_archive/` | Research-only audit reports and TabNet investigation history |
| `docs/adr/` | Architecture decision records |
| `docs/context_templates/` | Handoff, session summary, and AI workflow templates |

## Runtime Layout

| Path | Role |
|---|---|
| `runtime/governed_reports/` | Production-track governed evaluation outputs |
| `runtime/research_archive/` | Local research outputs kept for comparison, not production |
| `runtime/logs/` | Local request and execution logs |

## Active Production Track

The current active production-track work centers on:

- monotonic constrained-tree evaluation
- governed promotion reviews
- fairness hardening for monotonic `XGBoost`

Primary entrypoints:

- [scripts/train_monotonic_tree_candidates.py](C:/Kaustubh/Projects/AlterScore/scripts/train_monotonic_tree_candidates.py)
- [scripts/fairness_harden_xgboost_candidate.py](C:/Kaustubh/Projects/AlterScore/scripts/fairness_harden_xgboost_candidate.py)
- [backend/ml/training/classical/monotonic_constraints.py](C:/Kaustubh/Projects/AlterScore/backend/ml/training/classical/monotonic_constraints.py)

## Research Archive

TabNet repair and monotonicity experiments are preserved for:

- governance lessons learned
- benchmark comparison
- presentation material
- future research reference

They are intentionally not part of the primary trusted production path.
