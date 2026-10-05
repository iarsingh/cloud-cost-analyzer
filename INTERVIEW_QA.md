# cloud-cost-analyzer — interview questions and answers

[README](README.md) · [Project architecture](PROJECT_ARCHITECTURE.md)

Answers below use this repository’s files and implementation. They distinguish existing behavior from suggested extensions; source links let you verify each walkthrough.

## 1. What problem does cloud-cost-analyzer address, and what can you demonstrate?

Send cost rows or a billing CSV. The API groups spend by service, gives each service its share, checks a budget, and names any day that jumped by 1.5 times or more over the day before.

I would demonstrate the linked implementation or examples and distinguish that evidence from any planned production features. Start with [`README.md`](README.md).

## 2. How is this repository organized?

- [`src/costs/main.py`](src/costs/main.py): Implementation or supporting configuration.
- [`src/costs/ops.py`](src/costs/ops.py): Implementation or supporting configuration.
- [`src/costs/analyze.py`](src/costs/analyze.py): Implementation or supporting configuration.
- [`requirements.txt`](requirements.txt): Implementation or supporting configuration.
- [`Dockerfile`](Dockerfile): Container build/service configuration.
- [`Makefile`](Makefile): Implementation or supporting configuration.
- [`docker-compose.yml`](docker-compose.yml): Container build/service configuration.
- [`tests/test_costs.py`](tests/test_costs.py): Executable checks and regression examples.

[PROJECT_ARCHITECTURE.md](PROJECT_ARCHITECTURE.md) contains the component diagram and the implementation walkthrough.

## 3. Can you walk through `summarize` and explain the decision it makes?

