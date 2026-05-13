# AlterScore Data Schema

## Schema Principles

- Model inputs are derived from assessment answers, behavioral telemetry, and local NLP only.
- Protected attributes are audit-only and never model inputs.
- Temporal metadata is validation-only and never model input.
- Generated data must be deterministic given a seed.
- Feature definitions must be shared by training and inference.

## Dataset Inventory

| Dataset | Path | Producer | Consumer | Git Policy |
|---|---|---|---|---|
| Synthetic raw dataset | `data/raw/synthetic_dataset.csv` | Data generator | Validation, EDA | Ignored by default |
| Processed train dataset | `data/processed/train.parquet` | Preprocessing job | Training | Ignored by default |
| Processed validation dataset | `data/processed/validation.parquet` | Preprocessing job | Calibration | Ignored by default |
| Processed test dataset | `data/processed/test.parquet` | Preprocessing job | Evaluation, reports | Ignored by default |
| Data profile report | `data/reports/data_profile_report.html` | Validation job | Human review | Ignored unless small |
| Validation summary | `data/validation/validation_summary.json` | Validation job | CI and docs | May be tracked if small |

## Primary Target

| Column | Type | Values | Use |
|---|---|---|---|
| `repayment_label` | int | 0 default, 1 repaid | Supervised training target |

## Temporal Metadata

| Column | Type | Values | Use |
|---|---|---|---|
| `cohort_month` | int | 1-12 | Train/validation/test split and drift comparison |
| `application_date` | date/string | Date within cohort month | Demo realism and optional cohort filtering |

These columns must not appear in model input feature lists.

## Protected Attributes

| Column | Type | Values | Use |
|---|---|---|---|
| `gender` | category | `male`, `female`, `non_binary` | Fairness audit only |
| `age_group` | category | `18-25`, `26-35`, `36-50`, `50+` | Fairness audit only |
| `region` | category | `urban`, `semi-urban`, `rural` | Fairness audit only |
| `education_level` | category | `none`, `primary`, `secondary`, `graduate` | Fairness audit only |

Protected attributes must never appear in `NUMERIC_FEATURES`, `CATEGORICAL_FEATURES`, inference feature dataframes, SHAP suggestions, or DICE mutable feature lists.

## Model Feature Registry

### Feature Count Decision

AlterScore will use the explicit named feature list from the PRD as the source of truth: 33 numeric features plus 2 categorical features, for 35 total model inputs. The project will not invent four additional psychometric features to satisfy the earlier narrative count of 39.

Canonical breakdown:

| Layer | Numeric | Categorical | Total Model Inputs |
|---|---:|---:|---:|
| Psychometric | 14 | 0 | 14 |
| Behavioral telemetry | 7 | 2 | 9 |
| Local NLP | 5 | 0 | 5 |
| Derived / engineered | 7 | 0 | 7 |
| **Total** | **33** | **2** | **35** |

### Layer 1 - Psychometric Features

| Feature | Type | Range | Source | Notes |
|---|---|---|---|---|
| `numeracy_score` | float | 0-1 | Financial math questions | Correct answers over numeracy questions |
| `CRT_score` | float | 0-1 | Cognitive reflection questions | Reflective answers over CRT questions |
| `financial_literacy_score` | float | 0-1 | Financial literacy MCQs | Correct answers over financial literacy questions |
| `future_orientation` | float | 0-1 | Delay discounting choices and Likert | Larger-later preference and stated future orientation |
| `delay_discounting_rate` | float | 0-1 | Delay discounting choices | Normalized inverse discount rate |
| `risk_attitude` | float | 0-1 | Risk choices and Likert | Middle range preferred, extremes are risky |
| `risk_consistency_flag` | int | 0 or 1 | Risk choices | 1 means inconsistent risk behavior |
| `loss_aversion_score` | float | 0-1 | Loss aversion scenario | Higher means more loss-averse |
| `locus_of_control` | float | 0-1 | Locus questions | Higher means internal locus |
| `conscientiousness_score` | float | 0-1 | Planning and follow-through questions | Higher means more conscientious |
| `social_capital_score` | float | 0-1 | Community support questions | Informal collateral proxy |
| `honesty_score` | float | 0-1 | Trap and consistency questions | Higher means more reliable response pattern |
| `resilience_score` | float | 0-1 | Resilience questions | Adaptability under financial stress |
| `reciprocity_norm` | float | 0-1 | Reciprocity questions | Mutual obligation and repayment ethic |

### Layer 2 - Behavioral Telemetry Features

| Feature | Type | Range | Capture Method | Notes |
|---|---|---|---|---|
| `avg_response_time_ms` | float | 100-120000 | Per-question timing | Deliberation vs impulsivity |
| `answer_change_rate` | float | 0-1 | Answer revision counts / question count | Indecision or second guessing |
| `session_duration_sec` | float | 0-7200 | Session start to submit | Rushing vs careful completion |
| `dropout_count` | int | 0-20 | Visibility-change events | Distraction or outside help |
| `scroll_hesitation_score` | float | 0-1 | Scroll events normalized | Reading carefully vs skimming |
| `risk_response_speed_ratio` | float | 0-5 | Risk question response time / average response time | Fast risk choices imply impulsivity |
| `typing_speed_wpm` | float | 0-200 | Q27 typing speed | Literacy proxy |
| `time_of_day` | category | morning, afternoon, evening, night | Browser time bucket | Categorical model input |
| `device_type` | category | mobile, desktop, tablet | User-agent parsing | Categorical model input |

### Layer 3 - Local NLP Features

