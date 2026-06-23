"""Seed de exemplo de regras de roteamento (Diretoria -> Report -> Destinatários).

Uso (com .env carregado):  python -m scripts.seed_routing
"""
from __future__ import annotations

from app.db.session import Base, SessionLocal, engine
from app.models.routing import RoutingRule


def run() -> None:
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        db.add_all(
            [
                RoutingRule(
                    diretoria="Financeiro",
                    workspace_id="00000000-0000-0000-0000-000000000000",
                    dataset_id="11111111-1111-1111-1111-111111111111",
                    report_id="22222222-2222-2222-2222-222222222222",
                    page_name="ReportSection_financeiro",
                    report_display_name="Financeiro",
                    rls_username="financeiro@empresa.com.br",
                    rls_roles=["Financeiro"],
                    email_to=["diretor.financeiro@empresa.com.br"],
                    email_cc=["analise@empresa.com.br"],
                    teams_team_id="33333333-3333-3333-3333-333333333333",
                    teams_channel_id="19:abcdef...@thread.tacv2",
                    attach_pdf=True,
                ),
                RoutingRule(
                    diretoria="Vendas",
                    workspace_id="00000000-0000-0000-0000-000000000000",
                    dataset_id="11111111-1111-1111-1111-111111111111",
                    report_id="22222222-2222-2222-2222-222222222222",
                    page_name="ReportSection_vendas",
                    report_display_name="Vendas",
                    rls_username="vendas@empresa.com.br",
                    rls_roles=["Vendas"],
                    email_to=["diretor.comercial@empresa.com.br"],
                    attach_pdf=True,
                ),
            ]
        )
        db.commit()
    print("Seed concluído.")


if __name__ == "__main__":
    run()
