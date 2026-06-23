"""Cliente do Microsoft Graph: envio de e-mail (Outlook) e notificação no Teams.

- E-mail: POST /users/{id}/sendMail (App-Only exige Mail.Send de aplicação +,
  idealmente, Application Access Policy restringindo as mailboxes permitidas).
- Teams: POST /teams/{team-id}/channels/{channel-id}/messages
  (App-Only exige ChannelMessage.Send / Group.ReadWrite.All conforme tenant).

O anexo do PDF vai inline como fileAttachment em base64. O Graph aceita anexo
inline até ~3 MB no sendMail; acima disso use uma sessão de upload em rascunho.
Por isso a regra de roteamento permite enviar apenas o LINK em vez do anexo.
"""
from __future__ import annotations

import base64
from typing import Any, Optional

import httpx

from app.core.auth import token_provider
from app.core.config import settings
from app.core.http import raise_for_transient, transient_retry

# Limite prático para anexo inline no sendMail (3 MB).
INLINE_ATTACHMENT_LIMIT = 3 * 1024 * 1024


class GraphError(RuntimeError):
    pass


class RateLimited(Exception):
    def __init__(self, retry_after: int = 30) -> None:
        self.retry_after = retry_after
        super().__init__(f"Graph rate limited; retry_after={retry_after}s")


def _headers() -> dict[str, str]:
    return {
        "Authorization": f"Bearer {token_provider.graph_token()}",
        "Content-Type": "application/json",
    }


@transient_retry
def _post(path: str, payload: dict[str, Any]) -> httpx.Response:
    url = f"{settings.graph_api_base}{path}"
    with httpx.Client(timeout=60.0) as client:
        resp = client.post(url, headers=_headers(), json=payload)
    if resp.status_code == 429:
        raise RateLimited(int(resp.headers.get("Retry-After", "30")))
    raise_for_transient(resp)  # 5xx -> retry automático
    if resp.status_code >= 400:
        raise GraphError(f"POST {path} -> {resp.status_code}: {resp.text[:500]}")
    return resp


def send_mail(
    *,
    subject: str,
    body_html: str,
    to: list[str],
    cc: Optional[list[str]] = None,
    pdf_bytes: Optional[bytes] = None,
    pdf_name: str = "relatorio.pdf",
    sender_user_id: Optional[str] = None,
) -> None:
    """Envia e-mail via /users/{id}/sendMail, com PDF anexo opcional."""
    sender = sender_user_id or settings.graph_sender_user_id

    def recipients(addrs: list[str]) -> list[dict[str, Any]]:
        return [{"emailAddress": {"address": a}} for a in addrs]

    message: dict[str, Any] = {
        "subject": subject,
        "body": {"contentType": "HTML", "content": body_html},
        "toRecipients": recipients(to),
    }
    if cc:
        message["ccRecipients"] = recipients(cc)

    if pdf_bytes is not None:
        if len(pdf_bytes) > INLINE_ATTACHMENT_LIMIT:
            raise GraphError(
                f"PDF de {len(pdf_bytes)} bytes excede o limite inline de "
                f"{INLINE_ATTACHMENT_LIMIT} bytes; envie por link ou upload session."
            )
        message["attachments"] = [
            {
                "@odata.type": "#microsoft.graph.fileAttachment",
                "name": pdf_name,
                "contentType": "application/pdf",
                "contentBytes": base64.b64encode(pdf_bytes).decode("ascii"),
            }
        ]

    _post(f"/users/{sender}/sendMail", {"message": message, "saveToSentItems": True})


def post_teams_message(
    *,
    team_id: str,
    channel_id: str,
    html_content: str,
) -> None:
    """Posta mensagem (HTML) em um canal do Teams."""
    payload = {"body": {"contentType": "html", "content": html_content}}
    _post(f"/teams/{team_id}/channels/{channel_id}/messages", payload)
