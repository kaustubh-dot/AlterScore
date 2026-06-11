from backend.ml.evaluation.metrics import build_population_percentiles_payload


def test_population_percentiles_payload_uses_supplied_score_mapping_config() -> None:
    probabilities = [0.2, 0.5, 0.8]

    default_payload = build_population_percentiles_payload(
        probabilities,
        model_name="candidate",
    )
    compressed_payload = build_population_percentiles_payload(
        probabilities,
        model_name="candidate",
        score_mapping_config={
            "method": "log_odds",
            "score_base": 500,
            "log_odds_factor": 20,
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
