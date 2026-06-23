# BI Notify — Motor de Orquestração de Entrega de Relatórios Power BI

Substitui fluxos engessados do Power Automate por um backend assíncrono que:

1. Escuta a conclusão de um **Dataflow** (webhook).
2. Engatilha o refresh do **Modelo Semântico (dataset)**.
3. Exporta páginas específicas do relatório para **PDF** (com segmentação por área e **RLS**).
4. Cruza cada página com as **Regras de Roteamento** (Diretoria → Report → Destinatários).
5. Entrega por **e-mail (Outlook)** e notifica **canais do Teams** via Microsoft Graph.

## Stack

**Backend:** FastAPI · Celery + Redis · MSAL (Service Principal / App-Only) · Power BI REST API · Microsoft Graph API · PostgreSQL.
**Frontend:** React + TypeScript + Vite · Recharts (painel interno de operação).

## Frontend (`frontend/`)

Painel web para operar o motor:

- **Dashboard** — métricas (total, concluídas, falhas, taxa de sucesso) com gráficos por status e por diretoria; auto-refresh a cada 15s.
- **Regras de Roteamento** — CRUD completo (criar/editar/excluir), incluindo RLS, destinatários de e-mail/CC e canal do Teams.
- **Execuções** — monitor com auto-refresh (8s), filtro por status e **disparo manual** do pipeline.

```bash
cd frontend
cp .env.example .env        # VITE_API_BASE=/api (proxy do Vite -> backend)
npm install
npm run dev                 # http://localhost:5173
```

Em produção, o `frontend/Dockerfile` builda e serve via Nginx, com `/api/` fazendo proxy para o serviço `api`. Tudo sobe junto via `docker compose up --build` (serviços: db, redis, api, worker, frontend em :5173).

## Arquitetura

```
BI_Notify/
├── app/
│   ├── main.py                 # FastAPI (entrypoint)
│   ├── core/
│   │   ├── config.py           # Settings tipadas (Pydantic)
│   │   └── auth.py             # TokenProvider MSAL (App-Only) p/ Power BI e Graph
│   ├── db/
│   │   └── session.py          # Engine, SessionLocal, Base, get_db
│   ├── models/
│   │   ├── routing.py          # RoutingRule (Diretoria→Report→Destinatários)
│   │   └── execution.py        # ExecutionLog (auditoria)
│   ├── schemas/
│   │   └── webhooks.py         # Contratos de entrada/saída
│   ├── services/
│   │   ├── powerbi.py          # REST client: refresh, ExportTo, polling, download
│   │   └── graph.py            # sendMail + mensagem em canal do Teams
│   ├── workers/
│   │   ├── celery_app.py       # Instância/config do Celery
│   │   └── tasks.py            # Orquestração: refresh → export+polling → entrega
│   └── api/
│       ├── deps.py             # Auth do webhook (segredo compartilhado)
│       └── routes/
│           ├── webhooks.py     # POST /webhooks/dataflow-completed
│           └── status.py       # GET  /executions/{correlation_id}
├── frontend/                   # React + TS + Vite (painel de operação)
│   ├── src/api.ts              # cliente tipado da API
│   ├── src/pages/Dashboard.tsx # métricas + gráficos
│   ├── src/pages/RulesPage.tsx # CRUD de regras (+ RuleForm)
│   └── src/pages/ExecutionsPage.tsx # monitor + disparo manual
├── migrations/                 # Alembic (env.py + versions/0001_initial.py)
├── scripts/seed_routing.py     # Seed de exemplo das regras
├── docker-compose.yml          # db + redis + api + worker + frontend
├── Dockerfile
├── requirements.txt
└── .env.example
```

Fluxo das tasks (Celery):

```
refresh_dataset_task ─► wait_dataset_refresh_task (polling + backoff)
                                   └─► fan-out por RoutingRule ─► export_and_deliver_task
                                                                   (ExportTo → polling 429-aware → e-mail + Teams)
```

## Passo a passo de execução

### Opção A — Docker (recomendado: sobe tudo)

1. **Pré-requisitos:** Docker + Docker Compose instalados.
2. **Configurar variáveis:**
   ```bash
   cp .env.example .env
   # edite .env com as credenciais do Service Principal (tenant, client id, secret/cert)
   ```
3. **Subir os serviços** (db, redis, api, worker, frontend):
   ```bash
   docker compose up --build
   ```
