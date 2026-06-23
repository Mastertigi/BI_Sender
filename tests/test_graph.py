import base64

import pytest

from app.services import graph
from tests.conftest import FakeClient, FakeResponse


@pytest.fixture(autouse=True)
def _stub_token(monkeypatch):
    monkeypatch.setattr(graph.token_provider, "graph_token", lambda: "fake-token")


def _patch_client(monkeypatch, response: FakeResponse):
    monkeypatch.setattr(graph.httpx, "Client", lambda *a, **k: FakeClient(response))


def test_send_mail_with_attachment(monkeypatch):
    _patch_client(monkeypatch, FakeResponse(202))
    graph.send_mail(
        subject="Rel",
        body_html="<p>oi</p>",
        to=["a@x.com"],
        cc=["b@x.com"],
        pdf_bytes=b"%PDF-1.4 conteudo",
        pdf_name="rel.pdf",
    )
    body = FakeClient.last_request["json"]
    msg = body["message"]
    assert msg["subject"] == "Rel"
    assert msg["toRecipients"][0]["emailAddress"]["address"] == "a@x.com"
    att = msg["attachments"][0]
    assert att["name"] == "rel.pdf"
    assert base64.b64decode(att["contentBytes"]) == b"%PDF-1.4 conteudo"


def test_send_mail_attachment_too_big(monkeypatch):
    _patch_client(monkeypatch, FakeResponse(202))
    big = b"x" * (graph.INLINE_ATTACHMENT_LIMIT + 1)
    with pytest.raises(graph.GraphError):
        graph.send_mail(subject="s", body_html="b", to=["a@x.com"], pdf_bytes=big)


def test_send_mail_rate_limited(monkeypatch):
    _patch_client(monkeypatch, FakeResponse(429, headers={"Retry-After": "42"}))
    with pytest.raises(graph.RateLimited) as ei:
        graph.send_mail(subject="s", body_html="b", to=["a@x.com"])
    assert ei.value.retry_after == 42


def test_post_teams_message(monkeypatch):
    _patch_client(monkeypatch, FakeResponse(201))
    graph.post_teams_message(team_id="T1", channel_id="C1", html_content="<p>x</p>")
    req = FakeClient.last_request
    assert req["url"].endswith("/teams/T1/channels/C1/messages")
    assert req["json"]["body"]["contentType"] == "html"