| Feature | Type | Range | Source | Notes |
|---|---|---|---|---|
| `text_sentiment_compound` | float | -1 to 1 | VADER | Overall sentiment |
| `text_agency_score` | float | 0-1 | spaCy patterning | Active first-person agency |
| `text_problem_solving_flag` | int | 0 or 1 | Keyword matching | Problem-solving language present |
| `text_semantic_dim1` | float | unbounded | Sentence-transformer PCA | PCA dim 1 fit on train only |
| `text_semantic_dim2` | float | unbounded | Sentence-transformer PCA | PCA dim 2 fit on train only |

### Layer 4 - Derived Features

| Feature | Type | Formula |
|---|---|---|
| `psychological_credit_index` | float | `0.22*numeracy + 0.18*honesty + 0.16*future_orientation + 0.12*locus + 0.10*social_capital + 0.08*conscientiousness + 0.06*CRT + 0.05*financial_literacy + 0.03*(1-loss_aversion)` |
| `cognitive_consistency_index` | float | `CRT_score * (1 - risk_consistency_flag) * (1 - answer_change_rate)` |
| `repayment_intention_score` | float | `locus_of_control * social_capital_score * honesty_score` |
| `impulsivity_index` | float | `(risk_attitude * risk_response_speed_ratio) / (CRT_score + 0.1)` |
| `cognitive_load_index` | float | `(avg_response_time_ms / 4500) * (1 + answer_change_rate) * (1 + dropout_count * 0.2)` |
| `engagement_score` | float | `scroll_hesitation_score * (1 - answer_change_rate) * (1 - dropout_count/4) * (1 - risk_response_speed_ratio*0.3)` |
| `behavioral_trust_score` | float | `engagement_score * honesty_score * (1 - impulsivity_index)` |

## Canonical Feature Lists

### Numeric Features

```python
NUMERIC_FEATURES = [
    "numeracy_score",
    "CRT_score",
    "financial_literacy_score",
    "future_orientation",
    "delay_discounting_rate",
    "risk_attitude",
    "risk_consistency_flag",
    "loss_aversion_score",
    "locus_of_control",
    "conscientiousness_score",
    "social_capital_score",
    "honesty_score",
    "resilience_score",
    "reciprocity_norm",
    "avg_response_time_ms",
    "answer_change_rate",
    "session_duration_sec",
    "dropout_count",
    "scroll_hesitation_score",
    "risk_response_speed_ratio",
    "typing_speed_wpm",
    "text_sentiment_compound",
    "text_agency_score",
    "text_problem_solving_flag",
    "text_semantic_dim1",
    "text_semantic_dim2",
    "psychological_credit_index",
    "cognitive_consistency_index",
    "repayment_intention_score",
    "impulsivity_index",
    "cognitive_load_index",
    "engagement_score",
    "behavioral_trust_score",
]
```

### Categorical Features

```python
CATEGORICAL_FEATURES = [
    "device_type",
    "time_of_day",
]
```

### All Model Inputs And Target

```python
ALL_MODEL_FEATURES = NUMERIC_FEATURES + CATEGORICAL_FEATURES

TARGET = "repayment_label"
```

### Excluded From Model Inputs

```python
PROTECTED_FEATURES = [
    "gender",
    "age_group",
    "region",
    "education_level",
]

TEMPORAL_METADATA = [
    "cohort_month",
    "application_date",
]
```

### Counterfactual Actionability

`ACTIONABLE_FEATURES` are mutable numeric fields that DICE-style counterfactuals may vary. They must exclude protected attributes, temporal metadata, categorical model inputs, and immutable fields.

```python
ACTIONABLE_FEATURES = [
    "numeracy_score",
    "financial_literacy_score",
    "future_orientation",
    "conscientiousness_score",
    "social_capital_score",
    "engagement_score",
    "avg_response_time_ms",
    "answer_change_rate",
    "text_agency_score",
]

IMMUTABLE_FEATURES = [
    "gender",
    "age_group",
    "region",
    "education_level",
    "device_type",
    "time_of_day",
    "cohort_month",
    "application_date",
]
```

## Synthetic Generation Requirements

| Requirement | Target |
|---|---|
| Record count | 10,000 |
| Default rate | 24-32 percent, target around 28 percent |
| Cohort months | 1-12 |
| Train split | months 1-8 |
| Validation/calibration split | months 9-10 |
| Test split | months 11-12 |
| Future test size | At least 1,000 rows |
| Label generation | Latent model with capacity, intention, character, and risk signal |
| Demographics | Indian microfinance-like distributions from PRD |
| Drift | Mild later-cohort drift in response speed and typing speed |

## Required Correlations

| Pair | Target Direction |
|---|---|
| `numeracy_score` and `financial_literacy_score` | about +0.55 |
| `future_orientation` and `conscientiousness_score` | about +0.45 |
| `locus_of_control` and `resilience_score` | about +0.40 |
| `honesty_score` and `social_capital_score` | about +0.35 |
| `CRT_score` and `numeracy_score` | about +0.50 |
| `impulsivity_index` and `risk_response_speed_ratio` | about +0.60 |
| `avg_response_time_ms` and `CRT_score` | about -0.30 |

## Data Validation Gates

- No missing values.
- Default rate between 24 and 32 percent.
- Cohort months are only 1-12.
- Test cohort contains at least 1,000 rows.
- Primary features show meaningful correlation with label.
- Protected attributes do not have concerning direct label correlation.
- Protected attributes are separate from model inputs.
- Temporal metadata is excluded from model inputs.
- NLP PCA is fit only on training data.

## Runtime Feature Assembly Order

1. Parse raw answers into psychometric features.
2. Parse browser telemetry into behavioral features.
3. Extract local NLP features from Q27 text.
4. Transform raw sentence embedding through train-fitted PCA.
5. Compute derived features.
6. Build dataframe with `NUMERIC_FEATURES + CATEGORICAL_FEATURES`.
7. Apply saved preprocessor.
8. Pass processed row to calibrated model.
