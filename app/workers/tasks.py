"""Tasks Celery que orquestram o pipeline ponta a ponta.

Cadeia lógica disparada pelo webhook de conclusão do Dataflow:

    refresh_dataset_task            (engatilha refresh do modelo semântico)
        -> wait_dataset_refresh_task  (polling do refresh)
            -> fan-out por RoutingRule:
                export_and_deliver_task  (ExportTo + polling + entrega)

Pontos críticos tratados:
- Polling com backoff exponencial (cap em EXPORT_POLL_MAX_DELAY).
- 429 Too Many Requests respeitando Retry-After, com `self.retry`.
- Timeout global por export (EXPORT_POLL_TIMEOUT) para não vazar workers.
- Toda transição de estado é persistida em ExecutionLog (auditoria).

Gargalo previsto: cada export ocupa um worker durante o polling. Para volume
alto, dispare `export_and_deliver_task` em fila separada com seus próprios
workers e respeite o teto de 500 exports concorrentes por capacity, escalonando
no tempo (countdown progressivo no fan-out).
"""
from __future__ import annotations

import time
from typing import Any, Optional

from celery import shared_task
from celery.utils.log import get_task_logger

from app.core.config import settings
from app.db.session import SessionLocal
from app.models.execution import ExecutionLog, ExecutionStatus
from app.models.routing import RoutingRule
from app.services import graph
from app.services.powerbi import PowerBIError, RateLimited, powerbi_client

logger = get_task_logger(__name__)

# Status terminais do refresh de dataset.
_REFRESH_DONE = {"Completed"}
_REFRESH_FAILED = {"Failed", "Disabled"}


# ── helpers de log ──────────────────────────────────────────────
def _set_status(
    correlation_id: str,
    status: ExecutionStatus,
    *,
    error: Optional[str] = None,
    export_id: Optional[str] = None,
    **fields: Any,
) -> None:
    """Atualiza (ou cria) a linha de auditoria do correlation_id."""
    with SessionLocal() as db:
        log = (
            db.query(ExecutionLog)
            .filter(ExecutionLog.correlation_id == correlation_id)
            .order_by(ExecutionLog.id.desc())
            .first()
        )
        if log is None:
            log = ExecutionLog(correlation_id=correlation_id)
            db.add(log)
        log.status = status
        if error is not None:
            log.error_detail = error
        if export_id is not None:
            log.powerbi_export_id = export_id
        for key, value in fields.items():
            setattr(log, key, value)
        db.commit()


# ── 1. Refresh do dataset ───────────────────────────────────────
@shared_task(
    bind=True,
    name="bi_notify.refresh_dataset",
    max_retries=5,
    default_retry_delay=30,
)
def refresh_dataset_task(
    self, correlation_id: str, workspace_id: str, dataset_id: str
) -> dict[str, str]:
    """Engatilha o refresh do modelo semântico e encadeia o polling."""
    _set_status(
        correlation_id,
        ExecutionStatus.REFRESHING_DATASET,
        workspace_id=workspace_id,
        dataset_id=dataset_id,
    )
    try:
        powerbi_client.refresh_dataset(workspace_id, dataset_id)
    except RateLimited as exc:
        raise self.retry(exc=exc, countdown=exc.retry_after)
    except PowerBIError as exc:
        _set_status(correlation_id, ExecutionStatus.FAILED, error=str(exc))
        raise

    # Encadeia o polling do refresh.
    wait_dataset_refresh_task.delay(correlation_id, workspace_id, dataset_id, 0)
    return {"correlation_id": correlation_id, "state": "refresh_triggered"}


