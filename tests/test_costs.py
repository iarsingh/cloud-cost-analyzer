from fastapi.testclient import TestClient

from costs.main import app

client = TestClient(app)


def test_sample_gcp_names_bigquery():
    body = client.post("/costs/summary", json={"provider": "gcp"}).json()
    assert body["top_service"]["service"] == "BigQuery"
    assert body["total"] == 138.5


def test_unknown_provider_is_refused():
    response = client.post("/costs/summary", json={"provider": "azure"})
    assert response.status_code == 422
