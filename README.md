# Cloud cost analyzer

Level: Beginner

Skills: Python, APIs, JSON, CSV, GCP billing export, AWS Cost and Usage Report

Send cost rows or a billing CSV. The API groups spend by service, gives each service its share, checks a budget, and names any day that jumped by 1.5 times or more over the day before.

No cloud login is required. `data/sample-costs.json` is the local export. Providers in this version are `gcp` and `aws`. Anything else is refused rather than guessed.

```bash
pip install -r requirements.txt
pytest -q
PYTHONPATH=src uvicorn costs.main:app --reload
```

## JSON rows

```bash
curl -s -X POST localhost:8000/costs/summary \
  -H 'content-type: application/json' \
  -d '{"provider":"gcp","budget":100}'
```

On the sample, GCP totals 138.5 and BigQuery is the top service. A budget of 100 comes back `over: true` with 38.5 overspent.

## CSV exports

`POST /costs/csv` with `{"provider": "gcp" | "aws", "csv": "..."}`.

| Provider | Service column | Cost column | Day column |
| --- | --- | --- | --- |
| gcp | `service.description` | `cost` | `usage_start_time` |
| aws | `lineItem/ProductCode` | `lineItem/UnblendedCost` | `lineItem/UsageStartDate` |

## What it refuses

- A row without provider, service, or cost.
- A cost that is not a number.
- Rows in more than one currency. Convert first; this tool does not pick an exchange rate.
- A CSV that does not have the service and cost columns for its provider.

Negative rows are credits. They lower the total and are reported separately under `credits`.
