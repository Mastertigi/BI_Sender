"""CRUD de Regras de Roteamento."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.routing import RoutingRule
from app.schemas.routing import (
    RoutingRuleCreate,
    RoutingRuleOut,
    RoutingRuleUpdate,
)

router = APIRouter(prefix="/routing-rules", tags=["routing-rules"])


@router.get("", response_model=list[RoutingRuleOut])
def list_rules(
    db: Session = Depends(get_db),
    active: bool | None = Query(None, description="Filtra por status ativo"),
    diretoria: str | None = Query(None),
):
    stmt = select(RoutingRule).order_by(RoutingRule.diretoria, RoutingRule.id)
    if active is not None:
        stmt = stmt.where(RoutingRule.active.is_(active))
    if diretoria:
        stmt = stmt.where(RoutingRule.diretoria == diretoria)
    return db.scalars(stmt).all()


@router.get("/{rule_id}", response_model=RoutingRuleOut)
def get_rule(rule_id: int, db: Session = Depends(get_db)):
    rule = db.get(RoutingRule, rule_id)
    if rule is None:
        raise HTTPException(status_code=404, detail="Regra não encontrada.")
    return rule


@router.post("", response_model=RoutingRuleOut, status_code=status.HTTP_201_CREATED)
def create_rule(payload: RoutingRuleCreate, db: Session = Depends(get_db)):
    rule = RoutingRule(
        **payload.model_dump(exclude_none=False),
    )
    # EmailStr -> str para o ARRAY(String) do Postgres.
    rule.email_to = [str(e) for e in payload.email_to]
    rule.email_cc = [str(e) for e in payload.email_cc] if payload.email_cc else None
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


@router.put("/{rule_id}", response_model=RoutingRuleOut)
def update_rule(
    rule_id: int, payload: RoutingRuleUpdate, db: Session = Depends(get_db)
):
    rule = db.get(RoutingRule, rule_id)
    if rule is None:
        raise HTTPException(status_code=404, detail="Regra não encontrada.")
    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        if key in {"email_to", "email_cc"} and value is not None:
            value = [str(e) for e in value]
        setattr(rule, key, value)
    db.commit()
    db.refresh(rule)
    return rule


@router.delete("/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_rule(rule_id: int, db: Session = Depends(get_db)):
    rule = db.get(RoutingRule, rule_id)
    if rule is None:
        raise HTTPException(status_code=404, detail="Regra não encontrada.")
    db.delete(rule)
    db.commit()
