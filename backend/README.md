# AlterScore public backend

The serving backend exposes the anonymous, deterministic v2 assessment:

- `GET /api/v2/assessment/form`
- `POST /api/v2/assessment/score`
- `GET /api/v2/results/verify/{result_id}`
- `GET /api/live`
- `GET /api/ready`

The former model-backed `POST /api/score` and `/api/debug-score` routes return
`410 Gone`. Former analytics routes are not registered. The public runtime does
not import or load model artifacts, explainers, NLP packages, training scripts,
or the retired synthetic XGBoost source. Retired source and artifacts are not
part of the production repository.

Run locally with:

```bash
python -m pip install -r backend/requirements.txt
python -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

Set `ALTERSCORE_SIGNING_SECRET` to a generated base64url secret before using
the assessment or expecting `/api/ready` to report `ready`.
