# Cloud cost analyzer

<!-- project-guide:start -->
## Project guide

[Project architecture](PROJECT_ARCHITECTURE.md) · [Interview questions and answers](INTERVIEW_QA.md)

Use the architecture document for the component diagram, implementation boundaries, and verification entry points. The interview guide includes source-backed answers and project walkthroughs.

### Implementation map

| Component | Responsibility |
| --- | --- |
| [`src/costs/main.py`](src/costs/main.py) | HTTP handlers: `GET /healthz`, `POST /costs/summary`, `POST /costs/csv` |
| [`src/costs/ops.py`](src/costs/ops.py) | HTTP handlers: `GET /readyz`, `POST /workspaces`, `GET /workspaces`, `POST /workspaces/{workspace_id}/jobs`, `GET /jobs/{job_id}` |
| [`src/costs/analyze.py`](src/costs/analyze.py) | Functions: `normalize`, `parse_csv`, `summarize`, `spikes` |
| [`requirements.txt`](requirements.txt) | Implementation or supporting configuration |
| [`Dockerfile`](Dockerfile) | Container build/service configuration |
| [`Makefile`](Makefile) | Implementation or supporting configuration |
| [`docker-compose.yml`](docker-compose.yml) | Container build/service configuration |
| [`tests/test_costs.py`](tests/test_costs.py) | Executable checks and regression examples |
| [`tests/test_ops.py`](tests/test_ops.py) | Executable checks and regression examples |
| [`.github/workflows/ci.yml`](.github/workflows/ci.yml) | GitHub Actions job definitions |
| [`README.md`](README.md) | Project explanations or operating notes |
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | Project explanations or operating notes |

### Local setup and verification

From the repository root (the commands follow the checked-in manifests):

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pytest -q
```

To serve the FastAPI application locally, install the server separately if it is not already available:

```bash
python -m pip install uvicorn
PYTHONPATH=src python -m uvicorn costs.main:app --reload
```

<!-- project-guide:end -->

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

## Ops plane

Workspaces, tenant isolation, job approval, and audit live under `/v1`. Production apply is refused. See `docs/ARCHITECTURE.md`.

## Documentation checks

Project architecture, interview guides, and local source links are checked automatically on pushes and pull requests. Run the same check locally:

```bash
python3 .github/scripts/validate_project_docs.py
```

See [service improvements and local run instructions](docs/UPGRADES.md).
