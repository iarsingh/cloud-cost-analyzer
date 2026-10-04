import pytest
from fastapi.testclient import TestClient

from costs.analyze import CostError, parse_csv, spikes, summarize
from costs.main import app

client = TestClient(app)

GCP_CSV = """service.description,cost,currency,usage_start_time
BigQuery,10.00,USD,2026-10-01T00:00:00Z
BigQuery,30.00,USD,2026-10-02T00:00:00Z
Compute Engine,5.00,USD,2026-10-02T00:00:00Z
"""

AWS_CSV = """lineItem/ProductCode,lineItem/UnblendedCost,lineItem/CurrencyCode,lineItem/UsageStartDate
AmazonEC2,20.0,USD,2026-10-01T00:00:00Z
AmazonS3,-2.5,USD,2026-10-01T00:00:00Z
"""


def test_sample_gcp_names_bigquery():
    body = client.post("/costs/summary", json={"provider": "gcp"}).json()
    assert body["top_service"]["service"] == "BigQuery"
    assert body["total"] == 138.5


def test_unknown_provider_is_refused():
    assert client.post("/costs/summary", json={"provider": "azure"}).status_code == 422


def test_share_adds_up_to_the_whole():
    body = client.post("/costs/summary", json={"provider": "all"}).json()
    assert round(sum(row["share"] for row in body["by_service"])) == 100


def test_budget_reports_overspend():
    body = client.post("/costs/summary", json={"provider": "gcp", "budget": 100}).json()
    assert body["budget"]["over"] is True
    assert body["budget"]["remaining"] == -38.5
    assert body["budget"]["used_percent"] == 138.5


def test_growth_under_one_and_a_half_times_is_not_a_spike():
    body = client.post("/costs/summary", json={"provider": "gcp"}).json()
    assert body["spikes"] == []


def test_tripled_day_is_a_spike():
    found = spikes([{"day": "2026-10-01", "cost": 10.0}, {"day": "2026-10-02", "cost": 30.0}])
    assert found == [{"day": "2026-10-02", "previous": 10.0, "cost": 30.0, "ratio": 3.0}]


def test_gcp_billing_csv_is_mapped():
    rows = parse_csv(GCP_CSV, "gcp")
    body = summarize(rows, "gcp")
    assert body["total"] == 45.0
    assert body["top_service"] == {"service": "BigQuery", "cost": 40.0}
    assert body["spikes"][0]["day"] == "2026-10-02"


def test_aws_cur_csv_counts_a_credit():
    response = client.post("/costs/csv", json={"provider": "aws", "csv": AWS_CSV})
    body = response.json()
    assert body["total"] == 17.5
    assert body["credits"] == -2.5


def test_csv_missing_a_column_is_refused():
    response = client.post("/costs/csv", json={"provider": "gcp", "csv": "name,amount\nx,1\n"})
    assert response.status_code == 422
    assert "missing column" in response.json()["detail"]


def test_mixed_currencies_are_not_summed():
    rows = [
        {"provider": "gcp", "service": "BigQuery", "cost": 1, "currency": "USD"},
        {"provider": "gcp", "service": "GCS", "cost": 1, "currency": "EUR"},
    ]
    with pytest.raises(CostError, match="mixed currencies"):
        summarize(rows)


def test_non_numeric_cost_is_refused_by_the_api():
    rows = [{"provider": "gcp", "service": "BigQuery", "cost": "lots"}]
    assert client.post("/costs/summary", json={"rows": rows}).status_code == 422
