import re
from pathlib import Path

file_path = Path(r'C:\Kaustubh\Projects\AlterScore\backend\ml\data_generation\generator.py')
text = file_path.read_text(encoding='utf-8')

text = text.replace('from backend.ml.preprocessing.feature_registry import (', 'from backend.ml.features.scenario_analyzer import _OPTION_CODEBOOK, _SCENARIO_IDS, _PRIMARY_WEIGHT, _SECONDARY_WEIGHT\nfrom backend.ml.preprocessing.feature_registry import (')

new_block = """
    # --- Scenario-driven features (Discrete sampling via Codebook) ---
    # We simulate users picking options from the scenario codebook based on their latent traits.
    
    # Initialize zero arrays
    feature_accumulators = {
        "future_orientation": np.zeros(row_count),
        "conscientiousness_score": np.zeros(row_count),
        "social_capital_score": np.zeros(row_count),
        "locus_of_control": np.zeros(row_count),
        "resilience_score": np.zeros(row_count),
        "loss_aversion_score": np.zeros(row_count),
        "reciprocity_norm": np.zeros(row_count),
        "honesty_score": np.zeros(row_count)
    }
    feature_counts = {k: np.zeros(row_count) for k in feature_accumulators}
    
    latent_prefs = {
        "future_orientation": _sigmoid(0.62 * discipline + 0.24 * stability),
        "conscientiousness_score": _sigmoid(0.58 * discipline + 0.16 * stability),
        "social_capital_score": _sigmoid(0.64 * social + 0.18 * integrity),
        "locus_of_control": _sigmoid(0.56 * stability + 0.18 * discipline),
        "resilience_score": _sigmoid(0.54 * stability + 0.22 * social),
        "loss_aversion_score": _sigmoid(0.22 * stability - 0.12 * capacity),
        "reciprocity_norm": _sigmoid(0.56 * social + 0.20 * integrity),
        "honesty_score": _sigmoid(0.72 * integrity + 0.18 * discipline)
    }
    
    for s_id in _SCENARIO_IDS:
        prefix = s_id.split('_')[1]
        options = [k for k in _OPTION_CODEBOOK.keys() if k.startswith(prefix)]
        
        affinities = []
        for opt in options:
            p_feat, p_val, s_feat, s_val = _OPTION_CODEBOOK[opt]
            aff = p_val * latent_prefs[p_feat] + s_val * latent_prefs[s_feat] + rng.normal(0, 0.2, row_count)
            affinities.append(aff)
            
        affinities = np.array(affinities)
        best_opt_indices = np.argmax(affinities, axis=0)
        
        for i in range(row_count):
            chosen_opt = options[best_opt_indices[i]]
            p_feat, p_val, s_feat, s_val = _OPTION_CODEBOOK[chosen_opt]
            feature_accumulators[p_feat][i] += p_val * _PRIMARY_WEIGHT
            feature_counts[p_feat][i] += _PRIMARY_WEIGHT
            feature_accumulators[s_feat][i] += s_val * _SECONDARY_WEIGHT
            feature_counts[s_feat][i] += _SECONDARY_WEIGHT

    for f in feature_accumulators:
        avg_contributions = np.where(feature_counts[f] > 0, feature_accumulators[f] / feature_counts[f], 0.5)
        feature_accumulators[f] = 0.5 * 0.40 + avg_contributions * 0.60
        feature_accumulators[f] = np.clip(feature_accumulators[f], 0.0, 1.0)
        
    future_orientation = feature_accumulators["future_orientation"]
    conscientiousness_score = feature_accumulators["conscientiousness_score"]
    social_capital_score = feature_accumulators["social_capital_score"]
    locus_of_control = feature_accumulators["locus_of_control"]
    resilience_score = feature_accumulators["resilience_score"]
    loss_aversion_score = feature_accumulators["loss_aversion_score"]
    reciprocity_norm = feature_accumulators["reciprocity_norm"]
    honesty_score = feature_accumulators["honesty_score"]

    delay_discounting_rate = np.clip(
        0.68 * future_orientation + 0.12 * _sigmoid(0.35 * discipline) + rng.normal(0.0, 0.08, row_count),
        0.20, 1.0,
    )
    risk_attitude = np.clip(
        0.52 + 0.10 * capacity - 0.06 * discipline + rng.normal(0.0, 0.16, row_count),
        0.02,
        0.98,
    )
    risk_consistency_probability = np.clip(
        0.08 - 0.04 * discipline - 0.03 * capacity + rng.normal(0.0, 0.03, row_count),
        0.02,
        0.18,
    )
    risk_consistency_flag = (rng.random(row_count) < risk_consistency_probability).astype(int)
"""

pattern = r'# --- Scenario-driven features: floor at 0.25 to match v2 codebook minimum ---.*?reciprocity_norm.*?, row_count\)\),\n        0\.25, 1\.0,\n    \)'
text = re.sub(pattern, new_block, text, flags=re.DOTALL)

file_path.write_text(text, encoding='utf-8')
print("Successfully rewrote generator.py")
