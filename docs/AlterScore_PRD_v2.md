# AlterScore — Alternative Credit Scoring Platform
## Full Product Requirements Document v2.0
### Valiara Club Finance & Tech Recruitment | AY 2024-25

---

> **Constraints driving this version:**
> - ✅ No external LLM API required (all NLP is local via HuggingFace, VADER, spaCy)
> - ✅ GPU available (RTX 3060 local + cloud) — enables TabNet, MLP, Optuna HPO
> - ✅ Ample time and Codex tokens — no shortcuts; do it properly
> - ✅ Full model training pipeline included

---

## Implementation Status Addendum - May 25, 2026

This PRD records the original product target, including a calibrated stacking
ensemble as the planned production scorer. The implemented repository has since
completed that ensemble track and then superseded the default runtime with a
governed monotonic `XGBoost` bundle after constrained-tree governance review.

Current implementation source of truth:

- Active manifest runtime: `xgboost_monotonic`
- Manifest version: `xgboost_monotonic_v1`
- Runtime manifest: `models/registry/production_manifest.json`
- Reference ensemble: retained as benchmark and rollback/reference
  infrastructure
- Open pre-pilot item: reconcile checked-in monotonic metrics and fairness
  reports, especially the `gender=non_binary` attention finding

The original PRD should still be used for product scope, API intent, and
workflow coverage. Current runtime details live in `docs/CURRENT_STATE.md`,
`docs/BACKEND_RUNTIME_ARCHITECTURE.md`, and `docs/MODEL_REGISTRY.md`.

---

# TABLE OF CONTENTS

