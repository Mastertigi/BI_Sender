"""Aplicação FastAPI — ponto de entrada da API de orquestração."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.api.routes import routing as routing_routes
from app.api.routes import status as status_routes
from app.api.routes import webhooks
from app.core.config import settings
from app.core.idempotency import ping_redis
from app.core.logging import setup_logging
from app.db.session import Base, engine

# Importa modelos para registrar metadata antes do create_all.
import app.models  # noqa: F401

setup_logging()
logger = logging.getLogger("bi_notify")


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Em produção use Alembic; create_all é conveniência de bootstrap/dev.
    Base.metadata.create_all(bind=engine)
    logger.info("BI Notify API iniciada")
    yield


app = FastAPI(
    title="BI Notify — Orquestração de Entrega de Relatórios Power BI",
    version="1.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(webhooks.router)
app.include_router(status_routes.router)
app.include_router(routing_routes.router)


@app.get("/health", tags=["infra"])
def health():
    """Liveness + readiness: verifica DB e Redis."""
    db_ok = True
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as exc:  # noqa: BLE001
        logger.warning("Healthcheck DB falhou: %s", exc)
        db_ok = False

    redis_ok = ping_redis()
    status = "ok" if (db_ok and redis_ok) else "degraded"
    body = {"status": status, "db": db_ok, "redis": redis_ok}
    return JSONResponse(body, status_code=200 if status == "ok" else 503)