The main walkthrough here is `summarize(rows, provider=None, budget=None)` in [`src/costs/analyze.py`](src/costs/analyze.py#L57).

```python
def summarize(rows, provider=None, budget=None):
    clean = [normalize(row) for row in rows]
    chosen = [row for row in clean if provider is None or row["provider"] == provider]
    currencies = {row["currency"] for row in chosen}
    if len(currencies) > 1:
        raise CostError(f"mixed currencies {sorted(currencies)}; convert before summing")
    totals = {}
    credits = 0.0
    for row in chosen:
        totals[row["service"]] = round(totals.get(row["service"], 0) + row["cost"], 2)
        if row["cost"] < 0:
            credits = round(credits + row["cost"], 2)
    ranked = sorted(totals.items(), key=lambda item: item[1], reverse=True)
    top = {"service": ranked[0][0], "cost": ranked[0][1]} if ranked else None
    total = round(sum(totals.values()), 2)
    result = {
        "provider": provider or "all",
        "currency": currencies.pop() if currencies else "USD",
        "total": total,
        "credits": credits,
```

This is an excerpt; follow the source link for the rest of the branches.

The implementation calls `CostError`, `currencies.pop`, `len`, `normalize`, `round`, `sorted`, `spikes`, `sum`, `totals.get`. In an interview, trace those calls in execution order using a fixture input.

## 4. What responsibility does `parse_csv` have?

`parse_csv(text, provider)` is defined in [`src/costs/analyze.py`](src/costs/analyze.py#L35).

Its return expressions include:

- `rows`

It uses `', '.join`, `CostError`, `csv.DictReader`, `io.StringIO`, `raw.get`, `rows.append`, `text.strip`. This is the code path I would compare against the caller to explain responsibility boundaries.

## 5. What input validation and failure behavior are implemented?

Explicit failure paths include:

- `CostError(f"provider {row['provider']} is not supported")` in [`src/costs/analyze.py`](src/costs/analyze.py#L21).
- `CostError(f'no CSV mapping for provider {provider}')` in [`src/costs/analyze.py`](src/costs/analyze.py#L37).
- `CostError(f"CSV is missing column {', '.join(missing)}")` in [`src/costs/analyze.py`](src/costs/analyze.py#L42).
- `CostError(f'mixed currencies {sorted(currencies)}; convert before summing')` in [`src/costs/analyze.py`](src/costs/analyze.py#L62).
- `CostError(f'row is missing {key}')` in [`src/costs/analyze.py`](src/costs/analyze.py#L19).
- `CostError(f"cost is not a number: {row['cost']}")` in [`src/costs/analyze.py`](src/costs/analyze.py#L25).
- `HTTPException(status_code=422, detail='provider must be gcp, aws, or all')` in [`src/costs/main.py`](src/costs/main.py#L33).

I would test both the condition that reaches each exception and the caller that translates it. An explicit raise does not mean every malformed input or dependency failure is handled.

## 6. Which test would you use to demonstrate correctness?

[`tests/test_costs.py`](tests/test_costs.py#L21) contains `test_sample_gcp_names_bigquery`:

```python
def test_sample_gcp_names_bigquery():
    body = client.post("/costs/summary", json={"provider": "gcp"}).json()
    assert body["top_service"]["service"] == "BigQuery"
    assert body["total"] == 138.5
```

This is a concrete regression example from the repository. Its assertions establish that case; they do not establish behavior for every input or under production load.

## 7. What HTTP interface does the code expose?

- `GET /healthz` → `healthz` in [`src/costs/main.py`](src/costs/main.py#L38).
- `POST /costs/summary` → `summary` in [`src/costs/main.py`](src/costs/main.py#L43).
- `POST /costs/csv` → `summary_from_csv` in [`src/costs/main.py`](src/costs/main.py#L54).
- `GET /readyz` → `readyz` in [`src/costs/ops.py`](src/costs/ops.py#L44).
- `POST /workspaces` → `create_workspace` in [`src/costs/ops.py`](src/costs/ops.py#L49).
- `GET /workspaces` → `list_workspaces` in [`src/costs/ops.py`](src/costs/ops.py#L66).
- `POST /workspaces/{workspace_id}/jobs` → `create_job` in [`src/costs/ops.py`](src/costs/ops.py#L73).
- `GET /jobs/{job_id}` → `get_job` in [`src/costs/ops.py`](src/costs/ops.py#L96).

These are literal decorators. Application/router prefixes, authentication, and middleware must be checked in the corresponding setup code.

## 8. Where does state live, and what happens with multiple workers?

Module-level containers include `PROVIDERS`, `CSV_COLUMNS` in [`src/costs/analyze.py`](src/costs/analyze.py); `_WORKSPACES`, `_JOBS`, `_AUDIT`, `_METRICS` in [`src/costs/ops.py`](src/costs/ops.py).

These containers belong to a Python process. Inspect which are constant fixtures and which are mutated. Mutable process state needs an explicit shared-storage or synchronization strategy before multiple workers can provide consistent behavior.

## 9. How would another engineer reproduce your walkthrough?

Start from the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pytest -q
```

These commands follow repository manifests; environment setup and command results still need to be checked on the target machine.

## 10. What does automation verify, and what does it not prove?

Inspect [`.github/workflows/ci.yml`](.github/workflows/ci.yml) for triggers, permissions, and job commands. I would name the checks that those definitions run and show the latest run separately. A workflow definition alone does not establish a successful deployment, security review, or production SLO.

## 11. How would you present this project in a Forward Deployed Engineer interview?

Start with the user and operational problem described in [`README.md`](README.md). Explain one constraint that changes the implementation, show the linked code or example, and walk through a success case and a failure case. Agree on a measurable acceptance criterion before expanding the solution, and leave a handoff with data boundaries and rollback ownership. Any proposed production or business metric should be identified as a target until measured.

## 12. What is the input-to-output contract of `summarize`?

In [`src/costs/analyze.py`](src/costs/analyze.py#L57), `summarize(rows, provider=None, budget=None)` receives the inputs. The function computes these intermediate values:

- `clean = [normalize(row) for row in rows]`
- `chosen = [row for row in clean if provider is None or row['provider'] == provider]`
- `currencies = {row['currency'] for row in chosen}`
- `totals = {}`
- `credits = 0.0`
- `ranked = sorted(totals.items(), key=lambda item: item[1], reverse=True)`
- `top = {'service': ranked[0][0], 'cost': ranked[0][1]} if ranked else None`

Its result is defined by:

- `result`

## 13. Which decision rules or boundary conditions should an interviewer challenge?

The implementation in [`src/costs/analyze.py`](src/costs/analyze.py#L57) branches on:

- `len(currencies) > 1`
- `budget is not None`
- `row['cost'] < 0`

A useful extension is a table-driven test that covers each condition just below, at, and above its boundary where applicable. These expressions are the current rules; changing them changes behavior and should be justified by the project’s acceptance criteria.

## 14. What does the operations plane add, and where is its limit?

[`src/costs/ops.py`](src/costs/ops.py) declares `GET /readyz`, `POST /workspaces`, `GET /workspaces`, `POST /workspaces/{workspace_id}/jobs`, `GET /jobs/{job_id}`, `POST /jobs/{job_id}/approve`, `GET /audit`, `GET /metrics`. Inspect the application’s `include_router` call for its URL prefix.

Its state containers are `_WORKSPACES`, `_JOBS`, `_AUDIT`, `_METRICS`. The job-approval handler defines whether a target is accepted or refused; check that branch and the associated tests instead of treating a recorded job as a successful infrastructure apply.
