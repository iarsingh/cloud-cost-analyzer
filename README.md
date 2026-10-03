# Cloud cost analyzer

Level: Beginner

Skills: Python, APIs, JSON, GCP/AWS

Paste a cost export. The API groups it by service and names the largest line.

No cloud login is required. `data/sample-costs.json` is the local export. A row needs `provider`, `service`, and `cost`. Providers in this version are `gcp` and `aws`. Anything else is refused rather than guessed.

```bash
pip install -r requirements.txt
pytest -q
PYTHONPATH=src uvicorn costs.main:app --reload
```

```bash
curl -s -X POST localhost:8000/costs/summary -H 'content-type: application/json' -d '{"provider":"gcp"}'
```

