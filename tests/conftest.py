"""Fixtures e configuração de ambiente para os testes (sem infra externa)."""
from __future__ import annotations

import os

# Define env ANTES de importar qualquer módulo que instancie Settings.
os.environ.setdefault("AZURE_TENANT_ID", "tenant")
os.environ.setdefault("AZURE_CLIENT_ID", "client")
os.environ.setdefault("AZURE_CLIENT_SECRET", "secret")
os.environ.setdefault("GRAPH_SENDER_USER_ID", "bot@empresa.com")
os.environ.setdefault("DATABASE_URL", "postgresql+psycopg2://u:p@localhost/x")
os.environ.setdefault("CELERY_BROKER_URL", "redis://localhost:6379/0")
os.environ.setdefault("CELERY_RESULT_BACKEND", "redis://localhost:6379/1")
os.environ.setdefault("WEBHOOK_SHARED_SECRET", "test-secret")
os.environ.setdefault("CORS_ORIGINS", "http://a.com, http://b.com")


class FakeResponse:
    """Resposta httpx mínima para testes."""

    def __init__(self, status_code=200, json_data=None, headers=None, content=b""):
        self.status_code = status_code
        self._json = json_data or {}
        self.headers = headers or {}
        self.content = content
        self.text = str(json_data)

    def json(self):
        return self._json


class FakeClient:
    """Substitui httpx.Client capturando a última requisição."""

    last_request: dict = {}

    def __init__(self, response: FakeResponse):
        self._response = response

    def __call__(self, *args, **kwargs):
        return self

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def request(self, method, url, **kwargs):
        FakeClient.last_request = {"method": method, "url": url, **kwargs}
        return self._response

    def post(self, url, **kwargs):
        FakeClient.last_request = {"method": "POST", "url": url, **kwargs}
        return self._response
