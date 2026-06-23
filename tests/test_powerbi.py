import pytest

from app.services import powerbi
from tests.conftest import FakeClient, FakeResponse


@pytest.fixture(autouse=True)
def _stub_token(monkeypatch):
    monkeypatch.setattr(powerbi.token_provider, "powerbi_token", lambda: "fake-token")


def _patch_client(monkeypatch, response: FakeResponse):
    monkeypatch.setattr(powerbi.httpx, "Client", lambda *a, **k: FakeClient(response))


def test_start_export_builds_rls_body(monkeypatch):
    _patch_client(monkeypatch, FakeResponse(202, json_data={"id": "export-123"}))
    export_id = powerbi.powerbi_client.start_export(
        "ws1",
        "rep1",
        "ReportSectionA",
        rls_username="user@x.com",
        rls_roles=["Vendas"],
        dataset_id="ds1",
        report_level_filters="Tabela/Campo eq 'X'",
    )
    assert export_id == "export-123"
    body = FakeClient.last_request["json"]
    cfg = body["powerBIReportConfiguration"]
    assert body["format"] == "PDF"
    assert cfg["pages"] == [{"pageName": "ReportSectionA"}]
    assert cfg["identities"][0]["username"] == "user@x.com"
    assert cfg["identities"][0]["roles"] == ["Vendas"]
    assert cfg["identities"][0]["datasets"] == ["ds1"]
    assert cfg["reportLevelFilters"][0]["filter"] == "Tabela/Campo eq 'X'"


def test_export_status_parsing(monkeypatch):
    _patch_client(
        monkeypatch,
        FakeResponse(
            200,
            json_data={
                "status": "Running",
                "percentComplete": 70,
                "resourceLocation": None,
            },
        ),
    )
    st = powerbi.powerbi_client.get_export_status("ws", "rep", "exp")
    assert st.status == "Running"
    assert st.percent_complete == 70


def test_rate_limited_propagates(monkeypatch):
    _patch_client(monkeypatch, FakeResponse(429, headers={"Retry-After": "13"}))
    with pytest.raises(powerbi.RateLimited) as ei:
        powerbi.powerbi_client.refresh_dataset("ws", "ds")
    assert ei.value.retry_after == 13


def test_business_error_raises(monkeypatch):
    _patch_client(monkeypatch, FakeResponse(404, json_data={"error": "not found"}))
    with pytest.raises(powerbi.PowerBIError):
        powerbi.powerbi_client.get_dataset_refresh_status("ws", "ds")
