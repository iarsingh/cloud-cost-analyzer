from costs.ops import router as ops_router
import json
from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from costs.analyze import CostError, parse_csv, summarize

app = FastAPI(title="Cloud cost analyzer")
app.include_router(ops_router, prefix="/v1")
SAMPLE = Path(__file__).resolve().parents[2] / "data" / "sample-costs.json"


class SummaryRequest(BaseModel):
    provider: str | None = None
    rows: list[dict] | None = None
    budget: float | None = Field(default=None, ge=0)


class CsvRequest(BaseModel):
    provider: str
    csv: str
    budget: float | None = Field(default=None, ge=0)


def sample_rows():
    return json.loads(SAMPLE.read_text(encoding="utf-8"))


def checked_provider(provider):
    if provider is not None and provider not in {"gcp", "aws", "all"}:
        raise HTTPException(status_code=422, detail="provider must be gcp, aws, or all")
    return None if provider in {None, "all"} else provider


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


@app.post("/costs/summary")
def summary(body: SummaryRequest | None = None):
    body = body or SummaryRequest()
    provider = checked_provider(body.provider)
    rows = sample_rows() if body.rows is None else body.rows
    try:
        return summarize(rows, provider, body.budget)
    except CostError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.post("/costs/csv")
def summary_from_csv(body: CsvRequest):
    provider = checked_provider(body.provider)
    if provider is None:
        raise HTTPException(status_code=422, detail="a CSV export belongs to one provider")
    try:
        return summarize(parse_csv(body.csv, provider), provider, body.budget)
    except CostError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