4. **Aplicar migrations** (em outro terminal):
   ```bash
   docker compose exec api alembic upgrade head
   ```
5. **(Opcional) Seed de regras de exemplo:**
   ```bash
   docker compose exec api python -m scripts.seed_routing
   ```
6. **Acessar:**
   - Painel (frontend): <http://localhost:5173>
   - API + Swagger: <http://localhost:8000/docs>
   - Health: <http://localhost:8000/health>

### Opção B — Local sem Docker (desenvolvimento)

Backend (precisa de PostgreSQL e Redis acessíveis):
```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
cp .env.example .env                                 # ajuste DATABASE_URL/CELERY_* p/ localhost
alembic upgrade head
uvicorn app.main:app --reload                        # API em :8000
# Em outro terminal (mesma venv):
celery -A app.workers.celery_app.celery worker --loglevel=INFO
```

Frontend:
```bash
cd frontend
cp .env.example .env          # VITE_API_BASE=/api (proxy do Vite -> :8000)
npm install
npm run dev                   # painel em :5173
```

### Rodar os testes

```bash
pip install -r requirements-dev.txt
pytest            # testes unitários do backend (mockados, sem infra)
ruff check .      # lint
cd frontend && npm run build   # type-check (tsc) + build de produção
```

### Disparar o pipeline manualmente

Pelo painel (aba **Execuções** → "Disparo manual"), ou via API:

```bash
# Webhook oficial (gatilho do Dataflow) — exige o header de segredo:
curl -X POST http://localhost:8000/webhooks/dataflow-completed \
  -H "X-Webhook-Token: <WEBHOOK_SHARED_SECRET>" \
  -H "Content-Type: application/json" \
  -d '{"workspace_id":"<ws>","dataset_id":"<ds>"}'

# Disparo manual interno:
curl -X POST http://localhost:8000/executions/trigger \
  -H "Content-Type: application/json" \
  -d '{"workspace_id":"<ws>","dataset_id":"<ds>"}'
```

Disparos duplicados para o mesmo dataset numa janela de 5 min retornam **409 Conflict** (idempotência via Redis). Consultar status: `GET /executions/{correlation_id}` ou a aba **Execuções**.

## Pré-requisitos no Azure / Power BI

- **Service Principal** (Entra ID) com app registration. Em produção, autentique por **certificado** (`AZURE_CLIENT_CERT_*`) em vez de secret.
- No **Power BI Admin Portal**: habilitar "Service principals can use Power BI APIs" e adicionar o SP como **Admin/Contributor** dos workspaces. Exportação exige capacity **Premium/Embedded/Fabric** (não há suporte em PPU para `exportToFile` de relatórios).
- RLS via `effectiveIdentity` requer **write no dataset** + **contributor/admin no workspace**. Relatórios com rótulo de confidencialidade **não** exportam para PDF via Service Principal.
- **Graph (App-Only)**: permissões de aplicação `Mail.Send` (restrinja as mailboxes com *Application Access Policy*) e, para Teams, `ChannelMessage.Send` / `Group.ReadWrite.All` conforme política do tenant. Conceder **admin consent**.

## Considerações de segurança

- Webhook protegido por segredo comparado em tempo constante (`hmac.compare_digest`). Em produção, prefira validar assinatura HMAC do corpo + IP allowlist.
- Tokens só em memória; nada de credenciais em log. Use Key Vault para o secret/certificado.
- Sanitização: payloads validados por Pydantic; queries via ORM parametrizado (sem string SQL).
- Princípio do menor privilégio: SP restrito aos workspaces necessários; Mail.Send restrito por policy.

## Gargalos previstos e mitigação

- **Limite de 500 exports concorrentes por capacity** e 5 páginas processadas em paralelo → o fan-out usa `countdown` crescente para escalonar disparos; para volume alto, fila dedicada e *rate limiting* por capacity.
- **429 (rate limit)**: tratado em todas as chamadas, respeitando `Retry-After`; polling com **backoff exponencial** (cap configurável).
- **Worker preso no polling**: `worker_prefetch_multiplier=1`, `acks_late` e `task_time_limit`; separe a fila de export dos demais workers.
- **Cache de token por processo**: em frota grande, mover o `TokenCache` do MSAL para Redis evita N pedidos simultâneos ao Entra ID.
- **Anexo > 3 MB no Graph**: regra de roteamento permite enviar **link** em vez de anexo; acima do limite, usar *upload session* em rascunho.
```
