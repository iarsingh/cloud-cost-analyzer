import json
from pathlib import Path

from fastapi import FastAPI, HTTPException

from costs.analyze import summarize

app = FastAPI(title="Cloud cost analyzer")
SAMPLE = Path(__file__).resolve().parents[2] / "data" / "sample-costs.json"


def load_rows(payload):
    if payload is None:
        return json.loads(SAMPLE.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise HTTPException(status_code=422, detail="body must be a list of cost rows")
    return payload


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


@app.post("/costs/summary")
def summary(body: dict | None = None):
    provider = None if body is None else body.get("provider")
    rows = None if body is None or "rows" not in body else body["rows"]
    if provider is not None and provider not in {"gcp", "aws", "all"}:
        raise HTTPException(status_code=422, detail="provider must be gcp, aws, or all")
    return summarize(load_rows(rows), None if provider in {None, "all"} else provider)