@shared_task(
    bind=True,
    name="bi_notify.wait_dataset_refresh",
    max_retries=None,  # controlamos o limite via attempt/timeout
)
def wait_dataset_refresh_task(
    self,
    correlation_id: str,
    workspace_id: str,
    dataset_id: str,
    attempt: int,
) -> dict[str, str]:
    """Polling do refresh com backoff; ao concluir, faz fan-out das regras."""
    # Backoff exponencial limitado.
    delay = min(
        settings.export_poll_initial_delay * (2**attempt),
        settings.export_poll_max_delay,
    )
    # Teto de tempo: attempt * delay médio não pode estourar o timeout.
    if delay * attempt > settings.export_poll_timeout:
        _set_status(
            correlation_id,
            ExecutionStatus.FAILED,
            error="Timeout aguardando refresh do dataset.",
        )
        raise PowerBIError("Timeout no refresh do dataset")

    try:
        status = powerbi_client.get_dataset_refresh_status(workspace_id, dataset_id)
    except RateLimited as exc:
        raise self.retry(exc=exc, countdown=exc.retry_after)

    if status in _REFRESH_FAILED:
        _set_status(
            correlation_id,
            ExecutionStatus.FAILED,
            error=f"Refresh do dataset falhou: {status}",
        )
        raise PowerBIError(f"Refresh falhou: {status}")

    if status not in _REFRESH_DONE:
        # Ainda em andamento: re-agenda com o próximo delay.
        raise self.retry(countdown=delay, args=(
            correlation_id, workspace_id, dataset_id, attempt + 1,
        ))

    # Refresh concluído -> fan-out por regra de roteamento.
    _fan_out_routes(correlation_id, workspace_id, dataset_id)
    return {"correlation_id": correlation_id, "state": "refresh_completed"}


def _fan_out_routes(
    correlation_id: str, workspace_id: str, dataset_id: str
) -> None:
    """Cria um job de export+entrega por RoutingRule ativa do dataset.

    Escalona no tempo (countdown crescente) para não estourar o limite de
    exports concorrentes por capacity (429).
    """
    with SessionLocal() as db:
        rules = (
            db.query(RoutingRule)
            .filter(
                RoutingRule.workspace_id == workspace_id,
                RoutingRule.dataset_id == dataset_id,
                RoutingRule.active.is_(True),
            )
            .all()
        )
        rule_ids = [r.id for r in rules]

    if not rule_ids:
        logger.warning("Nenhuma RoutingRule ativa para dataset %s", dataset_id)
        _set_status(correlation_id, ExecutionStatus.SUCCEEDED)
        return

    for i, rule_id in enumerate(rule_ids):
        export_and_deliver_task.apply_async(
            args=(correlation_id, rule_id),
            countdown=i * 3,  # 3s entre disparos (suaviza carga na capacity)
        )


# ── 2. Export + entrega ─────────────────────────────────────────
@shared_task(
    bind=True,
    name="bi_notify.export_and_deliver",
    max_retries=8,
    default_retry_delay=30,
)
def export_and_deliver_task(
    self, correlation_id: str, rule_id: int
) -> dict[str, str]:
    """Exporta a página (com RLS) para PDF, faz polling e entrega."""
    with SessionLocal() as db:
        rule = db.get(RoutingRule, rule_id)
        if rule is None or not rule.active:
            logger.warning("RoutingRule %s inexistente/inativa", rule_id)
            return {"state": "skipped"}
        # Materializa os campos antes de fechar a sessão.
        r = _RuleSnapshot.from_model(rule)

    _set_status(
        correlation_id,
        ExecutionStatus.EXPORTING,
        diretoria=r.diretoria,
        report_id=r.report_id,
        page_name=r.page_name,
    )

    # 2.1 Dispara o export.
    try:
        export_id = powerbi_client.start_export(
            r.workspace_id,
            r.report_id,
            r.page_name,
            rls_username=r.rls_username,
            rls_roles=r.rls_roles,
            dataset_id=r.dataset_id,
            report_level_filters=r.report_level_filters,
        )
    except RateLimited as exc:
        raise self.retry(exc=exc, countdown=exc.retry_after)
    except PowerBIError as exc:
        _set_status(correlation_id, ExecutionStatus.FAILED, error=str(exc))
        raise

    _set_status(correlation_id, ExecutionStatus.EXPORTING, export_id=export_id)

    # 2.2 Polling com backoff exponencial até concluir.
    pdf_bytes = _poll_until_ready(r, export_id, correlation_id, task=self)

    # 2.3 Entrega.
    _set_status(correlation_id, ExecutionStatus.DELIVERING, export_id=export_id)
    try:
        _deliver(r, pdf_bytes)
    except graph.RateLimited as exc:
        raise self.retry(exc=exc, countdown=exc.retry_after)
    except graph.GraphError as exc:
        _set_status(correlation_id, ExecutionStatus.FAILED, error=str(exc))
        raise

    _set_status(correlation_id, ExecutionStatus.SUCCEEDED, export_id=export_id)
    return {"correlation_id": correlation_id, "state": "delivered"}