1. [Executive Summary](#1-executive-summary)
2. [Problem Statement & Research Basis](#2-problem-statement--research-basis)
3. [System Architecture Overview](#3-system-architecture-overview)
4. [Complete Feature Engineering](#4-complete-feature-engineering)
5. [Data Generation Pipeline](#5-data-generation-pipeline)
6. [Local NLP Pipeline (No API)](#6-local-nlp-pipeline-no-api)
7. [Full ML Training Architecture](#7-full-ml-training-architecture)
8. [Fairness Audit System](#8-fairness-audit-system)
9. [FastAPI Backend — Complete Spec](#9-fastapi-backend--complete-spec)
10. [React Frontend — Complete Spec](#10-react-frontend--complete-spec)
11. [Complete File Structure](#11-complete-file-structure)
12. [Codex Build Roadmap — Step by Step](#12-codex-build-roadmap--step-by-step)
13. [Testing & Validation Strategy](#13-testing--validation-strategy)
14. [Submission Checklist](#14-submission-checklist)
15. [Interview Preparation](#15-interview-preparation)

---

# 1. Executive Summary

**Product:** AlterScore — Psychometric & Behavioral Credit Scoring for the Unbanked  
**Stack:** React + FastAPI + scikit-learn + PyTorch + HuggingFace Transformers  
**Data:** 10,000 synthetic records, 39 model features, 4 feature layers, simulated cohort month  
**Models:** Logistic → RF → XGBoost → LightGBM → TabNet → MLP → Stacking Ensemble  
**NLP:** sentence-transformers (local), VADER sentiment, spaCy keyword extraction  
**Explainability:** SHAP waterfall plots + DICE-ML counterfactual improvement plans  
**Fairness:** Demographic parity, equalized odds, calibration across 4 protected attributes  
**Validation:** Temporal cohort split + PSI drift detection + baseline comparison against a simulated loan officer  

AlterScore scores creditworthiness using only **how a person thinks and behaves**, not their financial history. A 27-question assessment captures psychometric dimensions (numeracy, CRT, integrity, time preference, social capital) and behavioral telemetry (response speed, answer changes, engagement). One open-text question is analyzed locally via sentence-transformers. The final model is a 6-learner stacking ensemble calibrated with isotonic regression, producing a score from 300–850 with SHAP-powered per-user explanations, DICE-ML "what would need to change" counterfactuals, a WhatsApp-shareable score card, and an evaluator dashboard that proves temporal generalization, drift stability, and ensemble lift over simpler baselines.

---

# 2. Problem Statement & Research Basis

## 2.1 The Access Gap

1.4 billion adults globally are unbanked. In India, 190M+ adults have no formal credit history. The CIBIL score requires prior loan history — a circular exclusion that traps new borrowers permanently. Rural workers, informal sector earners, and first-time job holders cannot access capital not because they are risky but because they are **invisible** to the financial system.

## 2.2 What the Research Says

| Source | Finding |
|---|---|
| Klinger et al., 2013 (IFC / World Bank) | Psychometric tests predicting entrepreneurial success have AUC 0.71–0.78 on real microfinance datasets in Peru, South Africa, and Eastern Europe |
| Djankov et al., 2008 | Social capital and community trust are significant predictors of informal loan repayment |
| Karlan & Zinman, 2008 | Behavioral economics signals (time preference, risk attitude) improve credit model AUC by 4–7 points over demographic-only models |
| EFL Global (now Lenddo) | Commercial psychometric scoring deployed across 30+ countries; reduces default rates by 30–50% versus no-score lending |

## 2.3 What Makes This Different From Standard Credit Scoring

| Traditional CIBIL/FICO | AlterScore |
|---|---|
| Requires bank account + loan history | Requires 27 questions and 5 minutes |
| Black box score | SHAP explanation + counterfactual improvement plan per user |
| Circular — excludes first-time borrowers | Works on anyone who can read |
| No fairness audit | Explicit demographic parity check + PSI drift monitoring |
| Static — only looks at past | Behavioral — measures current cognition and validates on future simulated cohorts |

---

# 3. System Architecture Overview

```
╔══════════════════════════════════════════════════════════════════╗
║                        USER BROWSER                              ║
║                                                                  ║
║  Landing → Assessment → [Results] → [Dashboard]                 ║
║                │                                                  ║
║                │  POST /api/score (JSON)                          ║
╚════════════════╪═════════════════════════════════════════════════╝
                 │
╔════════════════▼═════════════════════════════════════════════════╗
║              FASTAPI APPLICATION (port 8000)                     ║
║                                                                  ║
║  ┌─────────────────┐   ┌──────────────────────────────────────┐  ║
║  │  /api/score     │   │  /api/analytics/*                    │  ║
║  │  POST handler   │   │  model-stats, baselines, drift, roc  │  ║
║  │                 │   │  distribution, shap, counterfactuals │  ║
║  └────────┬────────┘   └──────────────────────────────────────┘  ║
║           │                                                       ║
║  ┌────────▼──────────────────────────────────────────────────┐   ║
║  │                  INFERENCE ENGINE                          │   ║
║  │                                                            │   ║
║  │  answer_parser.py → feature_engineer.py → nlp_features.py │   ║
║  │       ↓                                                    │   ║
║  │  stacking_ensemble.pkl  (loaded at startup, cached)        │   ║
║  │       ↓                                                    │   ║
║  │  shap_explainer.pkl  →  waterfall values                   │   ║
║  │  dice_explainer.pkl  →  counterfactual actions             │   ║
║  │       ↓                                                    │   ║
║  │  score_mapper.py  →  300-850 credit score                  │   ║
║  └────────────────────────────────────────────────────────────┘   ║
╚══════════════════════════════════════════════════════════════════╝

╔══════════════════════════════════════════════════════════════════╗
║           OFFLINE TRAINING PIPELINE (run once on GPU)            ║
║                                                                  ║
║  generate_data.py                                                ║
║       → synthetic_dataset.csv  (10,000 records, 39 features + month) ║
║       → nlp_text_embeddings.npy  (sentence-transformer output)  ║
║                                                                  ║
║  baselines.py                                                    ║
║       → majority, logistic, simulated loan-officer benchmarks    ║
║                                                                  ║
║  train_classical.py                                              ║
║       → logistic.pkl, rf.pkl, xgb.pkl, lgbm.pkl                 ║
║       → optuna HPO logs per model                               ║
║                                                                  ║
║  train_neural.py  (GPU)                                          ║
║       → tabnet_model.pt, mlp_model.pt                           ║
║                                                                  ║
║  train_stacking.py                                               ║
║       → stacking_ensemble.pkl  (meta-learner on all base models) ║
║       → calibrated_stacking.pkl                                  ║
║                                                                  ║
║  explain.py                                                      ║
║       → global_shap_importance.json                              ║
║       → shap_explainer.pkl                                       ║
║                                                                  ║
║  fairness_audit.py                                               ║
║       → fairness_report.json                                     ║
║                                                                  ║
║  drift.py                                                        ║
║       → psi_report.json (train vs future test feature stability) ║
║                                                                  ║
║  evaluate.py                                                     ║
║       → metrics.json  (models + baselines + temporal metrics)    ║
╚══════════════════════════════════════════════════════════════════╝
```

## 3.1 Technology Decisions

| Decision | Choice | Reason |
|---|---|---|
| Neural models | PyTorch (TabNet via pytorch-tabnet) | GPU-compatible; TabNet is SOTA for tabular |
| NLP (text question) | sentence-transformers (all-MiniLM-L6-v2) | 80MB, CPU/GPU, no API key, 384-dim embeddings |
| Sentiment analysis | VADER (vaderSentiment) | Rule-based, zero inference cost, good for short text |
| NLP tokenization | spaCy (en_core_web_sm) | Keyword extraction from text answers |
| HPO | Optuna | GPU-friendly, efficient, integrates with sklearn + PyTorch |
| Explainability | SHAP (TreeExplainer + DeepExplainer) | Gold standard, supports all model types |
| Counterfactuals | DICE-ML | Produces actionable "what to change" explanations for sklearn-compatible models |
| Calibration | sklearn CalibratedClassifierCV (isotonic) | Ensures probabilities are meaningful |
| Drift detection | Population Stability Index (PSI) | Lightweight, interpretable feature drift signal for analytics dashboard |
| Frontend charts | Recharts | Lightweight, React-native, no CDN dependency |
| Share card export | html2canvas | Converts the score result card into a WhatsApp-shareable PNG |
| API validation | Pydantic v2 | Fast, strict, great error messages |

---

# 4. Complete Feature Engineering

## 4.1 Feature Layer Map

```
LAYER 1 — PSYCHOMETRIC FEATURES      (from scored questions)           18 features
LAYER 2 — BEHAVIORAL TELEMETRY       (captured silently during session)  9 features
LAYER 3 — NLP FEATURES               (from open-text answer, local NLP)  5 features
LAYER 4 — DERIVED / ENGINEERED       (computed from layers 1–3)          7 features
                                                                  TOTAL: 39 features
```

---

## 4.2 Layer 1 — Psychometric Features (18 features)

### 1.1 Cognitive Ability Cluster

**`numeracy_score`** *(float 0–1)*  
Proportion of financial math questions answered correctly.
- Q: "You borrow ₹6,000 at 2.5% monthly. How much do you owe after 4 months?" (₹6,600 correct)
- Q: "A wholesaler gives 20% discount on ₹1,400. What do you pay?" (₹1,120 correct)
- Q: "Saving ₹800/month for 18 months. Total saved?" (₹14,400 correct)
- Score: correct/3

**`CRT_score`** *(float: 0, 0.33, 0.67, or 1.0)*  
The Cognitive Reflection Test — measures reflective vs. impulsive System 1 thinking. Validated predictor of financial patience.
- Q: "A bat and ball cost ₹110. Bat costs ₹100 more. Ball costs ₹?" (Correct: ₹5. Trap: ₹10)
- Q: "5 machines make 5 widgets in 5 mins. 100 machines to make 100 widgets?" (Correct: 5 mins. Trap: 100 mins)
- Q: "A lily-pad patch doubles daily. Fills lake in 48 days. Half full on day?" (Correct: 47. Trap: 24)
- Score: reflective answers / 3

**`financial_literacy_score`** *(float 0–1)*  
Conceptual understanding of financial instruments and principles.
- Q: "Inflation is 9%. Your savings account earns 6%. Are you getting richer or poorer in real terms?" (Poorer = correct)
- Q: "A mutual fund — is your invested principal guaranteed?" (No = correct)
- Q: "What does 'credit utilization at 85%' mean for your score?" (MCQ — high utilization harms score = correct)
- Score: correct/3

---

### 1.2 Intertemporal Preference Cluster

**`future_orientation`** *(float 0–1)*  
Delay discounting — preference for larger later vs. smaller sooner rewards. Low discounting (future-preferring) strongly predicts loan repayment.
- Q: "₹500 today OR ₹720 in 4 weeks?" (₹720 = future-preferring, score 1)
- Q: "₹2,000 today OR ₹3,200 in 3 months?" (₹3,200 = future-preferring, score 1)
- Q: "Rate: 'I am willing to sacrifice today's comfort for tomorrow's gain' (1–5)"
- Score: (future_choices/2 × 0.6) + (rating/5 × 0.4)

**`delay_discounting_rate`** *(float 0–1)*  
Implicit discount rate estimated from the intertemporal choices.
- From Q1: implied rate = (720-500)/500 over 4 weeks → annualised
- From Q2: implied rate = (3200-2000)/2000 over 12 weeks → annualised
- Score: normalised inverse discount rate (lower discounting = higher score = better)

---

### 1.3 Risk Preference Cluster

**`risk_attitude`** *(float 0–1)*  
0 = strongly risk-averse, 1 = strongly risk-seeking. Neither extreme is ideal — very risk-averse borrowers avoid growth, very risk-seeking ones over-leverage.
- Q: "Certain ₹400 OR 60% chance of ₹800?" 
- Q: "Certain ₹8,000 OR 50% chance of ₹20,000?"
- Q: "Rate: 'I prefer a stable low-paying job over a risky high-paying one' (1–5)" (reversed)
- Score: normalised 0–1 (0.4–0.6 band is optimal)

**`risk_consistency_flag`** *(int 0 or 1)*  
Checks if risk choices are consistent across magnitudes. Inconsistent choices indicate irrational decision-making.
- If Q1 says risk-averse but Q2 says risk-seeking (or vice versa): flag=1 (inconsistent)
- Inconsistency correlates with impulsive borrowing behavior

**`loss_aversion_score`** *(float 0–1)*  
Extreme loss aversion = sunk cost fallacy = throwing good money after bad.
- Q: "A business loses ₹1,200/month. Do you: (A) Close it immediately (B) Give it 3 more months (C) Invest more to recover?" — C scores highest loss aversion
- Q: "You invested ₹10,000 in something. It's worth ₹4,000 now. Do you: (A) Sell and cut losses (B) Hold hoping it recovers (C) Buy more at lower price?" — B,C = high loss aversion
- Score: 0=rational, 1=highly loss-averse

---

### 1.4 Character & Integrity Cluster

**`locus_of_control`** *(float 0–1)*  
Internal locus (1.0) = "I control my outcomes." External locus (0.0) = "Things just happen to me." Internal locus is one of the strongest single predictors of loan repayment.
- Q: "Financial success is mostly due to: (A) Hard work & smart decisions (B) Luck and connections (C) Circumstances you're born into" — A=1.0, B=0.5, C=0.0
- Q: "If I struggle to repay a loan, it will be because of: (A) My own financial mistakes (B) Bad luck or unexpected events (C) The lender's unfair terms" — A=1.0, B=0.5, C=0.0
- Q: "Rate: 'I am the main author of my own financial story' (1–5)"
- Score: average of attribution scores + rating/5, normalised

**`conscientiousness_score`** *(float 0–1)*  
Proxy for the Big Five conscientiousness trait — planning, discipline, follow-through.
- Q: "Do you keep a record of your monthly spending? (Always/Sometimes/Never)" — Always=1.0, Sometimes=0.5, Never=0.0
- Q: "When you set a goal, how often do you follow through? (1–5)"
- Q: "When you commit to a time, how often are you punctual? (1–5)"
- Score: average normalised to 0–1

**`social_capital_score`** *(float 0–1)*  
Quality of community financial relationships — acts as informal collateral.
- Q: "How many people in your community would lend you ₹1,000 immediately? (0 / 1–2 / 3–5 / 5+)" — 0=0, 1-2=0.33, 3-5=0.67, 5+=1.0
- Q: "Have you ever lent money that was repaid in full and on time? (Yes/No/Haven't lent)" — Yes=1.0, No=0.0, Haven't=0.5
- Q: "If you struggle to repay a friend: (A) Tell them immediately (B) Wait and see (C) Avoid them" — A=1.0, B=0.5, C=0.0
- Score: average of three component scores

**`honesty_score`** *(float 0–1)*  
Multi-method honesty assessment using three independent signals:
1. **Ipsative consistency** (answer same question twice, rephrased) — inconsistency lowers score
2. **Social desirability trap** (implausible virtue claims) — extreme agreement raises suspicion  
3. **CRT honesty** (some people look up answers; CRT+numeracy combo can detect this)

- Trap Q1 (Likert 1–5): "I have never told even a small lie in my entire life" — agreement ≥4 → suspicious flag
- Trap Q2 (Likert 1–5): "I always repay every debt 100% on time, without exception" — agreement ≥4 → suspicious flag
- Consistency check: Reask Q on future_orientation rephrased → |answer1 - answer2| / scale_size
- Score: (1 - inconsistency_ratio) × (1 - social_desirability_penalty) × (1 - implausibility_flag)

**`resilience_score`** *(float 0–1)*  
Grit and adaptability under financial adversity. Resilient borrowers seek solutions rather than defaulting.
- Q (Likert 1–5): "When things get very difficult financially, I find new ways to solve problems"
- Q (Likert 1–5): "I finish what I start, even when it gets much harder than expected"  
- Q (MCQ): "When facing a major financial setback, your first instinct is: (A) Find a new income source (B) Cut expenses hard (C) Ask trusted people for help (D) Feel overwhelmed and unsure" — A,B,C = positive signals

**`reciprocity_norm`** *(float 0–1)*  
How strongly does the person believe in mutual obligation? High reciprocity = strong repayment ethic.
- Q (Likert 1–5): "If someone helped me financially in the past, I feel a strong obligation to help others in the future"
- Q (MCQ): "Which statement best describes you: (A) I always repay favors and debts as a point of honor (B) I repay when I can (C) I deal with each situation independently"

---

### 1.5 Open-Text Dimension (feeds into NLP Layer)

**Question 27 (open text, ~30–100 words):**  
"Describe a time when you faced a serious financial difficulty. What happened, what did you do, and what did you learn?"

This text response is processed by the **local NLP pipeline** (see Section 6) to produce 5 numeric features.

---

## 4.3 Layer 2 — Behavioral Telemetry (9 features)

All captured silently by the frontend during the assessment session. No extra questions needed.

| Feature | Capture Method | What It Signals |
|---|---|---|
| `avg_response_time_ms` | `Date.now()` on question open → answer submit | Deliberation vs impulsivity |
| `answer_change_rate` | Count of answer revisions / 27 | Indecision or second-guessing |
| `session_duration_sec` | Session start → submit timestamp | Rushing vs careful reading |
| `dropout_count` | `document.addEventListener('visibilitychange')` count | Distraction, seeking help outside |
| `scroll_hesitation_score` | Scroll event count before answering each question | Reading carefully vs skimming |
| `risk_response_speed_ratio` | `avg_response_time_ms` on risk Qs / overall avg | Fast risk choices = impulsive |
| `time_of_day` | `new Date().getHours()` binned into 4 windows | Night applicants show mild elevated risk |
| `device_type` | `navigator.userAgent` parsing | Proxy for economic status |
| `typing_speed_wpm` | Character count / typing duration on open-text Q27 | Literacy and education proxy |

---

## 4.4 Layer 3 — NLP Features (5 features, from Q27 open-text)

Processed entirely locally — no API calls. (See Section 6 for full pipeline.)

| Feature | Source | Extraction Method |
|---|---|---|
| `text_sentiment_compound` | Q27 text | VADER compound score (−1 to +1) |
| `text_agency_score` | Q27 text | Proportion of first-person active verbs ("I did", "I found", "I decided") vs passive ("it happened", "I was unable") |
| `text_problem_solving_flag` | Q27 text | spaCy keyword match: solution-oriented keywords present (1) or absence/victim language (0) |
| `text_semantic_embedding_dim1` | Q27 text | PCA dim 1 of sentence-transformer 384-dim embedding (captures primary semantic axis) |
| `text_semantic_embedding_dim2` | Q27 text | PCA dim 2 of sentence-transformer 384-dim embedding |

PCA on the 384-dim embeddings is fit on training set, reducing to 2 dimensions. This avoids the curse of dimensionality while preserving the most discriminative semantic information.

---

## 4.5 Layer 4 — Derived / Engineered Features (7 features)

Computed programmatically from Layers 1–3 *after* all features are extracted.

| Feature | Formula | Interpretation |
|---|---|---|
| `psychological_credit_index` | `0.22*numeracy + 0.18*honesty + 0.16*future_orient + 0.12*locus + 0.10*social_capital + 0.08*conscient + 0.06*CRT + 0.05*fin_lit + 0.03*(1-loss_aversion)` | Composite psychometric creditworthiness |
| `cognitive_consistency_index` | `CRT_score × (1 - risk_consistency_flag) × (1 - answer_change_rate)` | Reflective, consistent decision-maker |
| `repayment_intention_score` | `locus_of_control × social_capital × honesty_score` | All three must be high for strong repayment intent |
| `impulsivity_index` | `(risk_attitude × risk_response_speed_ratio) / (CRT_score + 0.1)` | Fast risky choices + low reflection = impulsive borrower |
| `cognitive_load_index` | `(avg_response_time_ms / 4500) × (1 + answer_change_rate) × (1 + dropout_count×0.2)` | Struggling with questions → lower literacy → higher risk |
| `engagement_score` | `scroll_hesitation_score × (1 − answer_change_rate) × (1 − dropout_count/4) × (1 − risk_response_speed_ratio×0.3)` | High = thoughtful, careful, not rushing |
| `behavioral_trust_score` | `engagement_score × honesty_score × (1 − impulsivity_index)` | Behavioral + psychometric trustworthiness composite |

---

## 4.6 Protected Attributes (NOT model inputs — fairness audit only)

| Attribute | Values | Use |
|---|---|---|
| `gender` | male / female / non_binary | Fairness audit only |
| `age_group` | 18-25 / 26-35 / 36-50 / 50+ | Fairness audit only |
| `region` | urban / semi-urban / rural | Fairness audit only |
| `education_level` | none / primary / secondary / graduate | Fairness audit only |

These are collected in the background during signup/consent screen. They are stored separately from model features, never passed to the model, and used only for post-prediction fairness analysis.

---

# 5. Data Generation Pipeline

## 5.1 Statistical Design

Generate **10,000 records** with realistic distributions. Do not use uniform random — real psychometric data has internal correlations.

### Correlation Structure (must be enforced in generation)
```
numeracy ↔ financial_literacy:      r ≈ +0.55 (high corr — both reflect education)
future_orientation ↔ conscientiousness: r ≈ +0.45
locus_of_control ↔ resilience:      r ≈ +0.40
honesty ↔ social_capital:           r ≈ +0.35
CRT ↔ numeracy:                     r ≈ +0.50
impulsivity ↔ risk_response_speed:  r ≈ +0.60
avg_response_time ↔ CRT:            r ≈ -0.30 (slow responders = more reflective)
```

Use a **multivariate normal** base with a correlation matrix, then transform to the desired marginal distributions. This is the correct approach — do not generate features independently and hope correlations emerge.

```python
import numpy as np
from scipy.stats import norm, beta, truncnorm

def generate_correlated_features(n=10000, seed=42):
    np.random.seed(seed)
    
    # Define 10 base continuous features
    feature_names = [
        'numeracy_base', 'CRT_base', 'financial_lit_base',
        'future_orient_base', 'risk_attitude_base', 'locus_base',
        'conscientiousness_base', 'social_capital_base', 'honesty_base',
        'resilience_base'
    ]
    
    # Correlation matrix (must be positive semi-definite)
    corr = np.array([
        # num   CRT   finlit futornt risk   locus  consc  social honst  resil
        [1.00, 0.50,  0.55,  0.20,  0.00,  0.15,  0.25,  0.10,  0.20,  0.15],  # numeracy
        [0.50, 1.00,  0.40,  0.25, -0.10,  0.20,  0.20,  0.05,  0.15,  0.20],  # CRT
        [0.55, 0.40,  1.00,  0.25,  0.05,  0.20,  0.30,  0.15,  0.15,  0.15],  # fin_lit
        [0.20, 0.25,  0.25,  1.00, -0.15,  0.35,  0.45,  0.25,  0.30,  0.40],  # future_orient
        [0.00,-0.10,  0.05, -0.15,  1.00, -0.10, -0.10,  0.00, -0.05, -0.05],  # risk_attitude
        [0.15, 0.20,  0.20,  0.35, -0.10,  1.00,  0.40,  0.30,  0.35,  0.40],  # locus
        [0.25, 0.20,  0.30,  0.45, -0.10,  0.40,  1.00,  0.30,  0.30,  0.35],  # conscientiousness
        [0.10, 0.05,  0.15,  0.25,  0.00,  0.30,  0.30,  1.00,  0.35,  0.30],  # social_capital
        [0.20, 0.15,  0.15,  0.30, -0.05,  0.35,  0.30,  0.35,  1.00,  0.30],  # honesty
        [0.15, 0.20,  0.15,  0.40, -0.05,  0.40,  0.35,  0.30,  0.30,  1.00],  # resilience
    ])
    
    # Sample from multivariate normal, then transform marginals
    L = np.linalg.cholesky(corr)
    Z = np.random.randn(n, len(feature_names))
    X = Z @ L.T
    
    # Transform each column to desired marginal distribution
    # Most psychometric scores: beta-distributed (avoids uniform, allows skew)
    features = {}
    for i, name in enumerate(feature_names):
        u = norm.cdf(X[:, i])  # to uniform [0,1]
        if 'risk_attitude' in name:
            features[name] = beta.ppf(u, a=1.8, b=1.8)  # roughly symmetric
        elif 'honesty' in name:
            features[name] = beta.ppf(u, a=3.0, b=1.5)  # right-skewed (most are honest)
        elif 'social_capital' in name:
            features[name] = beta.ppf(u, a=2.0, b=2.0)  # symmetric
        else:
            features[name] = beta.ppf(u, a=2.5, b=1.5)  # slightly positive skew
    
    return features
```

## 5.2 Simulated Time Axis and Temporal Split

Every synthetic applicant must be assigned to a simulated application month so the final evaluation proves the model generalizes to future cohorts rather than memorizing one synthetic draw.

```python
def assign_cohort_month(n=10000, seed=42):
    rng = np.random.default_rng(seed)
    # Slight seasonal unevenness, similar to real MFI application volume.
    month_weights = np.array([0.07, 0.07, 0.08, 0.09, 0.10, 0.09, 0.08, 0.08, 0.08, 0.09, 0.09, 0.08])
    cohort_month = rng.choice(np.arange(1, 13), size=n, p=month_weights / month_weights.sum())
    return cohort_month
```

Required columns:
- `cohort_month` *(int 1-12)* — used only for splitting, drift detection, and dashboard cohort filters.
- `application_date` *(date)* — optional derived date inside the month for demo realism.

Required split:
- **Train:** months 1-8
- **Validation/calibration:** months 9-10
- **Test:** months 11-12

The model may use neither `cohort_month` nor `application_date` as input features. They are metadata for validation only.

Add mild temporal drift so PSI has something meaningful to detect without making the dataset unrealistic:

```python
def apply_temporal_drift(features, cohort_month):
    # Later cohorts become slightly faster and more mobile-heavy, but label logic stays stable.
    features['avg_response_time_ms'] *= np.where(cohort_month >= 9, 0.96, 1.0)
    features['typing_speed_wpm'] *= np.where(cohort_month >= 9, 1.04, 1.0)
    return features
```

## 5.3 Realistic Label Generation

Do not use a simple linear formula. Use a **latent variable model** with four components:

```python
def generate_labels(features, n=10000, target_default_rate=0.28, seed=42):
    np.random.seed(seed)
    
    # === COMPONENT 1: Capacity (can they manage debt mathematically?) ===
    capacity = (
        0.40 * features['numeracy_score'] +
        0.35 * features['financial_literacy_score'] +
        0.25 * features['CRT_score']
    )
    
    # === COMPONENT 2: Intention (do they want to repay?) ===
    intention = (
        0.35 * features['locus_of_control'] +
        0.30 * features['honesty_score'] +
        0.20 * features['social_capital_score'] +
        0.15 * features['reciprocity_norm']
    )
    
    # === COMPONENT 3: Character (will they persist when it's hard?) ===
    character = (
        0.35 * features['conscientiousness_score'] +
        0.30 * features['future_orientation'] +
        0.20 * features['resilience_score'] +
        0.15 * (1 - features['loss_aversion_score'])
    )
    
    # === COMPONENT 4: Risk signal (behavioral red flags) ===
    risk_signal = (
        0.40 * (1 - features['impulsivity_index']) +
        0.35 * features['engagement_score'] +
        0.25 * (1 - features['risk_consistency_flag'])
    )
    
    # Combine with domain-informed weights
    latent = (
        0.30 * capacity +
        0.28 * intention +
        0.27 * character +
        0.15 * risk_signal
    )
    
    # Add realistic noise (external shocks: health, job loss, family)
    external_shock = np.random.normal(0, 0.07, n)
    latent = latent + external_shock
    latent = np.clip(latent, 0, 1)
    
    # Sigmoid transformation — makes boundary sharper around 0.5
    repay_prob = 1 / (1 + np.exp(-9 * (latent - 0.52)))
    
    # Adjust intercept to hit target default rate
    # The 0.52 offset is calibrated to give ~72% repayment, ~28% default
    labels = np.random.binomial(1, repay_prob)
    
    actual_default_rate = 1 - labels.mean()
    print(f"Default rate: {actual_default_rate:.3f} (target: {target_default_rate})")
    
    return labels, repay_prob
```

## 5.4 Demographic Distribution

Realistic distributions reflecting Indian microfinance applicant pool:

```python
demographics = {
    'gender':          np.random.choice(['male','female','non_binary'], n, p=[0.52, 0.45, 0.03]),
    'age_group':       np.random.choice(['18-25','26-35','36-50','50+'], n, p=[0.28, 0.38, 0.24, 0.10]),
    'region':          np.random.choice(['urban','semi-urban','rural'], n, p=[0.38, 0.35, 0.27]),
    'education_level': np.random.choice(['none','primary','secondary','graduate'], n, p=[0.08, 0.22, 0.42, 0.28]),
}
```

Add slight, realistic feature-demographic correlations (education affects numeracy, age affects future orientation) to make the fairness audit non-trivial:

```python
# Education bump on numeracy (realistic, but model must NOT use education as a feature)
edu_map = {'none': -0.15, 'primary': -0.05, 'secondary': 0.05, 'graduate': 0.15}
features['numeracy_score'] += [edu_map[e] for e in demographics['education_level']]
features['numeracy_score'] = np.clip(features['numeracy_score'], 0, 1)
```

## 5.5 Validation Checks After Generation

Run these before proceeding to training:

```python
default_rate = 1 - labels.mean()
assert 0.24 <= default_rate <= 0.32, f"Default rate {default_rate:.3f} outside target 24-32%"
assert df.isnull().sum().sum() == 0, "NaN values found"
assert set(df['cohort_month'].unique()).issubset(set(range(1, 13)))
assert len(df[df['cohort_month'].between(11, 12)]) >= 1000, "Future test cohort too small"

# Feature-label correlation check (all primary features should have r > 0.10)
from scipy.stats import pointbiserialr
for col in PRIMARY_FEATURES:
    r, p = pointbiserialr(df[col], df['label'])
    if abs(r) < 0.08:
        print(f"WARNING: {col} has very low correlation with label: r={r:.3f}")

# Confirm protected attributes are NOT correlated with label beyond expected level
for col in PROTECTED_FEATURES:
    print(f"{col} mean label per group:")
    print(df.groupby(col)['label'].mean())
```

---

# 6. Local NLP Pipeline (No API)

## 6.1 Models Used (all local, no API key needed)

| Tool | Installation | Size | Purpose |
|---|---|---|---|
| `sentence-transformers` | `pip install sentence-transformers` | ~80MB (MiniLM) | Semantic embeddings of text |
| `vaderSentiment` | `pip install vaderSentiment` | <1MB | Sentiment scoring |
| `spaCy` | `pip install spacy && python -m spacy download en_core_web_sm` | ~12MB | Tokenization, POS, keyword extraction |
| `sklearn PCA` | Already in sklearn | 0MB | Dimensionality reduction of embeddings |

## 6.2 Text Feature Extraction Pipeline

```python
# backend/model/nlp_features.py

from sentence_transformers import SentenceTransformer
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import spacy
import numpy as np
from sklearn.decomposition import PCA
import joblib

# Load models once globally
sentence_model = SentenceTransformer('all-MiniLM-L6-v2')  # 80MB, runs on CPU or GPU
vader = SentimentIntensityAnalyzer()
nlp = spacy.load('en_core_web_sm')

# Keywords indicating agency and problem-solving orientation
AGENCY_VERBS = {'decided', 'found', 'solved', 'acted', 'chose', 'started', 'built',
                'worked', 'managed', 'negotiated', 'saved', 'earned', 'reduced'}
VICTIM_VERBS = {'happened', 'unable', 'couldnt', 'lost', 'failed', 'stuck', 
                'forced', 'had no choice', 'gave up'}
SOLUTION_KEYWORDS = {'cut', 'reduce', 'save', 'earn', 'borrow', 'negotiate', 
                     'plan', 'budget', 'help', 'learn', 'recover', 'rebuild'}

def extract_nlp_features(text: str) -> dict:
    """
    Extract 5 numeric features from the open-text resilience response.
    Works entirely offline — no API calls.
    """
    
    if not text or len(text.strip()) < 10:
        return _default_nlp_features()
    
    text_clean = text.strip().lower()
    doc = nlp(text)
    
    # === Feature 1: VADER sentiment compound score (-1 to +1) ===
    sentiment = vader.polarity_scores(text)['compound']
    
    # === Feature 2: Agency score ===
    # First-person active verbs / total verbs
    first_person_tokens = {token for token in doc if token.text.lower() in {'i', 'my', 'me', 'myself'}}
    active_verbs = 0
    total_verbs = 0
    for token in doc:
        if token.pos_ == 'VERB':
            total_verbs += 1
            # Check if verb is preceded or nearby a first-person token
            context_tokens = {doc[max(0, token.i-3):token.i+1]}
            if any(t.text.lower() in {'i', 'my', 'me'} for t in doc[max(0, token.i-3):token.i+1]):
                if token.lemma_ in AGENCY_VERBS:
                    active_verbs += 1
    
    agency_score = active_verbs / (total_verbs + 1)  # +1 to avoid div by zero
    
    # === Feature 3: Problem-solving flag ===
    words = set(text_clean.split())
    solution_count = len(words & SOLUTION_KEYWORDS)
    victim_count = sum(1 for v in VICTIM_VERBS if v in text_clean)
    problem_solving_flag = float(solution_count > victim_count)
    
    # === Features 4 & 5: Semantic embedding (PCA dims) ===
    # PCA is fit on training set (see train_classical.py for fitting)
    # At inference time, the saved PCA transform is applied
    embedding = sentence_model.encode([text])[0]  # shape: (384,)
    # PCA applied externally — return raw embedding here, apply PCA in predict.py
    
    return {
        'text_sentiment_compound': float(sentiment),
        'text_agency_score': float(agency_score),
        'text_problem_solving_flag': float(problem_solving_flag),
        '_embedding_raw': embedding,  # handled by predict.py
    }

def _default_nlp_features():
    """Return neutral features when text is empty or too short."""
    return {
        'text_sentiment_compound': 0.0,
        'text_agency_score': 0.3,
        'text_problem_solving_flag': 0.0,
        '_embedding_raw': np.zeros(384),
    }
```

## 6.3 PCA Training (fit on training set only)

```python
# In train_classical.py — during data preprocessing

from sklearn.decomposition import PCA

# Generate embeddings for all training samples
train_texts = df_train['q27_text'].fillna('').tolist()
embeddings = sentence_model.encode(train_texts, batch_size=64, show_progress_bar=True)
# embeddings shape: (n_train, 384)

# Fit PCA on training embeddings only
pca = PCA(n_components=2, random_state=42)
pca.fit(embeddings)
print(f"PCA explained variance: {pca.explained_variance_ratio_}")

# Transform training and test embeddings
train_pca = pca.transform(embeddings)
df_train['text_semantic_dim1'] = train_pca[:, 0]
df_train['text_semantic_dim2'] = train_pca[:, 1]

# Save PCA for inference
joblib.dump(pca, 'backend/models/text_pca.pkl')
```

---

# 7. Full ML Training Architecture

## 7.1 Training Environment Setup

```bash
# GPU setup check
python -c "import torch; print(torch.cuda.is_available()); print(torch.cuda.get_device_name(0))"

# Install all training deps
pip install scikit-learn xgboost lightgbm pytorch-tabnet optuna imbalanced-learn \
            shap dice-ml sentence-transformers vaderSentiment spacy joblib \
            torch torchvision --extra-index-url https://download.pytorch.org/whl/cu118

python -m spacy download en_core_web_sm
```

## 7.2 Preprocessing Pipeline

```python
# backend/model/preprocess.py

NUMERIC_FEATURES = [
    # Layer 1 — Psychometric
    'numeracy_score', 'CRT_score', 'financial_literacy_score',
    'future_orientation', 'delay_discounting_rate', 'risk_attitude',
    'risk_consistency_flag', 'loss_aversion_score', 'locus_of_control',
    'conscientiousness_score', 'social_capital_score', 'honesty_score',
    'resilience_score', 'reciprocity_norm',
    # Layer 2 — Behavioral
    'avg_response_time_ms', 'answer_change_rate', 'session_duration_sec',
    'dropout_count', 'scroll_hesitation_score', 'risk_response_speed_ratio',
    'typing_speed_wpm',
    # Layer 3 — NLP
    'text_sentiment_compound', 'text_agency_score', 'text_problem_solving_flag',
    'text_semantic_dim1', 'text_semantic_dim2',
    # Layer 4 — Derived
    'psychological_credit_index', 'cognitive_consistency_index',
    'repayment_intention_score', 'impulsivity_index', 'cognitive_load_index',
    'engagement_score', 'behavioral_trust_score',
]

CATEGORICAL_FEATURES = ['device_type', 'time_of_day']

PROTECTED_FEATURES = ['gender', 'age_group', 'region', 'education_level']

TARGET = 'repayment_label'

# Full preprocessing pipeline
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler, OrdinalEncoder
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer

def build_preprocessor():
    return ColumnTransformer([
        ('num', Pipeline([
            ('imputer', SimpleImputer(strategy='median')),
            ('scaler', StandardScaler()),
        ]), NUMERIC_FEATURES),
        ('cat', Pipeline([
            ('imputer', SimpleImputer(strategy='most_frequent')),
            ('encoder', OrdinalEncoder(handle_unknown='use_encoded_value', unknown_value=-1)),
        ]), CATEGORICAL_FEATURES),
    ], remainder='drop')
```

## 7.3 Data Split Strategy

Use **stratified 5-fold cross-validation** on the training months for model selection, and a **final temporal holdout** for fair comparison. The public dashboard must label this clearly: train on months 1-8, calibrate on months 9-10, test on months 11-12.

```python
from sklearn.model_selection import StratifiedKFold

# Final temporal split — use this for the results table
train_mask = df['cohort_month'].between(1, 8)
val_mask = df['cohort_month'].between(9, 10)
test_mask = df['cohort_month'].between(11, 12)

X_train, y_train, prot_train = X[train_mask], y[train_mask], protected[train_mask]
X_val, y_val, prot_val = X[val_mask], y[val_mask], protected[val_mask]
X_test, y_test, prot_test = X[test_mask], y[test_mask], protected[test_mask]

assert 'cohort_month' not in X_train.columns
assert 'application_date' not in X_train.columns

# 5-fold CV for model selection and HPO, using training months only
skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
```

### 7.3.1 Required Baselines and Loan-Officer Comparator

Before training the full ensemble, compute baselines on the exact same temporal test cohort. This creates a cleaner demo story: "random/simple → interpretable → human-style heuristic → ensemble."

| Baseline | Implementation | Expected AUC | Calibration metric | Why it matters |
|---|---|---:|---:|---|
| Majority class | Always predict repay | ~0.50 | ECE baseline | Sanity floor |
| Logistic regression | Same preprocessor, no SMOTE leakage | >0.68 | ECE < 0.08 | Interpretable ML baseline |
| Simulated loan officer | Weighted heuristic on visible psychometric + behavior features with noise | ~0.65-0.72 | ECE tracked | Human decision proxy |
| Stacking ensemble | Calibrated production model | >0.78 | ECE < 0.05 | Must beat every baseline |

```python
# backend/model/baselines.py

class SimulatedLoanOfficer:
    """Noisy expert heuristic used only as a benchmark, not as the production model."""
    def predict_proba(self, X):
        heuristic = (
            0.25 * X['numeracy_score'] +
            0.20 * X['financial_literacy_score'] +
            0.20 * X['conscientiousness_score'] +
            0.15 * X['social_capital_score'] +
            0.10 * X['honesty_score'] +
            0.10 * (1 - X['impulsivity_index'])
        )
        noisy = np.clip(heuristic + np.random.normal(0, 0.08, len(X)), 0, 1)
        return np.vstack([1 - noisy, noisy]).T
```

Save `models/baseline_metrics.json` and include these rows in `metrics.json` under a `baselines` key. Each row must include `auc_roc`, `ks_statistic`, `brier_score`, and `expected_calibration_error` so the dashboard can compare both ranking power and probability reliability.

## 7.4 Class Imbalance Handling

Use **all three strategies** and compare:

```python
from imblearn.over_sampling import SMOTE
from imblearn.combine import SMOTETomek

# Strategy 1: class_weight='balanced' in each model
# Strategy 2: SMOTE only on training fold
# Strategy 3: SMOTETomek (SMOTE + Tomek link removal) — more aggressive cleaning

X_train_smote, y_train_smote = SMOTE(
    sampling_strategy=0.5,  # minority class becomes 50% of majority
    k_neighbors=5,
    random_state=42
).fit_resample(X_train_preprocessed, y_train)

X_train_smotetomek, y_train_smotetomek = SMOTETomek(random_state=42).fit_resample(
    X_train_preprocessed, y_train
)
```

## 7.5 Classical Model Training with Optuna HPO

### Logistic Regression

```python
# No HPO needed — very few hyperparameters
lr = LogisticRegression(
    C=1.0, class_weight='balanced', max_iter=2000, 
    solver='saga', penalty='elasticnet', l1_ratio=0.5,
    random_state=42
)
```

### Random Forest — Optuna HPO

```python
import optuna
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import cross_val_score

def rf_objective(trial):
    params = {
        'n_estimators': trial.suggest_int('n_estimators', 100, 500),
        'max_depth': trial.suggest_int('max_depth', 4, 16),
        'min_samples_leaf': trial.suggest_int('min_samples_leaf', 2, 20),
        'min_samples_split': trial.suggest_int('min_samples_split', 2, 20),
        'max_features': trial.suggest_categorical('max_features', ['sqrt', 'log2', 0.5]),
        'class_weight': 'balanced',
        'random_state': 42,
        'n_jobs': -1,
    }
    model = RandomForestClassifier(**params)
    scores = cross_val_score(model, X_train_smote, y_train_smote, 
                             cv=skf, scoring='roc_auc', n_jobs=-1)
    return scores.mean()

rf_study = optuna.create_study(direction='maximize', study_name='rf_study')
rf_study.optimize(rf_objective, n_trials=80, n_jobs=1)
best_rf = RandomForestClassifier(**rf_study.best_params, random_state=42)
best_rf.fit(X_train_smote, y_train_smote)
```

### XGBoost — Optuna HPO

```python
from xgboost import XGBClassifier

def xgb_objective(trial):
    params = {
        'n_estimators': trial.suggest_int('n_estimators', 100, 600),
        'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.20, log=True),
        'max_depth': trial.suggest_int('max_depth', 3, 10),
        'subsample': trial.suggest_float('subsample', 0.5, 1.0),
        'colsample_bytree': trial.suggest_float('colsample_bytree', 0.5, 1.0),
        'min_child_weight': trial.suggest_int('min_child_weight', 1, 10),
        'gamma': trial.suggest_float('gamma', 0.0, 1.0),
        'reg_alpha': trial.suggest_float('reg_alpha', 0.0, 5.0),
        'reg_lambda': trial.suggest_float('reg_lambda', 0.5, 5.0),
        'scale_pos_weight': y_train.value_counts()[0] / y_train.value_counts()[1],
        'tree_method': 'gpu_hist',  # USE GPU
        'eval_metric': 'aucpr',
        'random_state': 42,
    }
    model = XGBClassifier(**params)
    scores = cross_val_score(model, X_train, y_train, cv=skf, scoring='roc_auc')
    return scores.mean()

xgb_study = optuna.create_study(direction='maximize', study_name='xgb_study')
xgb_study.optimize(xgb_objective, n_trials=100)
```

### LightGBM — Optuna HPO

```python
from lightgbm import LGBMClassifier

def lgbm_objective(trial):
    params = {
        'n_estimators': trial.suggest_int('n_estimators', 100, 600),
        'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.20, log=True),
        'num_leaves': trial.suggest_int('num_leaves', 20, 200),
        'max_depth': trial.suggest_int('max_depth', 3, 12),
        'min_child_samples': trial.suggest_int('min_child_samples', 5, 50),
        'subsample': trial.suggest_float('subsample', 0.5, 1.0),
        'colsample_bytree': trial.suggest_float('colsample_bytree', 0.5, 1.0),
        'reg_alpha': trial.suggest_float('reg_alpha', 0.0, 5.0),
        'reg_lambda': trial.suggest_float('reg_lambda', 0.5, 5.0),
        'class_weight': 'balanced',
        'device': 'gpu',  # USE GPU
        'random_state': 42,
        'verbose': -1,
    }
    model = LGBMClassifier(**params)
    scores = cross_val_score(model, X_train, y_train, cv=skf, scoring='roc_auc')
    return scores.mean()

lgbm_study = optuna.create_study(direction='maximize', study_name='lgbm_study')
lgbm_study.optimize(lgbm_objective, n_trials=100)
```

## 7.6 Neural Network Training (GPU)

### TabNet (Attention-Based Tabular Model)

TabNet is SOTA for tabular data. Uses sequential attention to select which features to focus on at each step — produces its own built-in feature importance per instance.

```python
# backend/model/train_neural.py

from pytorch_tabnet.tab_model import TabNetClassifier
import torch

device = 'cuda' if torch.cuda.is_available() else 'cpu'
print(f"Training on: {device}")

tabnet = TabNetClassifier(
    n_d=32,           # Width of decision step (try 32–64)
    n_a=32,           # Width of attention embedding
    n_steps=5,        # Number of sequential attention steps
    gamma=1.5,        # Coefficient for feature reusage
    n_independent=2,  # Number of independent GLU layers per step
    n_shared=2,       # Number of shared GLU layers
    lambda_sparse=1e-4,  # Sparsity regularization
    optimizer_fn=torch.optim.Adam,
    optimizer_params={'lr': 2e-3, 'weight_decay': 1e-5},
    scheduler_params={'step_size': 50, 'gamma': 0.9},
    scheduler_fn=torch.optim.lr_scheduler.StepLR,
    mask_type='sparsemax',  # or 'entmax'
    device_name=device,
    verbose=1,
)

tabnet.fit(
    X_train=X_train_smote.astype(np.float32),
    y_train=y_train_smote,
    eval_set=[(X_val.astype(np.float32), y_val)],
    eval_metric=['auc'],
    max_epochs=300,
    patience=50,        # Early stopping
    batch_size=1024,
    virtual_batch_size=128,
    num_workers=0,
    drop_last=False,
)

tabnet.save_model('backend/models/tabnet')
```

### MLP (PyTorch, Residual Architecture)

```python
# backend/model/mlp_model.py

import torch
import torch.nn as nn

class ResidualBlock(nn.Module):
    def __init__(self, dim, dropout=0.3):
        super().__init__()
        self.block = nn.Sequential(
            nn.Linear(dim, dim),
            nn.BatchNorm1d(dim),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(dim, dim),
            nn.BatchNorm1d(dim),
        )
        self.activation = nn.GELU()
    
    def forward(self, x):
        return self.activation(x + self.block(x))

class CreditScoreMLP(nn.Module):
    def __init__(self, input_dim, hidden_dims=[256, 128, 64], dropout=0.30):
        super().__init__()
        layers = [nn.Linear(input_dim, hidden_dims[0]),
                  nn.BatchNorm1d(hidden_dims[0]),
                  nn.GELU(),
                  nn.Dropout(dropout)]
        for i in range(len(hidden_dims) - 1):
            layers.append(ResidualBlock(hidden_dims[i], dropout))
            layers.append(nn.Linear(hidden_dims[i], hidden_dims[i+1]))
            layers.append(nn.BatchNorm1d(hidden_dims[i+1]))
            layers.append(nn.GELU())
            layers.append(nn.Dropout(dropout))
        layers.append(nn.Linear(hidden_dims[-1], 1))
        self.net = nn.Sequential(*layers)
    
    def forward(self, x):
        return self.net(x)

# Training loop
def train_mlp(X_train, y_train, X_val, y_val, input_dim, epochs=200, lr=1e-3):
    model = CreditScoreMLP(input_dim=input_dim).to(device)
    
    # Weighted BCE for imbalanced classes
    pos_weight = torch.tensor([y_train.value_counts()[0] / y_train.value_counts()[1]]).to(device)
    criterion = nn.BCEWithLogitsLoss(pos_weight=pos_weight)
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs)
    
    best_val_auc = 0
    patience_count = 0
    
    for epoch in range(epochs):
        model.train()
        # Training step ...
        
        model.eval()
        with torch.no_grad():
            val_probs = torch.sigmoid(model(X_val_tensor)).cpu().numpy()
        val_auc = roc_auc_score(y_val, val_probs)
        
        if val_auc > best_val_auc:
            best_val_auc = val_auc
            torch.save(model.state_dict(), 'backend/models/mlp_best.pt')
            patience_count = 0
        else:
            patience_count += 1
            if patience_count >= 30:  # Early stopping
                print(f"Early stopping at epoch {epoch}")
                break
        
        scheduler.step()
    
    return model
```

## 7.7 Stacking Ensemble

The stacking ensemble uses out-of-fold predictions from all base models as features for a meta-learner. This avoids information leakage.

```python
# backend/model/train_stacking.py

from sklearn.ensemble import StackingClassifier

# All base models (already optimized)
base_estimators = [
    ('lr',     best_logistic),
    ('rf',     best_rf),
    ('xgb',    best_xgb),
    ('lgbm',   best_lgbm),
    # TabNet and MLP are wrapped in a sklearn-compatible wrapper
    ('tabnet', TabNetSklearnWrapper(tabnet_model)),
    ('mlp',    MLPSklearnWrapper(mlp_model)),
]

# Meta-learner: Logistic Regression (interpretable, prevents overfitting)
meta_learner = LogisticRegression(C=0.5, random_state=42)

stacking = StackingClassifier(
    estimators=base_estimators,
    final_estimator=meta_learner,
    cv=5,                  # Out-of-fold predictions for training meta-learner
    stack_method='predict_proba',
    passthrough=False,     # Only use model predictions, not original features
    n_jobs=-1,
)

stacking.fit(X_train_smote, y_train_smote)
```

## 7.8 Probability Calibration

Raw model probabilities are not well-calibrated. Calibration makes predict_proba(X) actually mean "this borrower has a P% chance of repaying."

```python
from sklearn.calibration import CalibratedClassifierCV, calibration_curve
import matplotlib.pyplot as plt

# Isotonic regression calibration (non-parametric, better than Platt for large data)
calibrated_stacking = CalibratedClassifierCV(
    stacking, 
    method='isotonic', 
    cv='prefit'  # already fitted
)
calibrated_stacking.fit(X_val, y_val)  # Use validation set for calibration

# Evaluate calibration quality
prob_true, prob_pred = calibration_curve(y_test, calibrated_stacking.predict_proba(X_test)[:,1], n_bins=10)
# Plot and save calibration curve — should be close to the diagonal

joblib.dump(calibrated_stacking, 'backend/models/calibrated_stacking.pkl')
```

## 7.9 SHAP Explainability

```python
# backend/model/explain.py

import shap

# For tree-based models (RF, XGBoost, LightGBM)
# Use the RF as the SHAP model since it's the most explainable base learner
rf_pipeline = Pipeline([
    ('preprocessor', preprocessor),
    ('model', best_rf),
])
rf_pipeline.fit(X_train, y_train)

# TreeExplainer is fast even for 10k records
explainer = shap.TreeExplainer(
    rf_pipeline.named_steps['model'],
    data=shap.sample(X_train_preprocessed, 200),  # background data for base values
    feature_perturbation='interventional',
)

# Global SHAP values on test set
shap_values = explainer.shap_values(X_test_preprocessed)
# shap_values[1] = SHAP values for class 1 (repaid)

# Save global importance
feature_names = NUMERIC_FEATURES + CATEGORICAL_FEATURES
global_importance = {
    name: float(np.abs(shap_values[1][:, i]).mean())
    for i, name in enumerate(feature_names)
}
global_importance_sorted = dict(sorted(global_importance.items(), key=lambda x: x[1], reverse=True))

with open('backend/models/global_importance.json', 'w') as f:
    json.dump(global_importance_sorted, f, indent=2)

# Save SHAP summary plot (top 15 features, beeswarm)
shap.summary_plot(shap_values[1], X_test_preprocessed, 
                  feature_names=feature_names, max_display=15, show=False)
plt.savefig('backend/models/shap_summary.png', dpi=150, bbox_inches='tight')
plt.close()

# Save explainer for inference
joblib.dump(explainer, 'backend/models/shap_explainer.pkl')

# Per-user explanation function
def explain_user(user_features_df: pd.DataFrame) -> list:
    """Returns top 6 SHAP factors for a single user."""
    X_proc = preprocessor.transform(user_features_df)
    sv = explainer.shap_values(X_proc)[1][0]  # class 1, first (only) row
    
    factors = []
    for i, (name, value) in enumerate(zip(feature_names, sv)):
        factors.append({
            'feature': name,
            'shap_value': round(float(value), 4),
            'direction': 'positive' if value > 0 else 'negative',
            'feature_value': round(float(user_features_df.iloc[0][name] if name in user_features_df.columns else 0), 3),
            'display_name': name.replace('_', ' ').title(),
        })
    
    return sorted(factors, key=lambda x: abs(x['shap_value']), reverse=True)[:6]
```

## 7.10 Counterfactual Explanations with DICE-ML

SHAP answers "what drove my score?" DICE-ML answers the more useful applicant question: "what would need to change for me to reach the next tier?"

Counterfactuals must only use **actionable mutable features**. Never suggest changing protected attributes, region, device type, or demographic metadata.

```python
# backend/model/counterfactuals.py

import dice_ml

ACTIONABLE_FEATURES = [
    'numeracy_score', 'financial_literacy_score', 'future_orientation',
    'conscientiousness_score', 'social_capital_score', 'engagement_score',
    'avg_response_time_ms', 'answer_change_rate', 'text_agency_score',
]

IMMUTABLE_FEATURES = [
    'gender', 'age_group', 'region', 'education_level',
    'device_type', 'time_of_day', 'cohort_month', 'application_date',
]

def build_dice_explainer(train_df, model_pipeline):
    data = dice_ml.Data(
        dataframe=train_df,
        continuous_features=ACTIONABLE_FEATURES,
        outcome_name='repayment_label',
    )
    model = dice_ml.Model(model=model_pipeline, backend='sklearn')
    return dice_ml.Dice(data, model, method='random')

def generate_counterfactual_actions(user_features_df, dice_exp, desired_probability=0.70):
    """Return 2-3 plain-English actions likely to move the applicant to the next score tier."""
    cf = dice_exp.generate_counterfactuals(
        user_features_df,
        total_CFs=3,
        desired_class='opposite',
        features_to_vary=ACTIONABLE_FEATURES,
    )
    return format_counterfactuals(cf.cf_examples_list[0].final_cfs_df, user_features_df)
```

Save `models/dice_explainer.pkl`. The `/api/score` response should include `counterfactual_actions`, each with `{feature, current_value, suggested_value, estimated_score_gain, plain_language}`.

## 7.11 Metrics Computation

```python
# backend/model/evaluate.py

from sklearn.metrics import (
    roc_auc_score, average_precision_score, f1_score,
    precision_score, recall_score, brier_score_loss,
    confusion_matrix, classification_report
)
from scipy.stats import ks_2samp
import numpy as np

def compute_all_metrics(model, X_test, y_test, model_name: str) -> dict:
    y_prob = model.predict_proba(X_test)[:, 1]
    y_pred = (y_prob >= optimal_threshold(y_prob, y_test)).astype(int)
    
    # KS Statistic (standard in credit scoring)
    defaulters_scores = y_prob[y_test == 0]
    repayers_scores = y_prob[y_test == 1]
    ks_stat, _ = ks_2samp(defaulters_scores, repayers_scores)
    
    # Gini coefficient (credit industry standard)
    auc = roc_auc_score(y_test, y_prob)
    gini = 2 * auc - 1
    
    return {
        'model': model_name,
        'auc_roc': round(auc, 4),
        'pr_auc': round(average_precision_score(y_test, y_prob), 4),
        'f1_macro': round(f1_score(y_test, y_pred, average='macro'), 4),
        'precision': round(precision_score(y_test, y_pred), 4),
        'recall': round(recall_score(y_test, y_pred), 4),
        'brier_score': round(brier_score_loss(y_test, y_prob), 4),
        'expected_calibration_error': round(expected_calibration_error(y_test, y_prob), 4),
        'ks_statistic': round(ks_stat, 4),
        'gini_coefficient': round(gini, 4),
        'optimal_threshold': round(optimal_threshold(y_prob, y_test), 3),
    }

def expected_calibration_error(y_true, y_prob, n_bins=10):
    """Weighted average absolute gap between predicted and observed repayment rates."""
    bins = np.linspace(0.0, 1.0, n_bins + 1)
    bin_ids = np.digitize(y_prob, bins[1:-1], right=True)
    ece = 0.0
    for bin_id in range(n_bins):
        mask = bin_ids == bin_id
        if not np.any(mask):
            continue
        bin_confidence = y_prob[mask].mean()
        bin_accuracy = y_true[mask].mean()
        ece += (mask.mean()) * abs(bin_accuracy - bin_confidence)
    return float(ece)

def optimal_threshold(y_prob, y_true):
    """Find threshold that maximises F1."""
    from sklearn.metrics import f1_score
    thresholds = np.linspace(0.2, 0.8, 60)
    f1s = [f1_score(y_true, y_prob >= t) for t in thresholds]
    return thresholds[np.argmax(f1s)]
```

## 7.12 Population Stability Index (PSI) Drift Detection

PSI compares the feature distribution in training months against the future test cohort. It is lightweight enough for this project and impressive on the dashboard because it tells evaluators whether the model is stable under population shift.

```python
# backend/model/drift.py

def calculate_psi(expected, actual, buckets=10):
    """PSI > 0.20 indicates meaningful drift; PSI > 0.30 is a retraining alert."""
    expected_perc, bin_edges = np.histogram(expected, bins=buckets, range=(0, 1), density=False)
    actual_perc, _ = np.histogram(actual, bins=bin_edges, density=False)
    expected_perc = np.clip(expected_perc / max(expected_perc.sum(), 1), 1e-6, 1)
    actual_perc = np.clip(actual_perc / max(actual_perc.sum(), 1), 1e-6, 1)
    return float(np.sum((actual_perc - expected_perc) * np.log(actual_perc / expected_perc)))

def build_psi_report(train_df, test_df, feature_names):
    report = []
    for feature in feature_names:
        psi = calculate_psi(train_df[feature], test_df[feature])
        report.append({
            'feature': feature,
            'psi': round(psi, 4),
            'status': 'alert' if psi > 0.30 else 'watch' if psi > 0.20 else 'stable',
        })
    return sorted(report, key=lambda row: row['psi'], reverse=True)
```

Save `models/psi_report.json` with top drifted features, overall max PSI, and a dashboard verdict.

---

# 8. Fairness Audit System

## 8.1 Metrics Computed

Four fairness frameworks are evaluated independently:

### Demographic Parity
Does the model approve similar proportions across groups?
```python
approval_rate = (predicted_score >= 600).mean()  # 600 = "Fair" band threshold
# Flag if any group's approval rate deviates >10% from the mean
```

### Equalized Odds
Are FPR and FNR equal across groups?
```python
# FPR: how often we approve defaulters (costly to lender)
# FNR: how often we reject repayers (costly to excluded applicants)
# Equalized odds = FPR equality AND FNR equality
```

### Calibration Parity
Is a score of 700 equally meaningful for men and women?
```python
# Use calibration_curve per group
# Plot all groups on same chart — should overlay closely
```

### Individual Fairness Proxy
Two similar individuals should get similar scores.
```python
# Compute pairwise score difference for demographically different but
# psychometrically similar pairs (cosine similarity on features > 0.90)
# Flag if score difference > 50 points for similar individuals
```

## 8.2 Full Report Structure

```python
# backend/model/fairness_audit.py

def run_full_fairness_audit(model, X_test, y_test, protected_test) -> dict:
    y_prob = model.predict_proba(X_test)[:, 1]
    y_pred = (y_prob >= 0.45).astype(int)
    scores = probability_to_score(y_prob)
    overall_auc = roc_auc_score(y_test, y_prob)
    
    report = {
        'overall_auc': round(overall_auc, 4),
        'overall_approval_rate': round(y_pred.mean(), 4),
        'overall_default_rate': round(1 - y_test.mean(), 4),
        'groups': {},
        'worst_auc_gap': 0.0,
        'flagged_groups': [],
        'verdict': '',
    }
    
    for attr in ['gender', 'age_group', 'region', 'education_level']:
        report['groups'][attr] = {}
        for val in protected_test[attr].unique():
            mask = protected_test[attr] == val
            n = mask.sum()
            if n < 30:  # Skip very small subgroups
                continue
            
            sub_prob = y_prob[mask]
            sub_true = y_test[mask]
            sub_pred = y_pred[mask]
            sub_scores = scores[mask]
            
            if sub_true.nunique() < 2:
                continue
            
            auc = roc_auc_score(sub_true, sub_prob)
            tn, fp, fn, tp = confusion_matrix(sub_true, sub_pred).ravel()
            
            auc_gap = abs(auc - overall_auc)
            if auc_gap > report['worst_auc_gap']:
                report['worst_auc_gap'] = round(auc_gap, 4)
            
            flag = 'red' if auc_gap > 0.07 else ('yellow' if auc_gap > 0.04 else 'green')
            if flag != 'green':
                report['flagged_groups'].append(f"{attr}={val}")
            
            report['groups'][attr][val] = {
                'n_samples': int(n),
                'auc': round(auc, 4),
                'auc_gap_from_overall': round(auc_gap, 4),
                'approval_rate': round(sub_pred.mean(), 4),
                'fpr': round(fp / (fp + tn + 1e-9), 4),
                'fnr': round(fn / (fn + tp + 1e-9), 4),
                'mean_score': round(float(sub_scores.mean()), 1),
                'flag': flag,
            }
    
    # Verdict
    if not report['flagged_groups']:
        report['verdict'] = "Model shows acceptable fairness across all tested demographic groups. No subgroup shows AUC deviation >4% from the overall model."
    else:
        report['verdict'] = f"Model requires attention for: {', '.join(report['flagged_groups'])}. These groups show AUC deviation beyond threshold. Recommend targeted feature collection or separate calibration."
    
    with open('backend/models/fairness_report.json', 'w') as f:
        json.dump(report, f, indent=2)
    
    return report
```

---

# 9. FastAPI Backend — Complete Spec

## 9.1 Startup and Model Loading

```python
# backend/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import joblib, json, logging

# Global model state — loaded once at startup
MODEL_CACHE = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load all heavy assets at startup, not per request."""
    logging.info("Loading model artifacts...")
    MODEL_CACHE['model'] = joblib.load('models/calibrated_stacking.pkl')
    MODEL_CACHE['preprocessor'] = joblib.load('models/preprocessor.pkl')
    MODEL_CACHE['shap_explainer'] = joblib.load('models/shap_explainer.pkl')
    MODEL_CACHE['dice_explainer'] = joblib.load('models/dice_explainer.pkl')
    MODEL_CACHE['text_pca'] = joblib.load('models/text_pca.pkl')
    with open('models/metrics.json') as f:
        MODEL_CACHE['metrics'] = json.load(f)
    with open('models/baseline_metrics.json') as f:
        MODEL_CACHE['baselines'] = json.load(f)
    with open('models/fairness_report.json') as f:
        MODEL_CACHE['fairness'] = json.load(f)
    with open('models/global_importance.json') as f:
        MODEL_CACHE['importance'] = json.load(f)
    with open('models/psi_report.json') as f:
        MODEL_CACHE['psi'] = json.load(f)
    logging.info("All artifacts loaded. Server ready.")
    yield
    MODEL_CACHE.clear()

app = FastAPI(title="AlterScore API", version="1.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:3000"], 
                   allow_methods=["*"], allow_headers=["*"])
```

## 9.2 Complete Route List

| Method | Endpoint | Description | Response |
|---|---|---|---|
| `GET` | `/api/health` | Startup check + model loaded status | `{status, model_loaded, version}` |
| `POST` | `/api/score` | Submit answers → credit score | Full score response |
| `GET` | `/api/model-stats` | All production models × 10 metrics | metrics.json contents |
| `GET` | `/api/baseline-comparison` | Majority → logistic → loan officer → ensemble, including ECE calibration metric | baseline_metrics.json |
| `GET` | `/api/fairness-report` | Full fairness audit results | fairness_report.json |
| `GET` | `/api/drift-report` | PSI drift report for train vs future test cohorts | psi_report.json |
| `GET` | `/api/global-importance` | SHAP feature importance ranking | Top 15 features with values |
| `GET` | `/api/score-distribution` | Score histogram for 10k population | Histogram buckets + stats |
| `GET` | `/api/roc-data` | ROC curve points for all models | Points arrays per model |
| `GET` | `/api/pr-curve` | Precision-Recall curves | Points arrays per model |
| `GET` | `/api/calibration-curve` | Calibration curve data | Fraction positive vs mean predicted |
| `GET` | `/api/confusion-matrix` | Confusion matrix at optimal threshold | TP/FP/FN/TN + derived rates |

## 9.3 Score Endpoint — Full Spec

```python
# backend/routes/score.py

from pydantic import BaseModel, Field, validator
from fastapi import APIRouter, HTTPException
import uuid, datetime, json

router = APIRouter()

class AnswerPayload(BaseModel):
    # Section A — Financial Thinking (6 Qs)
    numeracy_q1: int = Field(..., ge=0, le=10000, description="Loan repayment answer in ₹")
    numeracy_q2: float = Field(..., ge=0, le=10000)
    numeracy_q3: float = Field(..., ge=0, le=100000)
    financial_literacy_q1: int = Field(..., ge=0, le=3)   # MCQ index
    financial_literacy_q2: int = Field(..., ge=0, le=2)
    conscientiousness_q1: int = Field(..., ge=1, le=5)    # Likert
    
    # Section B — Risk & Decisions (7 Qs)
    CRT_q1: float = Field(..., ge=0, le=1000)
    CRT_q2: float = Field(..., ge=0, le=1000)
    CRT_q3: int = Field(..., ge=1, le=48)
    future_orient_q1: int = Field(..., ge=0, le=1)  # Binary choice
    future_orient_q2: int = Field(..., ge=0, le=1)
    future_orient_q3: int = Field(..., ge=1, le=5)  # Likert
    risk_q1: int = Field(..., ge=0, le=1)           # Binary choice
    risk_q2: int = Field(..., ge=0, le=1)
    
    # Section C — Character & Community (8 Qs)
    locus_q1: int = Field(..., ge=0, le=2)          # MCQ index (0/1/2)
    locus_q2: int = Field(..., ge=0, le=2)
    locus_q3: int = Field(..., ge=1, le=5)           # Likert
    social_capital_q1: int = Field(..., ge=0, le=3)  # 0/1-2/3-5/5+ mapped to 0-3
    social_capital_q2: int = Field(..., ge=0, le=2)
    social_capital_q3: int = Field(..., ge=0, le=2)
    resilience_q1: int = Field(..., ge=1, le=5)
    resilience_q2: int = Field(..., ge=1, le=5)
    resilience_q3: int = Field(..., ge=0, le=3)     # MCQ
    loss_aversion_q1: int = Field(..., ge=0, le=2)
    
    # Section D — Honesty & Consistency (6 Qs incl traps)
    honesty_trap_q1: int = Field(..., ge=1, le=5)
    honesty_trap_q2: int = Field(..., ge=1, le=5)
    future_orient_repeat: int = Field(..., ge=0, le=1)  # Repeat of future_orient_q1
    locus_repeat: int = Field(..., ge=0, le=2)          # Repeat of locus_q1
    reciprocity_q1: int = Field(..., ge=1, le=5)
    reciprocity_q2: int = Field(..., ge=0, le=2)
    
    # Open text question
    q27_resilience_text: str = Field(..., min_length=0, max_length=1000)

class BehavioralPayload(BaseModel):
    avg_response_time_ms: float = Field(..., ge=100, le=120000)
    answer_change_rate: float = Field(..., ge=0, le=1)
    session_duration_sec: float = Field(..., ge=0, le=7200)
    dropout_count: int = Field(..., ge=0, le=20)
    scroll_hesitation_score: float = Field(..., ge=0, le=1)
    risk_response_speed_ratio: float = Field(..., ge=0, le=5)
    time_of_day: str = Field(..., pattern="^(morning|afternoon|evening|night)$")
    device_type: str = Field(..., pattern="^(mobile|desktop|tablet)$")
    typing_speed_wpm: float = Field(default=0.0, ge=0, le=200)

class ScoreRequest(BaseModel):
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    answers: AnswerPayload
    behavioral: BehavioralPayload

class ScoreResponse(BaseModel):
    session_id: str
    credit_score: int
    risk_band: str
    repayment_probability: float
    percentile: int          # What % of population scores lower than this
    explanation: list        # Top 6 SHAP factors
    counterfactual_actions: list  # 2-3 DICE-ML actions to improve tier
    loan_eligibility: str
    improvement_tips: list   # 2-3 actionable tips
    timestamp: str

@router.post("/score", response_model=ScoreResponse)
async def compute_score(request: ScoreRequest):
    try:
        # 1. Parse answers into features
        features = parse_answers(request.answers)
        
        # 2. Add behavioral features
        features.update(parse_behavioral(request.behavioral))
        
        # 3. Extract NLP features from open text (local, no API)
        nlp_feats = extract_nlp_features(request.answers.q27_resilience_text)
        embedding = nlp_feats.pop('_embedding_raw')
        pca_dims = MODEL_CACHE['text_pca'].transform(embedding.reshape(1, -1))[0]
        nlp_feats['text_semantic_dim1'] = float(pca_dims[0])
        nlp_feats['text_semantic_dim2'] = float(pca_dims[1])
        features.update(nlp_feats)
        
        # 4. Compute derived features
        features.update(compute_derived_features(features))
        
        # 5. Build DataFrame and preprocess
        feature_df = pd.DataFrame([features])[NUMERIC_FEATURES + CATEGORICAL_FEATURES]
        X_proc = MODEL_CACHE['preprocessor'].transform(feature_df)
        
        # 6. Predict
        repay_prob = float(MODEL_CACHE['model'].predict_proba(X_proc)[0][1])
        
        # 7. Map to credit score
        credit_score = probability_to_score(repay_prob)
        risk_band = get_risk_band(credit_score)
        percentile = compute_percentile(credit_score)  # from population distribution
        
        # 8. SHAP explanation
        explanation = explain_user(feature_df, MODEL_CACHE['shap_explainer'], 
                                   MODEL_CACHE['preprocessor'])
        
        # 9. Counterfactual actions and tips
        counterfactual_actions = generate_counterfactual_actions(
            feature_df, MODEL_CACHE['dice_explainer']
        )
        tips = generate_tips(explanation)
        
        # 10. Log request
        log_request(request.session_id, credit_score, repay_prob)
        
        return ScoreResponse(
            session_id=request.session_id,
            credit_score=credit_score,
            risk_band=risk_band,
            repayment_probability=round(repay_prob, 4),
            percentile=percentile,
            explanation=explanation,
            counterfactual_actions=counterfactual_actions,
            loan_eligibility=get_loan_eligibility(credit_score),
            improvement_tips=tips,
            timestamp=datetime.datetime.utcnow().isoformat(),
        )
    
    except Exception as e:
        logging.error(f"Scoring error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Scoring failed: {str(e)}")
```

## 9.4 Score Mapping Functions

```python
# backend/model/score_mapper.py

import numpy as np

def probability_to_score(prob_repay: float) -> int:
    """
    Maps repayment probability to 300-850 credit score.
    Uses log-odds scaling — industry standard.
    Calibrated so:
      prob=0.28 (avg defaulter) → score ≈ 400
      prob=0.50 (boundary)      → score ≈ 560
      prob=0.72 (avg repayer)   → score ≈ 720
      prob=0.90                 → score ≈ 810
    """
    prob_repay = np.clip(prob_repay, 0.01, 0.99)
    log_odds = np.log(prob_repay / (1 - prob_repay))
    score = 560 + (log_odds * 85)
    return int(np.clip(score, 300, 850))

def get_risk_band(score: int) -> str:
    if score >= 750: return "Excellent"
    if score >= 650: return "Good"
    if score >= 550: return "Fair"
    return "Poor"

def get_loan_eligibility(score: int) -> str:
    if score >= 750: return "Microloans up to ₹75,000 — Strong candidate"
    if score >= 650: return "Microloans up to ₹30,000 — Good candidate"
    if score >= 550: return "Microloans up to ₹12,000 — Moderate risk"
    return "Microloans up to ₹5,000 — Financial counselling recommended"

def compute_percentile(score: int) -> int:
    """Compute percentile from pre-computed population distribution."""
    # Load population CDF from training data
    # percentile_table maps score → percentile
    return int(percentile_table.get(score, 50))
```

---

# 10. React Frontend — Complete Spec

## 10.1 Page Map

```
/ (Landing)
/assessment (27-question flow, 4 sections)
/results (score + explanation — requires state from /assessment)
/dashboard (analytics for evaluators)
```

## 10.2 Global Design System

```javascript
// tailwind.config.js — extend with custom design tokens
module.exports = {
  theme: {
    extend: {
      colors: {
        navy: { 900: '#070D1A', 800: '#0A1228', 700: '#0D1A3A', 600: '#122050' },
        score: { poor: '#EF4444', fair: '#F97316', good: '#84CC16', excellent: '#22C55E' },
        accent: { blue: '#3B82F6', purple: '#8B5CF6', gold: '#F59E0B' },
      },
      fontFamily: { sans: ['Inter', 'system-ui', 'sans-serif'] },
    }
  }
}
```

## 10.3 Complete Question Data Structure

```javascript
// src/data/questions.js

export const SECTIONS = [
  { id: 'A', title: 'Financial Thinking',    icon: 'Calculator',   questionCount: 6 },
  { id: 'B', title: 'Risk & Decisions',      icon: 'Scale',        questionCount: 8 },
  { id: 'C', title: 'Character & Community', icon: 'Users',        questionCount: 10 },
  { id: 'D', title: 'Honesty & Reflection',  icon: 'Shield',       questionCount: 3 },
];

export const QUESTIONS = [
  // ─────────────── SECTION A ───────────────
  {
    id: 'numeracy_q1', section: 'A', type: 'number',
    question: 'You borrow ₹6,000 at 2.5% monthly interest. How much do you owe after 4 months?',
    hint: 'Round to nearest ₹10',
    correctAnswer: 6600,
    scoringFn: (ans) => Math.abs(ans - 6600) < 100 ? 1 : Math.abs(ans - 6600) < 300 ? 0.5 : 0,
    isRiskQuestion: false, isTrap: false,
  },
  {
    id: 'numeracy_q2', section: 'A', type: 'number',
    question: 'A wholesaler gives you 20% off on a ₹1,400 purchase. What do you pay?',
    correctAnswer: 1120,
    scoringFn: (ans) => Math.abs(ans - 1120) < 50 ? 1 : 0,
    isRiskQuestion: false, isTrap: false,
  },
  {
    id: 'numeracy_q3', section: 'A', type: 'number',
    question: 'You save ₹800 every month for 18 months. Total saved?',
    correctAnswer: 14400,
    scoringFn: (ans) => Math.abs(ans - 14400) < 200 ? 1 : 0,
    isTrap: false,
  },
  {
    id: 'financial_literacy_q1', section: 'A', type: 'mcq',
    question: 'Inflation is running at 9%. Your savings account earns 6% per year. What is happening to the real value of your savings?',
    options: [
      'Increasing — any interest is good',
      'Decreasing — inflation is outpacing your returns',
      'Staying the same — interest offsets inflation',
      'It depends on the bank',
    ],
    correctIndex: 1,
    isTrap: false,
  },
  {
    id: 'financial_literacy_q2', section: 'A', type: 'mcq',
    question: 'You invest ₹50,000 in a mutual fund. Is your principal guaranteed?',
    options: ['Yes — SEBI protects all investments', 'No — mutual funds carry market risk', 'Only if it\'s a bank mutual fund', 'Yes, for amounts under ₹5 lakh'],
    correctIndex: 1,
    isTrap: false,
  },
  {
    id: 'conscientiousness_q1', section: 'A', type: 'likert',
    question: 'I keep a written or digital record of my monthly income and expenses.',
    scale: { min: 1, max: 5, labels: ['Never', 'Rarely', 'Sometimes', 'Often', 'Always'] },
    isTrap: false,
  },

  // ─────────────── SECTION B ───────────────
  {
    id: 'CRT_q1', section: 'B', type: 'number',
    question: 'A bat and a ball together cost ₹110. The bat costs ₹100 more than the ball. How much does the ball cost? (in ₹)',
    hint: 'Take your time — most people get this wrong on first instinct',
    correctAnswer: 5,
    scoringFn: (ans) => Math.abs(ans - 5) < 2 ? 1 : 0,
    isTrap: false,
  },
  {
    id: 'CRT_q2', section: 'B', type: 'number',
    question: '5 machines take exactly 5 minutes to make 5 widgets. How many minutes would it take 100 machines to make 100 widgets?',
    correctAnswer: 5,
    scoringFn: (ans) => Math.abs(ans - 5) < 1 ? 1 : 0,
    isTrap: false,
  },
  {
    id: 'CRT_q3', section: 'B', type: 'number',
    question: 'A lily pad patch doubles in size every day. It fills an entire lake in 48 days. How many days does it take to fill half the lake?',
    correctAnswer: 47,
    scoringFn: (ans) => Math.abs(ans - 47) < 1 ? 1 : 0,
    isTrap: false,
  },
  {
    id: 'future_orient_q1', section: 'B', type: 'binary_choice',
    question: 'Which do you prefer?',
    options: ['₹500 right now', '₹720 in exactly 4 weeks'],
    futurePreferIndex: 1,
    isRiskQuestion: false, isTrap: false,
  },
  {
    id: 'future_orient_q2', section: 'B', type: 'binary_choice',
    question: 'Which do you prefer?',
    options: ['₹2,000 today', '₹3,200 in 3 months'],
    futurePreferIndex: 1,
    isTrap: false,
  },
  {
    id: 'future_orient_q3', section: 'B', type: 'likert',
    question: 'I am willing to sacrifice today\'s comfort to secure a better future for myself.',
    scale: { min: 1, max: 5, labels: ['Strongly Disagree', 'Disagree', 'Neutral', 'Agree', 'Strongly Agree'] },
    isTrap: false,
  },
  {
    id: 'risk_q1', section: 'B', type: 'binary_choice',
    question: 'Which do you prefer?',
    options: ['A guaranteed ₹400', 'A 60% chance of winning ₹800 (40% chance of nothing)'],
    isRiskQuestion: true, isTrap: false,
  },
  {
    id: 'loss_aversion_q1', section: 'B', type: 'mcq',
    question: 'Your small business has been losing ₹1,200 a month for 5 months. What do you do?',
    options: [
      'Close it now and cut further losses',
      'Give it 3 more months — things might turn around',
      'Invest more money to try to recover the losses',
      'Ask for outside help immediately',
    ],
    lossAversionScores: [0.0, 0.5, 1.0, 0.2],
    isTrap: false,
  },

  // ─────────────── SECTION C ───────────────
  {
    id: 'locus_q1', section: 'C', type: 'mcq',
    question: 'Financial success in life is mostly determined by:',
    options: [
      'Hard work, discipline, and smart decisions',
      'Luck, connections, and who you know',
      'The circumstances you were born into',
    ],
    internalLocusIndex: 0,
    isTrap: false,
  },
  {
    id: 'locus_q2', section: 'C', type: 'mcq',
    question: 'If you struggled to repay a loan, it would most likely be because of:',
    options: [
      'Your own financial mismanagement',
      'Unexpected external events or bad luck',
      'The lender setting unfair terms',
    ],
    internalLocusIndex: 0,
    isTrap: false,
  },
  {
    id: 'locus_q3', section: 'C', type: 'likert',
    question: 'I feel that I am the main author of my own financial story.',
    scale: { min: 1, max: 5, labels: ['Strongly Disagree', 'Disagree', 'Neutral', 'Agree', 'Strongly Agree'] },
    isTrap: false,
  },
  {
    id: 'social_capital_q1', section: 'C', type: 'mcq',
    question: 'How many people in your neighbourhood or community could lend you ₹1,000 today if you needed it urgently — no paperwork required?',
    options: ['No one', '1 or 2 people', '3 to 5 people', 'More than 5 people'],
    socialScores: [0.0, 0.33, 0.67, 1.0],
    isTrap: false,
  },
  {
    id: 'social_capital_q2', section: 'C', type: 'mcq',
    question: 'Have you ever lent money to someone who repaid you fully and on time?',
    options: ["Yes, multiple times", "Yes, once", "No — they didn\'t repay", "I haven\'t lent money"],
    socialScores: [1.0, 0.8, 0.0, 0.5],
    isTrap: false,
  },
  {
    id: 'social_capital_q3', section: 'C', type: 'mcq',
    question: 'If you borrowed money from a friend and were struggling to repay, what would you do?',
    options: [
      'Tell them immediately and work out a new plan together',
      'Wait a bit longer and hope the situation improves',
      'Avoid bringing it up until I have the money',
    ],
    socialScores: [1.0, 0.4, 0.0],
    isTrap: false,
  },
  {
    id: 'resilience_q1', section: 'C', type: 'likert',
    question: 'When things get very difficult financially, I find new ways to solve the problem.',
    scale: { min: 1, max: 5, labels: ['Strongly Disagree', 'Disagree', 'Neutral', 'Agree', 'Strongly Agree'] },
    isTrap: false,
  },
  {
    id: 'resilience_q2', section: 'C', type: 'likert',
    question: 'I finish what I start, even when it gets much harder than expected.',
    scale: { min: 1, max: 5, labels: ['Strongly Disagree', 'Disagree', 'Neutral', 'Agree', 'Strongly Agree'] },
    isTrap: false,
  },
  {
    id: 'resilience_q3', section: 'C', type: 'mcq',
    question: 'When you face a major financial setback, your first instinct is to:',
    options: [
      'Find a new income source or way to earn more',
      'Cut expenses immediately to a minimum',
      'Reach out to trusted people for support',
      'Feel overwhelmed and unsure where to start',
    ],
    resilienceScores: [1.0, 0.9, 0.8, 0.0],
    isTrap: false,
  },
  {
    id: 'reciprocity_q1', section: 'C', type: 'likert',
    question: 'If someone helped me financially in the past, I feel a strong sense of obligation to help others in similar situations.',
    scale: { min: 1, max: 5, labels: ['Strongly Disagree', 'Disagree', 'Neutral', 'Agree', 'Strongly Agree'] },
    isTrap: false,
  },

  // ─────────────── SECTION D ───────────────
  {
    id: 'honesty_trap_q1', section: 'D', type: 'likert',
    question: 'I have never told even a small lie in my entire life.',
    scale: { min: 1, max: 5, labels: ['Strongly Disagree', 'Disagree', 'Neutral', 'Agree', 'Strongly Agree'] },
    isTrap: true,
    trapLogic: 'agree_high_is_suspicious',  // Score ≥4 = suspicious flag
  },
  {
    id: 'honesty_trap_q2', section: 'D', type: 'likert',
    question: 'Without fail, I always repay every single debt completely on time.',
    scale: { min: 1, max: 5, labels: ['Strongly Disagree', 'Disagree', 'Neutral', 'Agree', 'Strongly Agree'] },
    isTrap: true,
    trapLogic: 'agree_high_is_suspicious',
  },
  {
    id: 'q27_resilience_text', section: 'D', type: 'text',
    question: 'Briefly describe a time you faced a serious financial difficulty. What happened, what did you do, and what did you learn from it?',
    hint: 'Write 2–5 sentences. This helps us understand how you handle real challenges.',
    minWords: 10,
    isTrap: false,
  },
];
```

## 10.4 Assessment Page — Key Logic

```javascript
// src/pages/Assessment.jsx — key state and logic

const [state, setState] = useState({
  currentQuestionIndex: 0,
  answers: {},            // { questionId: rawAnswer }
  responseTimes: {},      // { questionId: ms }
  changeCounts: {},       // { questionId: count }
  questionStartTime: null,
  sessionStartTime: Date.now(),
  scrollEvents: 0,
  dropouts: 0,
  riskFastCount: 0,       // risk questions answered < 2000ms
});

// Compute which section the current question belongs to
const currentQ = QUESTIONS[state.currentQuestionIndex];
const currentSection = SECTIONS.find(s => s.id === currentQ.section);
const isLastInSection = QUESTIONS[state.currentQuestionIndex + 1]?.section !== currentQ.section;

// On mount + question change: record question start time
useEffect(() => {
  setState(s => ({ ...s, questionStartTime: Date.now() }));
}, [state.currentQuestionIndex]);

// Handle answer submission
const handleAnswer = (questionId, rawValue) => {
  const rt = Date.now() - state.questionStartTime;
  const q = QUESTIONS.find(q => q.id === questionId);
  
  setState(s => ({
    ...s,
    answers: { ...s.answers, [questionId]: rawValue },
    responseTimes: { ...s.responseTimes, [questionId]: rt },
    changeCounts: { 
      ...s.changeCounts, 
      [questionId]: (s.changeCounts[questionId] || 0) + (s.answers[questionId] !== undefined ? 1 : 0),
    },
    riskFastCount: s.riskFastCount + (q.isRiskQuestion && rt < 2000 ? 1 : 0),
  }));
};

// Final submission
const handleSubmit = async () => {
  const behavioral = {
    avg_response_time_ms: Object.values(state.responseTimes).reduce((a,b)=>a+b,0) / QUESTIONS.length,
    answer_change_rate: Object.values(state.changeCounts).filter(v=>v>0).length / QUESTIONS.length,
    session_duration_sec: (Date.now() - state.sessionStartTime) / 1000,
    dropout_count: state.dropouts,
    scroll_hesitation_score: Math.min(state.scrollEvents / 120, 1.0),
    risk_response_speed_ratio: Object.entries(state.responseTimes)
      .filter(([id]) => QUESTIONS.find(q=>q.id===id)?.isRiskQuestion)
      .reduce((acc, [id, rt]) => ({ sum: acc.sum+rt, count: acc.count+1 }), {sum:0,count:0}),
    time_of_day: getTimeOfDay(),
    device_type: getDeviceType(),
    typing_speed_wpm: computeTypingSpeed(state.answers['q27_resilience_text'], state.responseTimes['q27_resilience_text']),
    risk_fast_count: state.riskFastCount,
  };
  
  // POST to backend
  const response = await axios.post('/api/score', {
    session_id: generateUUID(),
    answers: state.answers,
    behavioral,
  });
  
  navigate('/results', { state: response.data });
};
```

## 10.5 Results Page Components

```
Results Page Layout (max-width 760px, centered)
│
├── Header
│   └── "Your Credit Assessment" + session timestamp
│
├── ScoreGauge (SVG arc, animated needle, count-up number)
│   ├── Score: 712
│   ├── Band: GOOD
│   └── Percentile: "Higher than 68% of applicants"
│
├── BandExplanationCard
│   └── Plain language description of what this band means
│
├── LoanEligibilityCard
│   ├── Eligibility amount
│   └── "What this means for you" text
│
├── FactorBars (horizontal SHAP waterfall)
│   ├── Title: "What drove your score"
│   ├── Top 6 factors, positive green / negative red
│   └── Each bar: feature display name + direction label + bar
│
├── ImprovementCard
│   ├── Title: "How to improve"
│   └── 2-3 tips based on lowest positive SHAP features
│
├── CounterfactualActions
│   ├── Title: "What could move you up a tier"
│   └── 2-3 DICE-ML actions with current value → suggested value
│
├── ShareCard
│   ├── Hidden/exportable score card DOM node
│   └── "Share on WhatsApp" button using html2canvas PNG export
│
└── ActionButtons
    ├── "Retake Assessment" → /assessment
    └── "View Full Methodology" → /dashboard
```

## 10.6 Dashboard Page Components

```
Dashboard Layout (max-width 1280px, 12-column grid)
│
├── Hero: "Model Analytics Dashboard" subtitle + last trained date
│
├── KPI Cards Row (4 cards)
│   ├── Overall AUC: 0.XX
│   ├── Best Model: Stacking Ensemble
│   ├── Training Records: 10,000
│   └── Features: 39
│
├── ModelComparisonTable (full width)
│   └── Production models × 10 metrics, best row highlighted
│
├── BaselineComparisonTable (full width)
│   └── Majority → logistic → simulated loan officer → stacking ensemble, with ECE
│
├── Row (2 cols, 6/6)
│   ├── FeatureImportanceChart (horizontal bar, color coded by layer)
│   └── ROCCurveChart (overlaid curves for all 7 models)
│
├── Row (2 cols, 7/5)
│   ├── ScoreDistributionHistogram (color coded by band)
│   └── CalibrationCurve (model vs perfect calibration diagonal)
│
├── DriftMonitorPanel (full width)
│   └── PSI by feature, max PSI verdict, train months 1-8 vs test months 11-12
│
├── PRCurveChart (full width, all models)
│
├── ConfusionMatrix (at optimal threshold)
│
├── FairnessAuditSection (full width)
│   ├── Overall verdict
│   ├── 4 sub-tables (gender, age, region, education)
│   └── Color coded status per subgroup
│
└── DataInspector (full width)
    ├── Sample 20 rows from test set with predictions
    └── Click row → show SHAP waterfall for that row
```

---

# 11. Complete File Structure

```
alterscore/
│
├── backend/
│   ├── main.py                        # FastAPI app, lifespan, CORS, router inclusion
│   ├── requirements.txt               # All backend dependencies
│   │
│   ├── model/
│   │   ├── generate_data.py           # Synthetic dataset generation (10k records)
│   │   ├── preprocess.py              # Feature lists, ColumnTransformer pipeline
│   │   ├── nlp_features.py            # VADER + spaCy + sentence-transformers (local)
│   │   ├── baselines.py               # Majority, logistic, simulated loan-officer baselines
│   │   ├── train_classical.py         # LR, RF, XGB, LGBM + Optuna HPO
│   │   ├── train_neural.py            # TabNet + MLP (PyTorch, GPU)
│   │   ├── train_stacking.py          # Stacking ensemble + calibration
│   │   ├── explain.py                 # SHAP explainer, global importance, per-user SHAP
│   │   ├── counterfactuals.py         # DICE-ML counterfactual explanation generator
│   │   ├── fairness_audit.py          # Full fairness report generation
│   │   ├── drift.py                   # PSI drift report generation
│   │   ├── evaluate.py                # All metrics computation
│   │   ├── answer_parser.py           # Maps raw API answers to feature values
│   │   ├── feature_engineer.py        # Derived feature computation
│   │   ├── score_mapper.py            # prob → score → band → eligibility
│   │   └── sklearn_wrappers.py        # sklearn-compatible wrappers for TabNet and MLP
│   │
│   ├── routes/
│   │   ├── score.py                   # POST /api/score
│   │   └── analytics.py               # GET /api/model-stats, fairness, roc, etc.
│   │
│   ├── models/                        # Saved model artifacts (gitignored)
│   │   ├── calibrated_stacking.pkl
│   │   ├── preprocessor.pkl
│   │   ├── shap_explainer.pkl
│   │   ├── dice_explainer.pkl
│   │   ├── text_pca.pkl
│   │   ├── tabnet_epoch_best.zip
│   │   ├── mlp_best.pt
│   │   ├── metrics.json
│   │   ├── baseline_metrics.json
│   │   ├── fairness_report.json
│   │   ├── psi_report.json
│   │   ├── global_importance.json
│   │   └── population_percentiles.json
│   │
│   ├── logs/
│   │   └── requests.jsonl             # Append-only prediction log
│   │
│   └── utils/
│       ├── logging_config.py
│       └── validators.py
│
├── frontend/
│   ├── public/
│   │   └── index.html
│   │
│   ├── src/
│   │   ├── App.jsx                    # Router setup
│   │   ├── index.js
│   │   │
│   │   ├── pages/
│   │   │   ├── Landing.jsx            # Hero, how-it-works, stats
│   │   │   ├── Assessment.jsx         # 27-question flow + telemetry capture
│   │   │   ├── Results.jsx            # Score display + explanations
│   │   │   └── Dashboard.jsx          # Full analytics for evaluators
│   │   │
│   │   ├── components/
│   │   │   ├── ScoreGauge.jsx         # SVG arc gauge with animated needle
│   │   │   ├── FactorBars.jsx         # SHAP waterfall horizontal bars
│   │   │   ├── CounterfactualActions.jsx
│   │   │   ├── ShareCard.jsx          # html2canvas export + WhatsApp share intent
│   │   │   ├── ModelComparisonTable.jsx
│   │   │   ├── BaselineComparisonTable.jsx
│   │   │   ├── DriftMonitorPanel.jsx
│   │   │   ├── FeatureImportanceChart.jsx
│   │   │   ├── ROCCurveChart.jsx
│   │   │   ├── PRCurveChart.jsx
│   │   │   ├── ScoreDistribution.jsx
│   │   │   ├── CalibrationCurve.jsx
│   │   │   ├── ConfusionMatrix.jsx
│   │   │   ├── FairnessAuditTable.jsx
│   │   │   ├── DataInspector.jsx
│   │   │   ├── SectionTransition.jsx
│   │   │   ├── QuestionCard.jsx
│   │   │   ├── ProgressBar.jsx
│   │   │   ├── LoadingSpinner.jsx
│   │   │   ├── ErrorBoundary.jsx
│   │   │   └── Navbar.jsx
│   │   │
│   │   ├── hooks/
│   │   │   ├── useFetch.js            # Generic fetch hook with loading/error
│   │   │   └── useSession.js          # Session tracking state
│   │   │
│   │   ├── utils/
│   │   │   ├── scoring.js             # Client-side answer scoring helpers
│   │   │   ├── formatting.js          # Feature name formatting, ₹ formatting
│   │   │   ├── deviceDetect.js        # Device type + time of day detection
│   │   │   └── constants.js           # API base URL, thresholds, band colors
│   │   │
│   │   └── data/
│   │       └── questions.js           # All 27 questions with metadata
│   │
│   ├── package.json
│   └── tailwind.config.js
│
├── data/                              # Generated data (gitignored)
│   ├── synthetic_dataset.csv
│   └── data_profile_report.html       # pandas-profiling report
│
├── notebooks/
│   ├── 01_eda.ipynb                   # Exploratory data analysis
│   ├── 02_model_comparison.ipynb      # Model training experiments
│   └── 03_fairness_analysis.ipynb     # Fairness deep dive
│
├── README.md
├── .env
├── .gitignore
release_runbook.md                 # Optional: manual release/demo notes
```

---

# 12. Codex Build Roadmap — Step by Step

Follow this **exact order**. Each step builds on the previous one. Do not skip ahead.

---

## PHASE 0 — Environment Setup (Day 0, 1 hour)

**Do manually, not in Codex:**
```bash
mkdir alterscore && cd alterscore
mkdir -p backend/{model,routes,models,logs,utils} frontend/src/{pages,components,hooks,utils,data} data notebooks

# Backend env
python -m venv venv && source venv/bin/activate
pip install fastapi uvicorn[standard] scikit-learn xgboost lightgbm imbalanced-learn \
            shap optuna sentence-transformers vaderSentiment spacy joblib \
            pandas numpy scipy pytorch-tabnet pydantic pandas-profiling
pip install torch --extra-index-url https://download.pytorch.org/whl/cu118
python -m spacy download en_core_web_sm

# Frontend env
cd frontend && npx create-react-app . && npm install axios recharts react-router-dom tailwindcss @headlessui/react lucide-react html2canvas
npx tailwindcss init && cd ..
```

**Verify GPU:**
```python
import torch
assert torch.cuda.is_available(), "CUDA not available"
print(torch.cuda.get_device_name(0))
```

---

## PHASE 1 — Data Generation (Day 1, AM)

### Step 1.1 — Core data generator

**Codex Prompt:**
```
Write backend/model/generate_data.py.

Generate 10,000 synthetic records for an alternative credit scoring dataset.

STEP 1: Generate 10 correlated base psychometric features using a multivariate 
normal approach. Define a 10x10 correlation matrix where:
- numeracy and CRT: r=0.50
- numeracy and financial_literacy: r=0.55
- future_orientation and conscientiousness: r=0.45
- locus_of_control and resilience: r=0.40
- honesty and social_capital: r=0.35
(See PRD section 5.1 for full correlation matrix)

Sample from multivariate normal, convert to uniform via norm.cdf(), then 
transform to Beta(2.5, 1.5) marginals using beta.ppf(). This gives realistic 
positive-skewed psychometric distributions.

STEP 2: Add secondary psychometric features:
- delay_discounting_rate: float 0-1 (Beta(1.5, 2.0))
- risk_consistency_flag: 0 or 1 (Bernoulli(0.15)) — 15% have inconsistent risk choices
- loss_aversion_score: float 0-1 (Beta(1.8, 2.5))
- reciprocity_norm: float 0-1 (Beta(2.0, 1.8))

STEP 3: Generate behavioral features:
- avg_response_time_ms: truncated normal, mean=4800, std=1800, min=500, max=25000
- answer_change_rate: Beta(1.2, 5.0) — right-skewed, most people rarely change answers
- session_duration_sec: avg_response_time_ms * num_questions * (1 + Poisson(0.3) * 0.1)
- dropout_count: Poisson(0.3), capped at 4
- scroll_hesitation_score: Beta(2.0, 1.5)
- risk_response_speed_ratio: log-normal mean=1.0, std=0.4, clipped 0.3-3.0
- time_of_day: choices['morning','afternoon','evening','night'] with p=[0.25,0.35,0.28,0.12]
- device_type: choices['mobile','desktop','tablet'] with p=[0.65,0.28,0.07]
- typing_speed_wpm: truncated normal mean=35, std=15, min=5, max=100

STEP 4: Generate synthetic Q27 text (resilience open text). Do this by:
- Creating 12 text templates ranging from high-agency/solution-focused to 
  low-agency/victim-framing
- Sampling template index based on resilience_score quintile
  (high resilience → high-agency templates)
- Adding slight word variation using random synonym substitution

STEP 4b: Extract NLP features from Q27 text:
- Load VADER and run sentiment
- Run spaCy for agency verb counting
- keyword match for problem_solving_flag
- For embeddings, just set placeholder zeros for now (PCA fit during training)

STEP 5: Compute derived features (see PRD section 4.5 formula table).

STEP 6: Generate labels using the 4-component latent variable model from PRD 
section 5.3. Target 28% default rate.

STEP 7: Generate demographics (gender, age_group, region, education_level) 
with realistic distributions. Add education bump on numeracy.

STEP 8: Assign cohort_month (1-12) and application_date. Apply mild temporal drift 
from PRD section 5.2, but never include these metadata fields in model features.

STEP 9: Save to data/synthetic_dataset.csv. 
Print: n_records, default_rate, feature stats, feature-label correlation table.
```

### Step 1.2 — Validate data quality

**Codex Prompt:**
```
Write backend/model/validate_data.py.

Load data/synthetic_dataset.csv. Run these checks and print results:

1. Shape and dtypes
2. Missing value count per column
3. Default rate (must be 24-32%)
4. Point-biserial correlation of each feature with label
   — Flag any feature with |r| < 0.05 as "too weak — consider removing"
   — Flag any with |r| > 0.65 as "possible data leakage"
5. For each numeric feature: min, max, mean, std, skewness
6. Confirm protected attributes are separate from model features
7. Confirm no protected attributes have extremely high label correlation (>0.15 is concerning)
8. Confirm cohort_month covers 1-12 and months 11-12 have enough future test samples
9. Confirm cohort_month and application_date are excluded from NUMERIC_FEATURES and CATEGORICAL_FEATURES

Also generate a pandas profiling report and save to data/data_profile_report.html.
(pip install ydata-profiling if needed)

Exit with code 1 if any critical check fails.
```

**Run and inspect before proceeding.**

---

## PHASE 2 — NLP Pipeline (Day 1, PM)

### Step 2.1 — NLP feature extractor

**Codex Prompt:**
```
Write backend/model/nlp_features.py.

This module runs entirely locally — no API calls. It uses:
- vaderSentiment for sentiment scoring
- spaCy (en_core_web_sm) for POS tagging and tokenization
- sentence-transformers (all-MiniLM-L6-v2) for semantic embeddings

Load all three models ONCE at module level (global variables), not inside functions.
This ensures they load only once when the backend starts.

Implement:

1. AGENCY_VERBS set and SOLUTION_KEYWORDS set (from PRD section 6.2)

2. extract_nlp_features(text: str) -> dict:
   Returns keys:
   - text_sentiment_compound: float -1 to 1 (VADER compound)
   - text_agency_score: float 0-1 (first-person active verbs / total verbs)
   - text_problem_solving_flag: float 0 or 1 (solution keywords > victim keywords)
   - _embedding_raw: np.array of shape (384,) from sentence_model.encode()
   
   If text is None or len < 10: return neutral defaults (0.0, 0.3, 0.0, np.zeros(384))

3. batch_extract(texts: list[str]) -> pd.DataFrame:
   Process a list of texts efficiently using sentence_model.encode(texts, batch_size=64).
   Returns DataFrame with columns: text_sentiment_compound, text_agency_score, 
   text_problem_solving_flag, and 384 embedding columns (emb_0, emb_1, ..., emb_383)
```

---

## PHASE 3 — Classical Model Training (Day 2, AM)

### Step 3.1 — Preprocessing pipeline

**Codex Prompt:**
```
Write backend/model/preprocess.py.

Define these constants (lists of strings):
NUMERIC_FEATURES = [all 33 numeric features from PRD section 4, Layers 1-4]
CATEGORICAL_FEATURES = ['device_type', 'time_of_day']
PROTECTED_FEATURES = ['gender', 'age_group', 'region', 'education_level']
TARGET = 'repayment_label'
ALL_MODEL_FEATURES = NUMERIC_FEATURES + CATEGORICAL_FEATURES

Implement build_preprocessor() that returns sklearn ColumnTransformer:
- Numeric: SimpleImputer(median) → StandardScaler
- Categorical: SimpleImputer(most_frequent) → OrdinalEncoder(handle_unknown='use_encoded_value', unknown_value=-1)

Implement load_and_split(csv_path, random_state=42):
- Load CSV
- Compute derived features (import compute_derived_features from feature_engineer.py)
- Extract NLP features by calling batch_extract from nlp_features.py
- Fit PCA(n_components=2) on training embedding columns, save to models/text_pca.pkl
- Apply PCA to add text_semantic_dim1, text_semantic_dim2 to all splits
- Temporal split: train = cohort_month 1-8, val = 9-10, test = 11-12
- Assert cohort_month and application_date are removed from model inputs before preprocessing
- Returns X_train, X_val, X_test, y_train, y_val, y_test, prot_train, prot_val, prot_test

Also implement:
fit_preprocessor(X_train) → fits and saves preprocessor to models/preprocessor.pkl
transform(preprocessor, X) → transforms X using fitted preprocessor
```

### Step 3.2 — Baseline comparators

**Codex Prompt:**
```
Write backend/model/baselines.py.

Load the temporal splits from preprocess.py.

Implement and evaluate:
1. MajorityClassBaseline — always predicts the majority training class probability.
2. LogisticRegression baseline — same preprocessor, simple class_weight='balanced', no Optuna.
3. SimulatedLoanOfficer — noisy weighted heuristic from PRD section 7.3.1.
4. Calibrated stacking ensemble placeholder row — filled later by evaluate.py.

Use compute_all_metrics from evaluate.py on the months 11-12 test set.
Save models/baseline_metrics.json with rows ordered:
majority_class, logistic_regression, simulated_loan_officer, stacking_ensemble.
Each row must include: auc_roc, ks_statistic, brier_score, expected_calibration_error.
```

### Step 3.3 — Classical model training with Optuna

**Codex Prompt:**
```
Write backend/model/train_classical.py.

Import from preprocess.py. Load data, call load_and_split().
Apply SMOTE (sampling_strategy=0.5, random_state=42) to training data only.

For each of 4 models (Logistic, RandomForest, XGBoost, LightGBM):

1. Run Optuna study with n_trials=80 for RF and LightGBM, n_trials=100 for XGBoost.
   (Use the hyperparameter search spaces exactly as defined in PRD section 7.5)
   XGBoost: set tree_method='gpu_hist' for GPU acceleration
   LightGBM: set device='gpu'

2. After HPO, retrain best model on full SMOTE-augmented training set.

3. Evaluate on the months 11-12 temporal test set using compute_all_metrics from evaluate.py.

4. Save best model to models/{model_name}_best.pkl (wrapped in full pipeline with preprocessor).

5. Save all metrics to a running dict.

After all 4 classical models are done, save metrics dict to models/classical_metrics.json.
Print final comparison table.
```

---

## PHASE 4 — Neural Network Training (Day 2, PM — use GPU)

### Step 4.1 — sklearn wrappers for PyTorch models

**Codex Prompt:**
```
Write backend/model/sklearn_wrappers.py.

Write two sklearn-compatible wrapper classes:

TabNetSklearnWrapper(BaseEstimator, ClassifierMixin):
- __init__(self, tabnet_model_path): loads model from path
- fit(X, y): no-op (already trained) — just set classes_
- predict_proba(X): returns 2-column array [prob_0, prob_1]
- predict(X): returns binary predictions

MLPSklearnWrapper(BaseEstimator, ClassifierMixin):
- __init__(self, model_path, input_dim): loads CreditScoreMLP state dict
- fit(X, y): no-op
- predict_proba(X): converts to tensor, runs forward pass, applies sigmoid, returns [1-p, p]
- predict(X): thresholds at 0.45
```

### Step 4.2 — TabNet training

**Codex Prompt:**
```
Write backend/model/train_tabnet.py.

Import TabNetClassifier from pytorch_tabnet.tab_model.
Import load_and_split and fit_preprocessor from preprocess.py.

Load the preprocessed training data (apply SMOTE).

Train TabNetClassifier with these parameters (from PRD section 7.6):
n_d=32, n_a=32, n_steps=5, gamma=1.5, n_independent=2, n_shared=2, 
lambda_sparse=1e-4, mask_type='sparsemax', device_name='cuda'

Optimizer: Adam, lr=2e-3, weight_decay=1e-5
Scheduler: StepLR, step_size=50, gamma=0.9
max_epochs=300, patience=50, batch_size=1024, virtual_batch_size=128

Fit with eval_set=[(X_val, y_val)], eval_metric=['auc'].

After training:
- Evaluate on test set, print AUC
- Save model with tabnet.save_model('models/tabnet')
- Save training/validation AUC curve to models/tabnet_training_curve.json
```

### Step 4.3 — MLP training

**Codex Prompt:**
```
Write backend/model/train_mlp.py.

Define CreditScoreMLP class (from PRD section 7.6) with ResidualBlock architecture:
- hidden_dims=[256, 128, 64]
- GELU activations, BatchNorm, Dropout(0.30)
- Residual connections within each hidden dim block

Training setup:
- Loss: BCEWithLogitsLoss with pos_weight = n_neg/n_pos
- Optimizer: AdamW, lr=1e-3, weight_decay=1e-4
- Scheduler: CosineAnnealingLR, T_max=200
- Early stopping: patience=30 on val AUC
- Batch size: 512 (adjust if OOM)
- max_epochs: 200

After training:
- Load best weights from checkpoint
- Evaluate on test set, print AUC
- Save final model state dict to models/mlp_best.pt
- Save training curves to models/mlp_training_curves.json
```

---

## PHASE 5 — Stacking Ensemble + Calibration (Day 3, AM)

### Step 5.1 — Build stacking ensemble

**Codex Prompt:**
```
Write backend/model/train_stacking.py.

Load all 4 classical best models + TabNet wrapper + MLP wrapper.
Load X_train, y_train, X_test, y_test from preprocess.py.

Build StackingClassifier:
estimators = [('lr', best_lr), ('rf', best_rf), ('xgb', best_xgb), 
              ('lgbm', best_lgbm), ('tabnet', tabnet_wrapper), ('mlp', mlp_wrapper)]
final_estimator = LogisticRegression(C=0.5, random_state=42)
cv=5, stack_method='predict_proba', passthrough=False

Fit stacking on SMOTE-augmented training data.

Then calibrate with CalibratedClassifierCV(stacking, method='isotonic', cv='prefit')
fitting on the validation set.

Evaluate calibrated model on test set using compute_all_metrics.
Compare calibrated vs uncalibrated AUC.

Save:
- models/stacking_uncalibrated.pkl
- models/calibrated_stacking.pkl (this is the production model)
Print final metrics for all 7 models together.
```

### Step 5.2 — SHAP explainability

**Codex Prompt:**
```
Write backend/model/explain.py.

Load best RF model (models/rf_best.pkl) — use this for SHAP since TreeExplainer 
works natively with RF and is fast.

Load X_train_preprocessed and X_test_preprocessed.

Initialize shap.TreeExplainer(rf_model, data=shap.sample(X_train_preprocessed, 200))

Compute SHAP values on test set (shap_values[1] = class "repaid").

Save:
1. models/global_importance.json: dict of {feature_name: mean_abs_shap}, sorted descending
2. models/shap_summary.png: beeswarm plot top 15 features (plt.savefig, dpi=150)
3. models/shap_explainer.pkl: the explainer object

Implement and test explain_user(user_features_df, explainer, preprocessor) -> list:
- Returns list of top 6 factor dicts (see PRD section 9.3)
- Each: {feature, shap_value, direction, feature_value, display_name}

Run a quick test: take the first 3 test rows and call explain_user on each, 
print the explanations to verify they look reasonable.
```

### Step 5.3 — Counterfactual explanations

**Codex Prompt:**
```
Write backend/model/counterfactuals.py.

Use dice-ml with the calibrated stacking sklearn pipeline.

Implement:
- build_dice_explainer(train_df, model_pipeline) using PRD section 7.10.
- generate_counterfactual_actions(user_features_df, dice_exp) -> list of 2-3 actions.
- format_counterfactuals(...) -> plain-English objects:
  {feature, current_value, suggested_value, estimated_score_gain, plain_language}

Only allow mutable/actionable features to vary. Explicitly exclude protected attributes,
cohort_month, application_date, device_type, and time_of_day.

Save models/dice_explainer.pkl.
Test with 3 low-score test applicants and verify suggestions are realistic.
```

### Step 5.4 — Full metrics and evaluation

**Codex Prompt:**
```
Write backend/model/evaluate.py.

Implement compute_all_metrics(model, X_test, y_test, model_name) using:
auc_roc, pr_auc, f1_macro, precision, recall, brier_score_loss, 
ks_statistic (from scipy.stats.ks_2samp on defaulter vs repayer score distributions),
gini_coefficient (= 2*auc - 1), expected_calibration_error (10 equal-width bins),
optimal_threshold (threshold that maximises F1).

Also implement:
- compute_roc_points(model, X_test, y_test) → list of {fpr, tpr} dicts (100 points)
- compute_pr_points(model, X_test, y_test) → list of {recall, precision} dicts
- compute_calibration_points(model, X_test, y_test) → list of {mean_predicted, fraction_pos}
- compute_confusion_matrix(model, X_test, y_test, threshold) → {tp, fp, fn, tn, tpr, fpr, fnr}
- compute_percentile_table(model, X_full, y_full) → dict mapping score → percentile rank

Load ALL production models, run all metrics on the months 11-12 test set, compile into models/metrics.json.
Merge in models/baseline_metrics.json under a `baselines` key for dashboard comparison.
Load calibrated_stacking and compute population_percentiles.json from full dataset.
```

### Step 5.5 — PSI drift report

**Codex Prompt:**
```
Write backend/model/drift.py.

Implement calculate_psi(expected, actual, buckets=10) and build_psi_report(train_df, test_df, feature_names)
from PRD section 7.12.

Compare train months 1-8 against test months 11-12 for every model feature.
Save models/psi_report.json:
- overall_status: stable/watch/alert
- max_psi
- top_drifted_features
- all_features table sorted by PSI descending
```

### Step 5.6 — Fairness audit

**Codex Prompt:**
```
Write backend/model/fairness_audit.py.

Implement run_full_fairness_audit (see PRD section 8.2 for exact structure).

Load calibrated_stacking.pkl, X_test, y_test, and protected_test.

For each of ['gender', 'age_group', 'region', 'education_level']:
  For each unique value in that column:
    Compute: n_samples, auc, auc_gap_from_overall, approval_rate, fpr, fnr, mean_score, flag

Also compute:
- Calibration curve per gender (2 curves, should overlay)
- Individual fairness proxy: for full-profile similar pairs using
  range-normalized similarity across the numeric scoring feature set,
  compute mean score difference — flag if > 60 points

Save models/fairness_report.json and print a readable table to console.
```

---

## PHASE 6 — FastAPI Backend (Day 3, PM)

### Step 6.1 — Answer parser

**Codex Prompt:**
```
Write backend/model/answer_parser.py.

This file maps raw API answer values (integers, floats, strings) to the 
normalised psychometric feature values (floats 0-1) that the model expects.

For each of the 27 question IDs, implement the scoring logic:
- Numeracy: partial credit if within tolerance of correct answer
- CRT: correct = 1, wrong = 0
- Likert: (value - 1) / 4 to normalize 1-5 → 0-1
- MCQ: map answer index to predefined score (see each question's scoringLogic in PRD)
- Binary choice: 0 or 1 based on which option chosen

Implement:
parse_answers(answers_dict) -> dict of feature_name: float pairs:
Returns a dict with all psychometric feature keys filled in.
Handle missing answers with sensible defaults (0.5 for likert, 0 for scored).

Also implement compute_derived_features(features_dict) -> dict:
Computes the 7 derived features from PRD section 4.5.
Returns merged dict.
```

### Step 6.2 — Main backend

**Codex Prompt:**
```
Write backend/main.py and backend/routes/score.py and backend/routes/analytics.py.

main.py:
- FastAPI app with lifespan context manager
- In lifespan startup: load calibrated_stacking.pkl, preprocessor.pkl, shap_explainer.pkl, 
  dice_explainer.pkl, text_pca.pkl, metrics.json, baseline_metrics.json, fairness_report.json, 
  psi_report.json, global_importance.json, population_percentiles.json into MODEL_CACHE dict
- Load sentence-transformers and spaCy models via nlp_features.py at startup
- CORSMiddleware for http://localhost:3000
- Include routers from routes/score.py (prefix=/api) and routes/analytics.py (prefix=/api)
- GET /api/health -> {status, model_loaded, artifacts_loaded: list, version}

routes/score.py:
- POST /api/score with full Pydantic request/response models (from PRD section 9.3)
- Full pipeline: parse_answers → compute_derived_features → extract_nlp_features → 
  apply text_pca → preprocess → predict_proba → probability_to_score → explain_user → 
  generate_counterfactual_actions → generate_tips
- Append log to logs/requests.jsonl (session_id, timestamp, score, band)
- Return full ScoreResponse

routes/analytics.py:
- GET /api/model-stats → MODEL_CACHE['metrics']
- GET /api/baseline-comparison → MODEL_CACHE['baselines']
- GET /api/fairness-report → MODEL_CACHE['fairness']  
- GET /api/drift-report → MODEL_CACHE['psi']
- GET /api/global-importance → top 15 from MODEL_CACHE['importance']
- GET /api/score-distribution → load synthetic_dataset.csv, run predict_proba on 
  all 10k rows (batch), bin into 50-point buckets, return histogram + stats
- GET /api/roc-data → from metrics.json, return points arrays for all models
- GET /api/pr-curve → return PR curve points for all models
- GET /api/calibration-curve → return calibration points
- GET /api/confusion-matrix → return confusion matrix at optimal threshold
```

---

## PHASE 7 — Frontend: Foundation (Day 4, AM)

### Step 7.1 — Project config and routing

**Codex Prompt:**
```
Set up the frontend:

1. tailwind.config.js: extend with custom colors from PRD section 10.2 
   (navy, score colors, accent colors). Configure content paths.

2. src/utils/constants.js:
   API_BASE = 'http://localhost:8000/api'
   SCORE_BANDS = { Excellent: {min:750, color:'#22C55E'}, Good: {min:650, color:'#84CC16'},
                   Fair: {min:550, color:'#F97316'}, Poor: {min:300, color:'#EF4444'} }
   FEATURE_CATEGORIES = { psychometric: [...], behavioral: [...], derived: [...], nlp: [...] }

3. src/App.jsx: React Router v6 with 4 routes (/, /assessment, /results, /dashboard).
   Wrap in ErrorBoundary. Add Navbar.

4. src/components/Navbar.jsx: Logo left, "Dashboard" link right, dark navy background.

5. src/hooks/useFetch.js: custom hook(url, options) → {data, loading, error, refetch}.
   Retry once on network failure.
```

### Step 7.2 — Question data and landing page

**Codex Prompt:**
```
1. Create src/data/questions.js with all 27 questions exactly as defined in PRD section 10.3.
   Include all metadata: section, type, options, scoringFn, isRiskQuestion, isTrap, etc.

2. Write src/pages/Landing.jsx:
   - Hero: dark navy background, CSS grid dot pattern overlay
   - "Get a Credit Score Without a Bank Account" H1, subtitle, "Start Assessment" CTA
   - Animated counter stats: 1.4B unbanked, 5 minutes, 27 questions, 39 features
   - "How It Works" 3-step section with icons from lucide-react
   - "What We Measure" 4 cards (Numeracy, Time Preference, Social Capital, Behavioral)
   - "Research Backed" section citing IFC and World Bank research
   - Footer
   Use IntersectionObserver for section fade-in animations.
   Fully responsive.
```

---

## PHASE 8 — Frontend: Assessment (Day 4, PM)

**Codex Prompt:**
```
Write src/pages/Assessment.jsx and related components.

Assessment.jsx:
- State: currentQuestionIndex, answers{}, responseTimes{}, changeCounts{}, 
  scrollEvents, dropouts, riskFastCount, sessionStartTime, questionStartTime, isSubmitting
- Tracks: visibilitychange for dropouts, scroll events, per-question timing
- Renders: ProgressBar + SectionLabel + QuestionCard + Navigation buttons
- Between sections: shows SectionTransition fullscreen component (3 sec or click)
- On submit: builds behavioral payload, POSTs to /api/score, navigates to /results
- Shows LoadingSpinner during POST

ProgressBar.jsx: Props{current, total}. Two-layer bar: section progress (major) 
and question progress (minor). Shows "Question 14 of 27".

SectionTransition.jsx: Fullscreen overlay. Section number, title, icon (lucide), 
question count. Fade-in animation. Auto-advances after 3 seconds or "Continue" click.

QuestionCard.jsx: Props{question, value, onChange}.
Renders correct input type:
- 'number': large number input with ₹ prefix where relevant
- 'mcq': large tappable button grid (2 cols on mobile, single col if >2 options)
- 'binary_choice': two giant side-by-side cards
- 'likert': horizontal slider with 5 labeled points
- 'text': full-width textarea with word count and "10+ words" guidance
All options visually indicate selected state. No auto-advance.
```

---

## PHASE 9 — Frontend: Results & Dashboard (Day 5)

### Step 9.1 — Score gauge and factor bars

**Codex Prompt:**
```
Write src/components/ScoreGauge.jsx:
Pure SVG semicircular arc gauge (no chart library).
- Outer arc: color-coded zones (red 300-549, orange 550-649, green-yellow 650-749, green 750-850)
- Animated needle sweeps from 300 to score over 1.5s using requestAnimationFrame
- Center number counts up from 300 to score during animation
- Band label below number
- Props: {score, band}

Write src/components/FactorBars.jsx:
Horizontal SHAP waterfall bars (no chart library, pure Tailwind).
- Positive SHAP → bar extends right, green
- Negative SHAP → bar extends left, red
- Width proportional to abs(shap_value), max 180px
- Feature name formatted (feature_name → "Feature Name")
- Direction label: "▲ Boosted score" or "▼ Reduced score"
- Bars animate in sequentially, 150ms apart, on mount
- Props: {factors: [{feature, shap_value, direction, display_name}]}
```

### Step 9.2 — Full results page

**Codex Prompt:**
```
Write src/pages/Results.jsx.

Read API response from react-router location.state. Redirect to / if state missing.

Layout: dark navy bg, max-w-2xl centered, vertical scroll.

1. Header section with score + ScoreGauge
2. Percentile callout: "Higher than X% of applicants"
3. Band explanation card (Excellent/Good/Fair/Poor text from PRD)
4. Loan eligibility card with amount and description
5. FactorBars with top 6 SHAP factors
6. CounterfactualActions: 2-3 DICE-ML actions from response.counterfactual_actions
7. Improvement tips: 2-3 cards, each with an icon, title, and 1-sentence tip
8. ShareCard: export the visible score summary to PNG with html2canvas and open WhatsApp share intent
9. Action buttons: Retake, View Dashboard

Improvement tip generation logic (client-side):
- Find the 2 negative-direction factors from explanation
- Map each feature to a pre-written tip from a TIPS_MAP constant
- Fall back to a generic tip if feature not in TIPS_MAP

TIPS_MAP should cover at least these features with specific advice:
future_orientation, numeracy_score, conscientiousness_score, 
social_capital_score, honesty_score, engagement_score, impulsivity_index

ShareCard requirements:
- Component accepts {score, band, percentile, topFactor, eligibility}
- Render a compact 1080×1080-friendly card DOM node with AlterScore branding
- Use html2canvas(ref.current, {backgroundColor: '#0B1220', scale: 2})
- If Web Share API supports files, share the generated PNG directly
- Else download the PNG and open https://wa.me/?text= with a short prefilled message
```

### Step 9.3 — Dashboard charts

**Codex Prompt (run separately for each component):**
```
Write these 8 dashboard components. All fetch their own data via useFetch.
All show skeleton loading states while fetching.

1. ModelComparisonTable.jsx
Fetch /api/model-stats. Production model rows × 10 metric columns table.
Highlight stacking ensemble row. Color-code AUC cells: >0.80 green, 0.70-0.80 yellow.
Show model type badge: Classical / Neural / Ensemble.

2. BaselineComparisonTable.jsx
Fetch /api/baseline-comparison. Show 4 rows:
Majority Class → Logistic Regression → Simulated Loan Officer → Stacking Ensemble.
Columns: Model, type, AUC, KS, Brier score, ECE, lift vs loan officer.
Highlight lift over loan officer in AUC, KS, Brier score, and ECE. Lower Brier/ECE is better.

3. FeatureImportanceChart.jsx
Fetch /api/global-importance. recharts HorizontalBarChart, top 12 features.
Color by category using FEATURE_CATEGORIES constant.
Legend shows 4 category types.

4. ROCCurveChart.jsx
Fetch /api/roc-data. recharts LineChart with 7 model lines + dashed diagonal.
Each model gets a distinct color. AUC shown in legend label.

5. ScoreDistributionHistogram.jsx
Fetch /api/score-distribution. recharts BarChart.
Color bars by band. Reference lines at 550, 650, 750 with labels.
Show mean and median as annotations.

6. CalibrationCurve.jsx
Fetch /api/calibration-curve. recharts LineChart.
Plot model calibration vs perfect-calibration diagonal.
X-axis: Mean Predicted Probability. Y-axis: Fraction Positive.

7. DriftMonitorPanel.jsx
Fetch /api/drift-report. Show max PSI verdict, top 10 drifted features, and color-coded statuses:
stable <0.20, watch 0.20-0.30, alert >0.30.

8. FairnessAuditTable.jsx
Fetch /api/fairness-report.
4 sub-sections (one per protected attribute).
Status column: green ✓/yellow ⚠/red ✗ based on flag.
Overall verdict shown at top with color border.
```

### Step 9.4 — Full dashboard assembly

**Codex Prompt:**
```
Write src/pages/Dashboard.jsx.

Full analytics dashboard layout (max-w-7xl, dark navy bg).

Hero row: Title + subtitle + 4 KPI stat cards (AUC, best model, records, features).
Values for KPI cards should be fetched from /api/model-stats.

Grid layout (use Tailwind grid):
Row 1 full-width: <ModelComparisonTable />
Row 2 full-width: <BaselineComparisonTable />
Row 3 two-cols (6/6): <FeatureImportanceChart /> | <ROCCurveChart />
Row 4 full-width: <ScoreDistributionHistogram />
Row 5 two-cols (7/5): <PRCurveChart /> | <CalibrationCurve />
Row 6 full-width: <DriftMonitorPanel />
Row 7 full-width: <FairnessAuditTable />

Each section: white-border card on dark bg, section title with colored left accent bar.
Cards have consistent padding and gap.
Fully responsive: all multi-col rows collapse to single col on mobile.
```

---

## PHASE 10 — Polish and Final Prep (Day 6)

### Step 10.1 — Error handling and loading states

**Codex Prompt:**
```
Write src/components/ErrorBoundary.jsx:
Class component. Catches render errors. Shows: error icon, "Something went wrong",
error.message, and Retry button that resets state.

Write src/components/LoadingSpinner.jsx:
Full-page or inline spinner (prop: fullPage bool).
Dark overlay with spinning SVG ring and prop message.

Add error handling to Assessment.jsx:
- If POST fails: show error toast with "Retry" and "Start over" options
- Do NOT lose the user's answers on network failure
- Retry the POST with the same data

Add error handling to all Dashboard charts:
- If fetch fails: show error card with retry button
- Charts should retry independently (one chart failing doesn't affect others)
```

### Step 10.2 — Mobile responsiveness

**Codex Prompt:**
```
Audit and fix mobile responsiveness (target: works at 375px width):

Assessment.jsx:
- MCQ buttons: full width on mobile, no side-by-side
- Likert slider: ensure labels are visible and tap targets ≥44px
- Number input: large font, no zoom trigger (font-size ≥16px)
- Navigation buttons: sticky bottom bar on mobile

Results.jsx:
- ScoreGauge: use viewport width calc to scale SVG correctly on small screens
- FactorBars: truncate long feature names with ellipsis on mobile
- CounterfactualActions: cards wrap cleanly; current → suggested values never overflow
- ShareCard: exported PNG text remains readable at 1080×1080 and 375px viewport

Dashboard.jsx:
- All recharts charts: responsive container already handles this, but verify margins
- Tables: horizontal scroll on mobile (overflow-x-auto)
- KPI cards: 2-col grid on mobile, 4-col on desktop
```

### Step 10.3 — README and docs

**Codex Prompt:**
```
Write README.md for the project root. Sections:

1. Project Overview (3 paragraphs: problem, approach, what it builds)
2. Architecture Diagram (ASCII, see PRD section 3)
3. Tech Stack table
4. Feature Categories table (4 layers, example features per layer)
5. Quick Start (step by step commands: clone, venv, pip install, generate data, 
   train all models, start backend, start frontend)
6. Training Guide (how to run each training script, expected time per script on GPU,
   what artifacts each script produces)
7. Model Performance (paste your actual metrics.json results here after training)
8. Fairness Audit Summary (paste actual fairness_report.json verdict)
9. API Documentation (table of all 12 endpoints with method, path, description)
10. Research References (5 academic citations in APA format)
11. File Structure (tree from PRD section 11)

Keep it clean. Add badges at top: Python 3.10+, PyTorch, FastAPI, React.
```

---

# 13. Testing & Validation Strategy

## 13.1 Backend Tests

```python
# Run these manually before final submission

# 1. Model sanity checks
assert calibrated_model.predict_proba(X_test).shape == (len(X_test), 2)
assert all(0 <= p <= 1 for p in calibrated_model.predict_proba(X_test)[:, 1])

# 2. Score range check
scores = [probability_to_score(p) for p in test_probs]
assert all(300 <= s <= 850 for s in scores)

# 3. Monotonicity check (higher prob → higher score, always)
probs = sorted([0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9])
scores = [probability_to_score(p) for p in probs]
assert scores == sorted(scores), "Score mapping is not monotonic!"

# 4. SHAP sanity check
shap_values = explainer.shap_values(X_test_preprocessed[:10])
assert shap_values[1].shape == (10, len(NUMERIC_FEATURES) + len(CATEGORICAL_FEATURES))

# 5. Temporal split integrity
assert df.loc[train_idx, 'cohort_month'].max() <= 8
assert df.loc[val_idx, 'cohort_month'].between(9, 10).all()
assert df.loc[test_idx, 'cohort_month'].min() >= 11
assert 'cohort_month' not in X_train.columns

# 6. Baseline comparison sanity
assert metrics['ensemble']['auc_roc'] > metrics['baselines']['simulated_loan_officer']['auc_roc']

# 7. DICE counterfactual sanity
actions = generate_counterfactual_actions(X_test.iloc[[0]], dice_explainer)
assert 1 <= len(actions) <= 3
assert all(a['feature'] not in PROTECTED_FEATURES for a in actions)

# 8. PSI sanity
psi_report = build_psi_report(train_df, test_df, NUMERIC_FEATURES + CATEGORICAL_FEATURES)
assert all(row['psi'] >= 0 for row in psi_report)

# 9. API endpoint test (with test client)
from fastapi.testclient import TestClient
client = TestClient(app)
response = client.get("/api/health")
assert response.status_code == 200
assert response.json()['model_loaded'] == True

# 10. Full pipeline test with dummy payload
dummy_payload = build_dummy_score_request()  
response = client.post("/api/score", json=dummy_payload)
assert response.status_code == 200
assert 300 <= response.json()['credit_score'] <= 850
assert 'counterfactual_actions' in response.json()
```

## 13.2 Model Performance Targets

Before submission, confirm these minimum bars are met:

| Model | AUC Target | Notes |
|---|---|---|
| Dummy Baseline | ~0.50 | Control |
| Logistic Regression | > 0.68 | Interpretable baseline |
| Simulated Loan Officer | > 0.65 | Human-style heuristic comparator |
| Random Forest | > 0.73 | Primary tree model |
| XGBoost | > 0.75 | Should beat RF |
| LightGBM | > 0.74 | Comparable to XGB |
| TabNet | > 0.72 | Attention model |
| MLP | > 0.71 | Neural baseline |
| **Stacking Ensemble** | **> 0.78** | **Production model on months 11-12 temporal test** |

If stacking AUC is < 0.75, check:
1. Did SMOTE run only on training data?
2. Did the temporal split use months 1-8 train, 9-10 validation, 11-12 test?
3. Is the label generation formula correctly correlated with features?
4. Are derived features computed before preprocessing?
5. Does the ensemble beat the simulated loan officer baseline?

## 13.3 NLP Pipeline Test

```python
# Test the local NLP pipeline
from backend.model.nlp_features import extract_nlp_features

# High agency text
result1 = extract_nlp_features(
    "When I lost my job in 2021, I immediately started budgeting strictly and found freelance work within 2 weeks. I learned that I can handle crisis if I act fast."
)
assert result1['text_agency_score'] > 0.3
assert result1['text_problem_solving_flag'] == 1.0
assert result1['text_sentiment_compound'] > 0

# Low agency text  
result2 = extract_nlp_features(
    "Bad things kept happening and I was unable to do anything. Everything just fell apart and I had no choice but to give up."
)
assert result2['text_agency_score'] < 0.2
assert result2['text_sentiment_compound'] < 0
```

---

# 14. Submission Checklist

## Code Quality
- [ ] All Python files have docstrings on functions and classes
- [ ] No hardcoded file paths — use os.path or pathlib
- [ ] All model artifacts loadable without retraining
- [ ] Requirements.txt pinned versions
- [ ] .env file exists, .gitignore excludes .env + models/ + data/

## ML Quality
- [ ] AUC of stacking ensemble > 0.75 on months 11-12 temporal test set
- [ ] Stacking beats all individual models
- [ ] Stacking beats simulated loan officer baseline by ≥0.05 AUC
- [ ] Calibration applied and tested
- [ ] SHAP produces non-trivial explanations (not all zeroes)
- [ ] DICE-ML counterfactual actions are generated for low and mid-tier applicants
- [ ] PSI report generated; no core feature has PSI >0.30 without explanation
- [ ] Fairness report has at least 30+ samples per subgroup
- [ ] Training scripts can be re-run from scratch reproducibly (seeds set everywhere)

## Feature Engineering
- [ ] All 39 features are present in the dataset
- [ ] cohort_month and application_date exist for validation but are excluded from model inputs
- [ ] Protected attributes never appear in NUMERIC_FEATURES or CATEGORICAL_FEATURES
- [ ] NLP features computed from Q27 text (including PCA dims)
- [ ] Derived features computed correctly (verify formulas match PRD)

## API Quality
- [ ] /api/health returns model_loaded: true
- [ ] /api/score returns valid JSON for both edge-case inputs (all low, all high)
- [ ] All 12 endpoints return 200 with correct schema
- [ ] CORS configured correctly for frontend

## Frontend Quality
- [ ] All 4 pages render without console errors
- [ ] Assessment completes from start to submit in < 8 minutes normally
- [ ] Results page shows score + SHAP explanation + counterfactual actions correctly
- [ ] ShareCard exports a readable PNG and opens WhatsApp share fallback
- [ ] Dashboard loads all 6+ charts
- [ ] Dashboard includes baseline comparison and PSI drift sections
- [ ] Mobile (375px): all pages are usable
- [ ] Network error handling: assessment doesn't lose data on API failure

## Demo Readiness
- [ ] Can do full end-to-end in ≤ 6 minutes for video
- [ ] Dashboard charts are populated with real trained data (not hardcoded)
- [ ] Score gauge animation is smooth
- [ ] Fairness table shows real results

---

# 15. Interview Preparation

## Expected Technical Questions

**"Why a stacking ensemble over a single best model?"**  
Each base model has different inductive biases — RF uses bagging and feature subsampling, XGBoost uses sequential residual correction, TabNet uses attention to select features per instance, MLP learns non-linear interactions in continuous space. Their errors are partially uncorrelated. Stacking learns from the disagreements between them, producing predictions that no single model achieves alone. The meta-learner (logistic regression) learns to weight each model's opinion based on the validation error patterns.

**"How does TabNet work and why is it better than plain XGBoost for this task?"**  
TabNet uses sequential attention — at each step, it learns a sparse mask over features, effectively selecting which features to look at before making that step's decision. This is advantageous for our dataset because different subsets of psychometric features matter for different applicant profiles (e.g., social capital matters more for rural applicants, numeracy matters more for semi-urban ones). TabNet discovers these subgroup-specific feature importances automatically.

**"Your NLP features — why not just use an LLM to evaluate the text answer?"**  
Two reasons: first, we have no API budget, and self-hosting an LLM requires significant compute for a single text feature. Second, interpretability — a recruiter or regulator can understand what "high agency verb ratio" means, but cannot interrogate a dense LLM embedding. VADER + spaCy gives us three interpretable, auditable NLP features that a domain expert can validate. The sentence-transformer PCA dims add semantic richness where interpretability is less critical.

**"What does a calibrated probability actually mean?"**  
It means: if the model assigns a repayment probability of 0.70 to 100 applicants, approximately 70 of them should actually repay. Without calibration, a model that outputs 0.70 might be systematically under- or over-estimating. We use isotonic regression calibration (fit on the validation set) to enforce this reliability property. The calibration curve — fraction_positive vs mean_predicted_probability — should lie along the diagonal.

**"You found a subgroup with lower AUC in your fairness audit. What do you do?"**  
First, understand why — is the lower AUC driven by smaller sample size (statistical artifact), feature distribution shift for that group, or systematic bias in the label generation? For real deployment: (1) collect more data from the underperforming group, (2) consider separate calibration for that group, (3) introduce group-specific features that are predictive but were missing, (4) consider a fairness-aware training objective (e.g., adversarial debiasing). We do NOT simply exclude the group.

**"What's the KS statistic and why do you report it?"**  
The Kolmogorov-Smirnov statistic measures the maximum vertical distance between the cumulative distribution functions of defaulters' scores and repayers' scores. It's the standard model evaluation metric in the credit industry (used by all credit bureaus globally). A KS of 0.40 means: there is a threshold where, if we draw a vertical line, we separate 40% more true repayers than true defaulters compared to random. Industry thumb rule: KS > 0.20 = acceptable, > 0.40 = good, > 0.60 = excellent.

**"How would you deploy this in production at an actual MFI?"**  
Phase 1: Shadow mode — run the model alongside the loan officer's manual decision. Collect actual repayment outcomes. Phase 2: After 6–12 months of actuals, retrain on real labels (psychometric features as inputs, real repayment as target). Phase 3: Gradual authority transfer — model becomes a recommender, loan officer has final say. Phase 4: For loans under a threshold (e.g., ₹10,000), model makes autonomous decisions. Phase 5: Continuous monitoring — monthly AUC on new cohorts, monthly fairness audit, automated drift detection.

**"What happens when someone lies on the psychometric questionnaire?"**  
This is the key limitation of self-reported assessments. Our mitigations: (1) Ipsative honesty scoring — repeat questions detect inconsistency; (2) Social desirability traps — implausible virtue claims are flagged; (3) Behavioral telemetry — actual response patterns (timing, hesitation) are harder to fake than stated preferences; (4) The open-text Q27 gives NLP signals that are hard to fabricate consistently; (5) In production, we would triangulate against other data sources where available. Perfect honesty is not required — the model needs only slight signal over noise to be useful.
