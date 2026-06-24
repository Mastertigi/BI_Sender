# BI Notify — Motor de Orquestração e Entrega de Relatórios Power BI

Motor assíncrono **pro-code** que automatiza a entrega de relatórios do Power BI
em PDF, substituindo fluxos engessados do Power Automate por uma aplicação
backend escalável e resiliente, com painel web de operação.

**Do link solto a PDFs por área, enviados por e-mail e Teams.**

O sistema replica, via código e chamadas de API, o fluxo completo:

1. Escuta a conclusão da atualização de um **Dataflow** (webhook).
2. Engatilha a atualização do **Modelo Semântico (dataset)** correspondente.
3. Exporta páginas específicas do relatório para **PDF** (respeitando segmentação por área e **RLS**).
4. Consulta o banco de **Regras de Roteamento** (cruza página exportada com diretoria/destinatário).
5. Dispara o envio dos PDFs por **e-mail** (anexo ou link) e notifica canais no **Microsoft Teams**.

---

## Sumário

- [Stack](#stack)
- [Arquitetura](#arquitetura)
- [Funcionalidades](#funcionalidades)
- [Executável único (BI_Notify.exe)](#executável-único-bi_notifyexe)
- [Passo a passo de execução](#passo-a-passo-de-execução)
- [Painel web](#painel-web)
- [Endpoints da API](#endpoints-da-api)
- [Pré-requisitos no Azure / Power BI](#pré-requisitos-no-azure--power-bi)
- [Onde achar cada ID](#onde-achar-cada-id)
- [Testes e qualidade](#testes-e-qualidade)
- [Segurança](#segurança)
- [Gargalos previstos e mitigação](#gargalos-previstos-e-mitigação)

---

## Stack

**Backend:** Python · FastAPI · Celery + Redis · MSAL (Service Principal / App-Only) ·
Power BI REST API · Microsoft Graph API · PostgreSQL · Alembic · tenacity.

**Frontend:** React + TypeScript + Vite · React Router · Recharts.

**Infra:** Docker Compose (db, redis, api, worker, frontend) · Nginx (serve o SPA + proxy `/api`).

---

## Arquitetura

```
BI_Notify/
├── app/
│   ├── main.py                 # FastAPI (entrypoint) + /health (db+redis)
│   ├── core/
│   │   ├── config.py           # Settings tipadas (Pydantic) + CORS
│   │   ├── auth.py             # TokenProvider MSAL (App-Only) p/ Power BI e Graph
│   │   ├── http.py             # Retry com backoff+jitter p/ erros transientes
│   │   ├── idempotency.py      # Lock no Redis (anti-duplicidade) + ping
│   │   └── logging.py          # Logging estruturado (JSON)
│   ├── db/session.py           # Engine, SessionLocal, Base, get_db
│   ├── models/
│   │   ├── routing.py          # RoutingRule (Diretoria→Report→Destinatários)
│   │   └── execution.py        # ExecutionLog (auditoria)
│   ├── schemas/                # Contratos Pydantic (webhooks, routing, executions)
│   ├── services/
│   │   ├── powerbi.py          # REST client: refresh, ExportTo, polling, download
│   │   ├── graph.py            # sendMail + mensagem em canal do Teams
│   │   └── pipeline.py         # Orquestração: ponto único de disparo (idempotente)
│   ├── workers/
│   │   ├── celery_app.py       # Instância/config do Celery
│   │   └── tasks.py            # refresh → export+polling(429-aware) → entrega
│   └── api/
│       ├── deps.py             # Auth do webhook (segredo, tempo constante)
│       └── routes/             # webhooks, executions (+metrics, +trigger), routing-rules
├── frontend/
│   ├── src/api.ts              # cliente tipado da API
│   ├── src/components/Pipeline.tsx  # hero + fluxo de 5 passos
│   └── src/pages/              # Dashboard, RulesPage(+RuleForm), ExecutionsPage, Docs
├── migrations/                 # Alembic (env.py + versions/0001_initial.py)
├── scripts/seed_routing.py     # Seed de exemplo das regras
├── tests/                      # pytest (unitários, mockados)
├── launcher/run.py             # Launcher da stack (empacotável como .exe)
├── build_exe.bat               # Gera BI_Notify.exe (PyInstaller)
├── BI_Notify.bat               # Sobe tudo sem compilar
├── push_to_github.ps1          # Commit + push para o repositório
├── docker-compose.yml · Dockerfile · pyproject.toml
└── requirements.txt · requirements-dev.txt · .env.example
```

Fluxo das tasks (Celery):

```
refresh_dataset_task ─► wait_dataset_refresh_task (polling + backoff)
                              └─► fan-out por RoutingRule ─► export_and_deliver_task
                                                             (ExportTo → polling 429-aware → e-mail + Teams)
```

---

## Funcionalidades

- **Pipeline assíncrono** ponta a ponta com Celery, sem timeout HTTP durante exportações pesadas.
- **Polling com backoff exponencial** e tratamento de **429 (rate limit)** respeitando `Retry-After`.
- **Retry automático** para falhas transientes (5xx/timeout) via tenacity.
- **Idempotência**: disparos duplicados do mesmo dataset (janela de 5 min) retornam **409** (lock no Redis).
- **RLS** aplicado na exportação via `effectiveIdentity`.
- **Entrega flexível**: e-mail com PDF anexo **ou** link, e notificação em canal do Teams.
- **Painel web**: dashboard com métricas, CRUD de regras, monitor de execuções, disparo manual e documentação.
- **Observabilidade**: logging JSON e `/health` checando banco e Redis.
- **Auditoria**: cada disparo gravado em `ExecutionLog` com `correlation_id`.

---

## Executável único (BI_Notify.exe)

Launcher de um clique que sobe **tudo** (Postgres, Redis, API, worker e frontend)
via Docker, aplica as migrations e abre o painel. Fechar a janela (Ctrl+C) derruba a stack.

**Pré-requisitos:** Docker Desktop instalado e em execução; Python 3.10+ (só para gerar o .exe).

```bat
build_exe.bat        REM gera BI_Notify.exe na raiz (uma vez)
```

Depois é só dar **duplo-clique no BI_Notify.exe**. Sem querer compilar, use o
`BI_Notify.bat`, que roda o mesmo launcher direto com o Python.

> O .exe é um **orquestrador** do Docker (não embute Postgres/Redis) — mantém a
> arquitetura de produção. O binário precisa ser gerado no Windows (PyInstaller
> não faz cross-compile a partir de Linux).

---

## Passo a passo de execução

### Opção A — Docker (recomendado)

1. **Configurar variáveis:**
   ```bash
   cp .env.example .env
   # edite o .env com as credenciais do Service Principal
   ```
2. **Subir os serviços:**
   ```bash
   docker compose up --build
   ```
3. **Aplicar migrations** (outro terminal):
   ```bash
   docker compose exec api alembic upgrade head
   ```
4. **(Opcional) Seed de regras de exemplo:**
   ```bash
   docker compose exec api python -m scripts.seed_routing
   ```
5. **Acessar:** Painel <http://localhost:5173> · API/Docs <http://localhost:8000/docs> · Health <http://localhost:8000/health>

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

### Disparar o pipeline

Pelo painel (**Execuções → Disparo manual**), ou via API:

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

---

## Painel web

- **Dashboard** — hero explicativo, fluxo de 5 passos, métricas (total, concluídas, falhas, taxa de sucesso) e gráficos por status e por diretoria; auto-refresh a cada 15s.
- **Regras de Roteamento** — CRUD completo. O formulário é dividido em seções e **cada campo traz onde encontrar o valor** (Workspace/Dataset/Report/Página, RLS, Teams).
- **Execuções** — monitor com auto-refresh (8s), filtro por status e disparo manual.
- **Documentação** — guia de configuração de ponta a ponta dentro do próprio app (`/docs`).

---

## Endpoints da API

| Método | Rota | Descrição |
| --- | --- | --- |
| `POST` | `/webhooks/dataflow-completed` | Gatilho do Dataflow (header `X-Webhook-Token`). |
| `POST` | `/executions/trigger` | Disparo manual do pipeline. |
| `GET` | `/executions` | Lista paginada de execuções (filtro por status). |
| `GET` | `/executions/metrics` | Agregações para o dashboard. |
| `GET` | `/executions/{correlation_id}` | Trilha de auditoria de um disparo. |
| `GET/POST/PUT/DELETE` | `/routing-rules` | CRUD das regras de roteamento. |
| `GET` | `/health` | Liveness/readiness (db + redis). |

Documentação interativa (Swagger) em `/docs` na API.

---

## Pré-requisitos no Azure / Power BI

- **Service Principal** (Entra ID) com app registration. Em produção, autentique por **certificado** (`AZURE_CLIENT_CERT_*`) em vez de secret.
- **Power BI Admin Portal**: habilitar "Service principals can use Power BI APIs"; adicionar o SP como **Admin/Member** dos workspaces. Exportação exige capacity **Premium/Embedded/Fabric** (sem suporte a PPU para `exportToFile` de relatórios).
- **RLS** via `effectiveIdentity` requer **write no dataset** + Admin/Member no workspace. Relatórios com rótulo de confidencialidade não exportam para PDF via Service Principal.
- **Graph (App-Only)**: permissões de aplicação `Mail.Send` (restrinja mailboxes com *Application Access Policy*) e, para Teams, `ChannelMessage.Send` / `Group.ReadWrite.All` conforme o tenant. Conceder **admin consent**.

---

## Onde achar cada ID

Abra o relatório no Power BI Service. A URL contém os IDs:

```
app.powerbi.com/groups/{WORKSPACE_ID}/reports/{REPORT_ID}/{PAGE_NAME}
```

- **Workspace ID** — após `/groups/`.
- **Report ID** — após `/reports/`.
- **Page Name** — último trecho (`ReportSection…`) ao navegar até a página; é o nome interno, não o título.
- **Dataset ID** — no workspace, `(…)` do modelo semântico → Configurações → na URL após `/datasets/`.
- **Teams Team ID** — Teams → `(…)` do time → "Obter link para a equipe" → valor de `groupId=`.
- **Teams Channel ID** — `(…)` do canal → "Obter link para o canal" → `19:…@thread.tacv2`.

O guia completo também está na página **Documentação** do painel.

---

## Testes e qualidade

```bash
pip install -r requirements-dev.txt
pytest            # testes unitários do backend (mockados, sem infra)
ruff check .      # lint
cd frontend && npm run build   # type-check (tsc) + build de produção
```

---

## Segurança

- Webhook protegido por segredo comparado em **tempo constante** (`hmac.compare_digest`). Em produção, prefira validar assinatura HMAC do corpo + IP allowlist.
- Tokens só em memória; nada de credenciais em log. Use Key Vault para o secret/certificado.
- Payloads validados por Pydantic; queries via ORM parametrizado (sem string SQL).
- Princípio do menor privilégio: SP restrito aos workspaces necessários; `Mail.Send` restrito por policy.

---

## Gargalos previstos e mitigação

- **Limite de 500 exports concorrentes por capacity** e 5 páginas processadas em paralelo → o fan-out usa `countdown` crescente para escalonar disparos; para volume alto, fila dedicada e rate limiting por capacity.
- **429 (rate limit)** → tratado em todas as chamadas, respeitando `Retry-After`; polling com backoff exponencial.
- **Worker preso no polling** → `worker_prefetch_multiplier=1`, `acks_late` e `task_time_limit`; separe a fila de export dos demais workers.
- **Cache de token por processo** → em frota grande, mover o `TokenCache` do MSAL para Redis evita N pedidos simultâneos ao Entra ID.
- **Anexo > 3 MB no Graph** → a regra permite enviar **link** em vez de anexo; acima do limite, usar upload session em rascunho.

---

_BI Notify v1.1 — FastAPI · Celery · Microsoft Graph · Power BI REST._
