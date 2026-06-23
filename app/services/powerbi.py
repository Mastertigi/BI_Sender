"""Cliente da Power BI REST API.

Cobre o caminho do pipeline:
  refresh de dataflow -> refresh de dataset -> exportToFile -> polling -> download.

Decisões de engenharia:
- httpx síncrono: as tasks rodam em workers Celery (processo/thread dedicado),
  então não há ganho real de asyncio aqui e o código fica mais simples.
- `RateLimited` é exceção dedicada para o 429: o worker decide o retry,
  respeitando o header `Retry-After` quando presente.
- Status do export segue o contrato oficial: NotStarted | Running | Succeeded | Failed,
  com `percentComplete` para telemetria.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

import httpx

from app.core.auth import token_provider
from app.core.config import settings
from app.core.http import raise_for_transient, transient_retry


class PowerBIError(RuntimeError):
    """Erro genérico (não-recuperável) da Power BI API."""


class RateLimited(Exception):
    """429 Too Many Requests. Carrega o tempo sugerido de espera (s)."""

    def __init__(self, retry_after: int = 30) -> None:
        self.retry_after = retry_after
        super().__init__(f"Power BI rate limited; retry_after={retry_after}s")


@dataclass(slots=True)
class ExportStatus:
    export_id: str
    status: str  # NotStarted | Running | Succeeded | Failed
    percent_complete: int
    resource_location: Optional[str]  # URL do arquivo quando Succeeded


class PowerBIClient:
    def __init__(self, timeout: float = 60.0) -> None:
        self._timeout = timeout

    # ── infra HTTP ──────────────────────────────────────────────
    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {token_provider.powerbi_token()}",
            "Content-Type": "application/json",
        }

    @transient_retry
    def _request(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        url = f"{settings.powerbi_api_base}{path}"
        with httpx.Client(timeout=self._timeout) as client:
            resp = client.request(method, url, headers=self._headers(), **kwargs)

        # Rate limit explícito: o worker decide o retry respeitando Retry-After.
        if resp.status_code == 429:
            retry_after = int(resp.headers.get("Retry-After", "30"))
            raise RateLimited(retry_after=retry_after)
        # 5xx -> transiente: retry automático (tenacity) com backoff + jitter.
        raise_for_transient(resp)
        if resp.status_code >= 400:
            raise PowerBIError(
                f"{method} {path} -> {resp.status_code}: {resp.text[:500]}"
            )
        return resp

    # ── Refresh ─────────────────────────────────────────────────
    def refresh_dataset(self, workspace_id: str, dataset_id: str) -> None:
        """Engatilha refresh assíncrono do modelo semântico (dataset)."""
        self._request(
            "POST",
            f"/groups/{workspace_id}/datasets/{dataset_id}/refreshes",
            json={"notifyOption": "NoNotification"},
        )

    def get_dataset_refresh_status(
        self, workspace_id: str, dataset_id: str
    ) -> str:
        """Status do refresh mais recente: Unknown(=em andamento)|Completed|Failed."""
        resp = self._request(
            "GET",
            f"/groups/{workspace_id}/datasets/{dataset_id}/refreshes?$top=1",
        )
        items = resp.json().get("value", [])
        if not items:
            return "Unknown"
        return items[0].get("status", "Unknown")

    # ── Export to file ──────────────────────────────────────────
    def start_export(
        self,
        workspace_id: str,
        report_id: str,
        page_name: str,
        *,
        rls_username: Optional[str] = None,
        rls_roles: Optional[list[str]] = None,
        dataset_id: Optional[str] = None,
        report_level_filters: Optional[str] = None,
        locale: str = "pt-BR",
        fmt: str = "PDF",
    ) -> str:
        """Dispara o job de exportação e retorna o exportId.

        Exporta apenas a página informada (segmentação por área) e aplica RLS
        via effectiveIdentity quando configurado.
        """
        export_config: dict[str, Any] = {
            "settings": {"locale": locale},
            "pages": [{"pageName": page_name}],
        }
        if report_level_filters:
            export_config["reportLevelFilters"] = [{"filter": report_level_filters}]

        body: dict[str, Any] = {"format": fmt, "powerBIReportConfiguration": export_config}

        # RLS: effectiveIdentity exige write no dataset + admin/contributor no workspace.
        if rls_username:
            identity: dict[str, Any] = {
                "username": rls_username,
                "roles": rls_roles or [],
                "datasets": [dataset_id] if dataset_id else [],
            }
            export_config["identities"] = [identity]

        resp = self._request(
            "POST",
            f"/groups/{workspace_id}/reports/{report_id}/ExportTo",
            json=body,
        )
        export_id = resp.json().get("id")
        if not export_id:
            raise PowerBIError(f"ExportTo não retornou id: {resp.text[:300]}")
        return export_id

    def get_export_status(
        self, workspace_id: str, report_id: str, export_id: str
    ) -> ExportStatus:
        resp = self._request(
            "GET",
            f"/groups/{workspace_id}/reports/{report_id}/exports/{export_id}",
        )
        data = resp.json()
        return ExportStatus(
            export_id=export_id,
            status=data.get("status", "Unknown"),
            percent_complete=int(data.get("percentComplete", 0)),
            resource_location=data.get("resourceLocation"),
        )

    def download_export(
        self, workspace_id: str, report_id: str, export_id: str
    ) -> bytes:
        """Baixa o arquivo do export concluído (em memória)."""
        resp = self._request(
            "GET",
            f"/groups/{workspace_id}/reports/{report_id}/exports/{export_id}/file",
        )
        return resp.content


powerbi_client = PowerBIClient()