def _poll_until_ready(
    r: "_RuleSnapshot", export_id: str, correlation_id: str, *, task: Any
) -> bytes:
    """Polling bloqueante com backoff exponencial e respeito ao 429.

    Roda dentro da própria task (bloqueia o worker). É intencional: mantém o
    fluxo simples e o acks_late protege contra perda em caso de crash.
    """
    elapsed = 0
    delay = settings.export_poll_initial_delay
    while elapsed < settings.export_poll_timeout:
        try:
            status = powerbi_client.get_export_status(
                r.workspace_id, r.report_id, export_id
            )
        except RateLimited as exc:
            # 429 no polling: espera o Retry-After e NÃO conta como backoff normal.
            time.sleep(exc.retry_after)
            elapsed += exc.retry_after
            continue

        if status.status == "Succeeded":
            return powerbi_client.download_export(
                r.workspace_id, r.report_id, export_id
            )
        if status.status == "Failed":
            _set_status(
                correlation_id,
                ExecutionStatus.FAILED,
                error="Export job retornou status Failed.",
                export_id=export_id,
            )
            raise PowerBIError(f"Export {export_id} falhou")

        logger.info(
            "Export %s em %d%% (status=%s); aguardando %ds",
            export_id, status.percent_complete, status.status, delay,
        )
        time.sleep(delay)
        elapsed += delay
        delay = min(delay * 2, settings.export_poll_max_delay)  # backoff exponencial

    _set_status(
        correlation_id,
        ExecutionStatus.FAILED,
        error="Timeout no polling da exportação.",
        export_id=export_id,
    )
    raise PowerBIError(f"Timeout aguardando export {export_id}")


def _deliver(r: "_RuleSnapshot", pdf_bytes: bytes) -> None:
    """Aplica a regra: e-mail (anexo ou link) + notificação no Teams."""
    pdf_name = f"{r.report_display_name}.pdf"
    body_html = (
        "<p>Olá,</p>"
        f"<p>Segue o relatório <b>{r.report_display_name}</b> "
        f"(área: {r.diretoria}), atualizado automaticamente.</p>"
        "<p>Qualquer dúvida, estou à disposição.</p>"
        "<p>Atenciosamente,<br>Equipe de Inteligência de Dados</p>"
    )

    if r.email_to:
        graph.send_mail(
            subject=f"Relatório BI — {r.report_display_name} ({r.diretoria})",
            body_html=body_html,
            to=r.email_to,
            cc=r.email_cc,
            pdf_bytes=pdf_bytes if r.attach_pdf else None,
            pdf_name=pdf_name,
        )

    if r.teams_team_id and r.teams_channel_id:
        graph.post_teams_message(
            team_id=r.teams_team_id,
            channel_id=r.teams_channel_id,
            html_content=(
                f"<p><b>Relatório atualizado:</b> {r.report_display_name} "
                f"({r.diretoria})</p><p>Enviado por e-mail aos destinatários.</p>"
            ),
        )


class _RuleSnapshot:
    """DTO imutável com os campos da RoutingRule, desacoplado da sessão ORM."""

    __slots__ = (
        "diretoria", "workspace_id", "dataset_id", "report_id", "page_name",
        "report_display_name", "rls_username", "rls_roles",
        "report_level_filters", "email_to", "email_cc",
        "teams_team_id", "teams_channel_id", "attach_pdf",
    )

    @classmethod
    def from_model(cls, m: RoutingRule) -> "_RuleSnapshot":
        s = cls()
        s.diretoria = m.diretoria
        s.workspace_id = m.workspace_id
        s.dataset_id = m.dataset_id
        s.report_id = m.report_id
        s.page_name = m.page_name
        s.report_display_name = m.report_display_name
        s.rls_username = m.rls_username
        s.rls_roles = m.rls_roles
        s.report_level_filters = m.report_level_filters
        s.email_to = list(m.email_to or [])
        s.email_cc = list(m.email_cc) if m.email_cc else None
        s.teams_team_id = m.teams_team_id
        s.teams_channel_id = m.teams_channel_id
        s.attach_pdf = m.attach_pdf
        return s
