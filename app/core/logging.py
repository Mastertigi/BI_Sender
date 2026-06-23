"""Configuração de logging estruturado (JSON-friendly).

Em produção, logs em uma linha facilitam ingestão por Azure Monitor / Log
Analytics. Evita logar credenciais: nunca passe tokens ao logger.
"""
from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        # Campos extras (ex.: correlation_id) passados via `extra=`.
        if hasattr(record, "correlation_id"):
            payload["correlation_id"] = record.correlation_id  # type: ignore[attr-defined]
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


def setup_logging(level: str = "INFO") -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)
    # Reduz ruído de libs.
    for noisy in ("httpx", "urllib3", "msal"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
