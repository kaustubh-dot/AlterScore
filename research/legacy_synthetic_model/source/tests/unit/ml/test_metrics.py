from backend.app.core.constants import SCORE_BASE, SCORE_LOG_ODDS_FACTOR
from backend.ml.evaluation.metrics import build_population_percentiles_payload


def test_population_percentiles_payload_uses_supplied_score_mapping_config() -> None:
    probabilities = [0.2, 0.5, 0.8]

    default_payload = build_population_percentiles_payload(
        probabilities,
        model_name="candidate",
    )
    # Use explicitly narrower scale (same base, half the factor) — min/max must compress
    compressed_payload = build_population_percentiles_payload(
        probabilities,
        model_name="candidate",
        score_mapping_config={
            "method": "log_odds",
            "score_base": SCORE_BASE,
            "log_odds_factor": SCORE_LOG_ODDS_FACTOR / 2,
            "probability_clip_min": 0.01,
            "probability_clip_max": 0.99,
            "score_min": 300,
            "score_max": 850,
            "calibration": "isotonic",
        },
    )

    assert compressed_payload["summary"]["min_score"] > (
        default_payload["summary"]["min_score"]
    )
    assert compressed_payload["summary"]["max_score"] < (
        default_payload["summary"]["max_score"]
    )
