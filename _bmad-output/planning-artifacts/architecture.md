---
stepsCompleted: [1, 2, 3, 4, 5, 6, 7, 8]
inputDocuments: ['product-brief.md', 'prd.md', 'ux-design-specification.md']
workflowType: 'architecture'
project_name: 'ReqStudio'
user_name: 'Glauber Costa'
date: '2026-03-28'
lastStep: 8
status: 'complete'
completedAt: '2026-03-29'
---

# Architecture Decision Document

_This document builds collaboratively through step-by-step discovery. Sections are appended as we work through each architectural decision together._

## Project Context Analysis

### Requirements Overview

**Functional Requirements:**
42 FRs organizados em 7 áreas de capacidade:
- **Contexto e Organização** (FR1-FR6): Projetos como containers isolados, resumo de progresso, zero vazamento
- **Enriquecimento de Contexto** (FR7-FR11): Import de docs (PDF, MD, planilhas), citação de fontes nos artefatos
- **Tradução Assistida** (FR12-FR19): Core — sessão multi-etapa com agentes IA, linguagem não-técnica, construção progressiva
- **Artefatos e Saída** (FR20-FR25): Saída dual (humano + máquina), export MD/JSON, cobertura por seção
- **Evolução Colaborativa** (FR26-FR31): Stakeholders, feedback, re-análise com IA, notificações — Growth
- **Brownfield** (FR32-FR37): Import de docs existentes, análise de codebase — Growth/Vision
- **Identidade e Acesso** (FR38-FR42): Auth, tenant isolation, RBAC — MVP parcial

Faseamento: FR1-FR25 + FR38-FR40 no MVP. FR26-FR35 + FR41-FR42 no Growth.

**Non-Functional Requirements:**
20 NFRs em 6 categorias com impacto arquitetural direto:
- **Performance:** IA ≤ 30s (NFR1), UI ≤ 2s (NFR2), export ≤ 5s (NFR3)
- **Segurança:** HTTPS, bcrypt, JWT 24h, zero vazamento entre tenants (NFR5-9)
- **Escalabilidade:** 10x sem reescrita, SQLite→PostgreSQL sem breaking (NFR10-12)
- **Disponibilidade:** 99.5%, modo degradado sem API, sessão preservada em desconexão (NFR13-15)
- **Acessibilidade:** Mobile-first, WCAG 2.1 AA, navegação por teclado (NFR16-18)
- **Integração:** Abstração de provedor de IA, export Notion/Jira-compatible (NFR19-20)

**Scale & Complexity:**
- Primary domain: Full-stack Web App (SPA + backend + IA)
- Complexity level: Média (MVP) — 3 camadas principais (frontend, backend, IA provider)
- Estimated architectural components: ~8 (Auth, Projects, Sessions, AI Engine, Artifact Pipeline, Document Import, Export, Notification)

### First Principles Decisions

Análise de primeiros princípios validada com PM (John) e Arquiteto (Winston):

| # | Premissa Desmontada | Decisão Tomada |
|---|---------------------|----------------|
| 1 | "BMAD é o motor de elicitação" | BMAD é **conteúdo/inspiração**, não runtime. MVP: workflows hardcoded (briefing, PRD, UX). V2: engine configurável que interpreta skills BMAD como configuração |
| 2 | "Sessão pausável = blob" | Sessão = **entidades persistidas separadamente** (workflow_position, messages[], artifact_state JSON, documents[]). Contexto do LLM **reconstruído on-demand** via Context Builder |
| 3 | "SQLite no MVP → PostgreSQL depois" | **PostgreSQL desde o MVP** (via Docker). Elimina migração, habilita RLS futuro, JSONB nativo. ADR: diverge do PRD por simplicidade operacional |
| 4 | "Backend leve" | **Monolito modular** — backend substancial com módulos: auth, projects, sessions, engine, documents, artifacts, shared. Deploy como unidade única |
| 5 | "Saída dual = gerar dois formatos" | **JSON é o formato canônico** do artefato. Markdown/PDF são views renderizadas. LLM gera JSON estruturado, pipeline de rendering transforma. Validação + retry para JSON inválido |
| 6 | "Isolamento por tenant_id" | Isolamento de IA é **tão crítico quanto DB**. Context Builder valida que 100% do contexto pertence ao `project_id` antes de cada chamada LLM. Teste automatizado de zero vazamento no CI |

### Technical Constraints & Dependencies

**Explícitas do PRD:**
- Frontend: SPA mobile-first (framework a decidir)
- Backend: API intermediária — frontend NUNCA acessa API de IA diretamente
- DB: PostgreSQL com isolamento lógico por `tenant_id` (decisão arquitetural — diverge de SQLite no PRD)
- Auth: Email+senha (MVP), OAuth Google (Growth)
- IA: Anthropic Claude (Sonnet) como provedor primário, abstração multi-provedor mandatória (NFR19)

**Implícitas da UX Spec:**
- Streaming de respostas da IA (typing indicator, artefato crescendo em real-time)
- Split view desktop com proporção fixa 40/60 (MVP)
- shadcn/ui + Tailwind como design system
- Auto-save com indicador visual (SaveIndicator)
- Responsive: 320px → 1280px+

### Cross-Cutting Concerns Identified

1. **Elicitation Engine** — Orchestrator de sessões com workflows hardcoded (MVP). Componente mais complexo do sistema. Carrega definição de workflow → gerencia estado → constrói prompt → chama LLM → parseia resposta → persiste resultado
2. **Context Builder** — Monta prompt do LLM a partir de entidades persistidas. Gerencia limite de tokens, priorização (docs > histórico recente > mensagens antigas), validação de isolamento por project_id
3. **Abstração de IA** — Isolar lógica de negócio do provedor LLM. Interface uniforme para streaming, structured output, token counting
4. **Artifact Pipeline** — JSON canônico → rendering para Markdown/PDF/prompts. Cálculo de cobertura. Versionamento
5. **Isolamento de dados** — Três camadas: aplicação (tenant_id filter), banco (RLS futuro), IA (validação de contexto)
6. **Custos de IA** — Monitoramento de tokens em tempo real, alertas de threshold per-session
7. **Importação de documentos** — PDF parsing, extração de texto, chunking para contexto de IA

### ADR: MetaCognition como Engine de Orquestração (V2+)

**Contexto:** O projeto MetaCognition v0.3, de propriedade do mesmo time, é uma plataforma de orquestração de agentes e fluxos com API FastAPI, suportando múltiplos engines (LangChain, CrewAI) e CRUD completo de agentes e flows como DAGs.

**Análise realizada:** Mapeamento das APIs do MetaCognition contra as necessidades do ReqStudio revelou que o motor de orquestração (`POST /orchestrate/run`) resolve o Elicitation Engine, mas faltam: streaming, sessões persistentes, tenant isolation e structured output.

**Decisão:** MVP do ReqStudio é **standalone** com Elicitation Engine próprio (workflows hardcoded). Após validação do produto com usuários reais, avaliar integração com MetaCognition como backend de orquestração, onde:
- MetaCognition fornece: Agents, Flows, Orchestration, multi-provider LLM
- ReqStudio fornece: Projects, Sessions, Auth, Documents, Artifacts, UX

**Rationale:** Validar o problema (Ana quer usar o ReqStudio?) antes de otimizar a arquitetura (como integrar dois produtos).

**Status:** Diferido para pós-MVP. Modelo de dados do MVP deve ser **compatível** com migração futura (ex: agentes e workflows como entidades, não hardcoded em código).

## Starter Template Evaluation

### Primary Technology Domain

Full-stack: Python Backend (FastAPI) + React Frontend (Vite). Duas aplicações separadas comunicando via REST API, deploy unificado via Docker Compose.

### Starter Options Considered

| Opção | Tipo | Veredicto |
|-------|------|----------|
| FastAPI manual (padrão Netflix Dispatch) | Backend | ✅ Selecionado — setup manual modular por domínio |
| Vite + React TS + shadcn/ui | Frontend | ✅ Selecionado — starter oficial via CLI |
| Full-stack generators (T3, etc.) | Monorepo | ❌ Descartado — incompatível com Python backend |

### Selected Stack

**Backend: Python 3.11+ / FastAPI**
- FastAPI + Pydantic v2 (schemas + validação)
- SQLAlchemy 2.0 + Alembic (ORM + migrations)
- LiteLLM (multi-provider LLM, streaming, cost tracking)
- JWT (python-jose + passlib) para auth
- Pytest + Ruff (testes + linting)
- Async/await para I/O

**Frontend: Vite + React + TypeScript + shadcn/ui**
- React 18+ com TypeScript
- Vite (build, HMR, dev server)
- Tailwind CSS + CSS Variables (design tokens)
- shadcn/ui (componentes Radix UI)
- React Router (navegação)
- React Context (estado MVP) → Zustand (V2)
- Vitest + ESLint (testes + linting)

**Infraestrutura:**
- PostgreSQL 16 (Docker)
- Docker Compose (api + db + frontend)

### Initialization Commands

```bash
# Frontend
npm create vite@latest reqstudio-ui -- --template react-ts
cd reqstudio-ui && npx shadcn@latest init

# Backend
mkdir reqstudio-api && cd reqstudio-api
pip install fastapi uvicorn sqlalchemy alembic litellm pydantic python-jose passlib
```

**Nota:** Inicialização do projeto deve ser a primeira story de implementação.

### Rationale: LiteLLM vs LangChain

**Decisão:** LiteLLM para o MVP. LangChain fica no MetaCognition (V2+).

**Motivo:** O ReqStudio não precisa de chains/agents/RAG — o Elicitation Engine faz sua própria orquestração de estado. Precisa apenas de: chamar LLM, streaming, multi-provider, cost tracking. LiteLLM resolve isso com menos código.

| Critério | LiteLLM | LangChain |
|----------|---------|----------|
| Foco | API gateway + normalização | Framework de aplicação |
| Multi-provider | 100+ providers nativos | Sim, mais verbose |
| Streaming | ✅ Nativo | ✅ Nativo |
| Fallback automático | ✅ Built-in | ❌ Manual |
| Cost tracking | ✅ Built-in | ❌ Precisa plugin |
| Curva de aprendizado | Baixa | Alta |

Na integração futura com MetaCognition, ambos coexistem: MetaCognition = LangChain (DAGs), ReqStudio = LiteLLM (chamadas diretas).

### Projeto Estrutural do Backend

```
reqstudio-api/
├── alembic/                    # Database migrations
├── app/
│   ├── core/                   # Config, security, middleware, tenant isolation
│   ├── modules/
│   │   ├── auth/               # router, schemas, models, service
│   │   ├── projects/           # CRUD projetos, tenant isolation
│   │   ├── sessions/           # Estado de workflow, mensagens
│   │   ├── engine/             # Elicitation Engine (workflows hardcoded MVP)
│   │   ├── documents/          # Import, parsing, chunking
│   │   └── artifacts/          # JSON canônico, rendering, export
│   ├── integrations/           # LiteLLM provider abstraction
│   ├── db/                     # Base DB, session management
│   └── main.py                 # FastAPI factory
├── tests/
├── Dockerfile
├── requirements.txt
└── .env
```

### Modelo de Dados Compatível com Migração Futura

Mesmo com workflows hardcoded no MVP, o schema inclui:
- `Workflow` (id, name, steps_json) — seed data, não editável na UI
- `WorkflowStep` (id, workflow_id, position, prompt_template) — seed data
- `Agent` (id, name, role, prompt) — seed data BMAD

Isso permite que na V2 essas tabelas se tornem editáveis pela UI (ou pelo MetaCognition) sem migração de schema.

## Core Architectural Decisions

### Decision Priority Analysis

**Critical Decisions (Block Implementation):**
- Data modeling approach (Declarative SQLAlchemy + JSONB para artefatos)
- JWT auth strategy (access + refresh token rotation)
- Streaming approach (SSE para respostas da IA)
- Error handling pattern (guided recovery)
- Tenant isolation (TenantMixin + middleware)

**Important Decisions (Shape Architecture):**
- Port management (auto-detect via helper script)
- Frontend state management (React Context + TanStack Query)
- Observability stack (OpenTelemetry + SigNoz)

**Deferred Decisions (Post-MVP):**
- Redis caching (só se performance exigir)
- CI/CD pipeline (manual Docker Compose por enquanto)
- WebSocket (SSE cobre MVP; WebSocket se V2 precisar bidirecional)

### Data Architecture

| Decisão | Escolha | Rationale |
|---------|---------|----------|
| ORM Style | **Declarative mapping** (SQLAlchemy 2.0) | Padrão do ecossistema, consistente com MetaCognition |
| Artefatos | **JSONB column** para `artifact_state` + tabelas relacionais para metadados | Flexibilidade do JSON para conteúdo em construção, tipagem forte para queries |
| Cache | **Sem Redis no MVP** — cache de prompt templates em memória | PostgreSQL handles tudo no MVP; Redis se bottleneck aparecer |
| Migrations | **Alembic** | Já decidido no Step 3 |

### Authentication & Security

| Decisão | Escolha | Rationale |
|---------|---------|----------|
| Access Token | **JWT, 15min TTL**, armazenado em memória (frontend) | Short-lived reduz risco de token comprometido |
| Refresh Token | **7 dias TTL**, httpOnly cookie, rotation obrigatória | Seguro contra XSS, descartado após uso |
| Password | **bcrypt** via passlib | NFR6 do PRD |
| Tenant Isolation | **TenantMixin** no SQLAlchemy + middleware que injeta `tenant_id` do JWT | Zero possibilidade de query sem filtro de tenant |
| CORS | Origens configuráveis via `.env` (`ALLOWED_ORIGINS`) | Restrito em produção |
| Rate Limiting | **slowapi** por IP | Protege API de IA contra abuso |

### API & Communication Patterns

| Decisão | Escolha | Rationale |
|---------|---------|----------|
| API Style | **REST** com versionamento URL (`/api/v1/`) | Padrão, auto-documentado via OpenAPI/Swagger |
| Streaming | **SSE** (`StreamingResponse` FastAPI) | Unidirecional server→client, perfeito para typing indicator. WebSocket diferido (refatoração ~2-3 arquivos se necessário V2) |
| Request ID | **UUID via middleware**, header `X-Request-ID` | Rastreabilidade em logs, consistente com MetaCognition |
| Error Handling | **Guided Recovery Pattern** (ver detalhes abaixo) | Erros proativos e colaborativos, ajudam o user a resolver sozinho |

#### Guided Recovery Error Pattern

Todo erro retorna um payload estruturado que o frontend renderiza como ErrorBanner com ações:

```json
{
  "error": {
    "code": "SESSION_EXPIRED",
    "message": "Sua sessão de trabalho expirou por inatividade.",
    "help": "Sessões são preservadas automaticamente. Volte à lista de projetos para retomar de onde parou.",
    "actions": [
      { "label": "Voltar aos projetos", "route": "/projects" },
      { "label": "Tentar novamente", "action": "retry" }
    ],
    "severity": "recoverable"
  }
}
```

| Campo | Descrição |
|-------|-----------|
| `code` | Identificador técnico (logs/debug) |
| `message` | Linguagem humana, não-técnica |
| `help` | Explicação de por quê + o que fazer |
| `actions` | Ações concretas renderizadas como botões |
| `severity` | `recoverable` \| `blocking` \| `info` |

Catálogo de erros mantido como enum no backend. Cada erro tem guided recovery documentado.

### Frontend Architecture

| Decisão | Escolha | Rationale |
|---------|---------|----------|
| State (global) | **React Context** para auth, tenant, theme | Simples, sem lib extra |
| State (server) | **TanStack Query** para cache de API, invalidação, retry | Padrão de mercado para server state |
| Components | Organização por domínio: `ui/`, `chat/`, `artifacts/`, `layout/`, `shared/` | Alinhado com UX Spec |
| API Client | **fetch nativo** + wrapper tipado | Menos dependências, TanStack Query gerencia retry/cache |
| Routing | **React Router v6** com lazy loading | Padrão, code splitting por página |

### Infrastructure & Deployment

| Decisão | Escolha | Rationale |
|---------|---------|----------|
| Deploy MVP | **Docker Compose** (api + db + frontend) | Decidido Step 3 |
| Port Management | **Portas via `.env`** + script `find-ports` auto-detect | Resolve conflitos com outros projetos rodando localmente |
| Environment | `.env.development`, `.env.production` + Pydantic `BaseSettings` | Validação na startup, fail fast se variável ausente |
| Logging | **Structured JSON** (structlog ou logging nativo) | Consistente com MetaCognition |
| Observability | **OpenTelemetry SDK** instrumentado desde MVP + **SigNoz** como container opcional | Código nasce instrumentado; SigNoz já adotado pela empresa |
| CI/CD | **Diferido** para pós-MVP | Manual Docker Compose por enquanto |
| Health Check | **`/health` endpoint** | Mínimo viável para monitoramento |

#### Docker Compose Structure

```yaml
services:
  api:
    build: ./reqstudio-api
    ports:
      - "${API_PORT:-8000}:8000"
    depends_on:
      - db
    env_file: .env
  db:
    image: postgres:16
    ports:
      - "${DB_PORT:-5432}:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
  frontend:
    build: ./reqstudio-ui
    ports:
      - "${FRONTEND_PORT:-5173}:5173"
  # Optional: uncomment for observability
  # signoz:
  #   image: signoz/signoz:latest
  #   ports:
  #     - "${SIGNOZ_PORT:-3301}:3301"
```

### Decision Impact Analysis

**Implementation Sequence:**
1. Docker Compose + PostgreSQL + FastAPI skeleton (infra foundation)
2. Auth module (JWT, bcrypt, TenantMixin)
3. Projects module (CRUD, tenant isolation)
4. Sessions + Engine module (Elicitation Engine, SSE streaming)
5. Documents module (import, parsing)
6. Artifacts module (JSON canônico, rendering, export)
7. Frontend (React, shadcn, TanStack Query, SSE client)

**Cross-Component Dependencies:**
- TenantMixin → usado por todos os modules
- Guided Recovery errors → usado por todos os routers
- LiteLLM → usado apenas pelo Engine module
- SSE → implementado no Engine, consumido pelo Frontend
- OpenTelemetry → instrumentado em todos os modules

## Implementation Patterns & Consistency Rules

### BMAD Compatibility Analysis

Analisado o workflow do dev agent BMAD (Amelia): **zero conflitos** com nossas regras. O BMAD dev agent é subordinado ao `project-context.md` e à arquitetura — nossas regras são a fonte de verdade. O agente já implementa TDD nativo (red-green-refactor). Frameworks externos operam via API, não leem nossas rules.

### Naming Patterns

**Database (PostgreSQL):**
| Elemento | Padrão | Exemplo |
|----------|--------|--------|
| Tabelas | `snake_case`, **plural** | `projects`, `sessions`, `workflow_steps` |
| Colunas | `snake_case` | `created_at`, `tenant_id`, `artifact_state` |
| Foreign keys | `{tabela_singular}_id` | `project_id`, `session_id` |
| Índices | `ix_{tabela}_{coluna}` | `ix_sessions_project_id` |

**API (FastAPI):**
| Elemento | Padrão | Exemplo |
|----------|--------|--------|
| Endpoints | `snake_case`, **plural**, versionados | `/api/v1/projects`, `/api/v1/sessions` |
| Path params | `{resource_id}` | `/api/v1/projects/{project_id}` |
| Query params | `snake_case` | `?page_size=10&sort_by=created_at` |
| JSON response | `snake_case` ponta a ponta | `{ "project_id": "...", "created_at": "..." }` |

**Backend Python:**
| Elemento | Padrão | Exemplo |
|----------|--------|--------|
| Módulos/packages | `snake_case` | `app/modules/sessions/` |
| Classes | `PascalCase` | `SessionCreate`, `TenantMixin` |
| Funções/variáveis | `snake_case` | `get_active_sessions()`, `tenant_id` |
| Constants | `UPPER_SNAKE` | `MAX_TOKEN_LIMIT`, `JWT_EXPIRY_MINUTES` |

**Frontend TypeScript/React:**
| Elemento | Padrão | Exemplo |
|----------|--------|--------|
| Components | `PascalCase.tsx` | `ChatBubble.tsx`, `ArtifactCard.tsx` |
| Hooks | `camelCase.ts`, prefixo `use` | `useSession.ts`, `useArtifact.ts` |
| Services | `camelCase.ts` | `apiClient.ts`, `sseClient.ts` |
| Types/Interfaces | `PascalCase` | `Session`, `ArtifactState` |
| CSS classes | shadcn/Tailwind (`cn()` helper) | `cn("flex gap-2", isActive && "bg-primary")` |

**Fronteira API:** `snake_case` ponta a ponta (Python → JSON → TypeScript). Sem conversão snake↔camel.

### Structure Patterns

**Backend — testes co-localizados por módulo:**
```
app/modules/projects/
├── router.py
├── schemas.py
├── models.py
├── service.py
└── tests/
    ├── test_router.py
    └── test_service.py
```

**Frontend — por domínio:**
```
src/
├── components/
│   ├── ui/          # shadcn primitives (gerados)
│   ├── chat/        # ChatBubble, ChatInput, TypingIndicator
│   ├── artifacts/   # ArtifactCard, CoverageBar, ArtifactViewer
│   ├── layout/      # Header, TabBar, SplitView
│   └── shared/      # SaveIndicator, ErrorBanner, LoadingSpinner
├── pages/           # LoginPage, ProjectsPage, SessionPage
├── hooks/           # useAuth, useSession, useArtifact, useSSE
├── services/        # apiClient, sseClient
├── contexts/        # AuthContext, TenantContext
├── types/           # interfaces TypeScript
└── lib/             # utils, constants
```

### Format Patterns

**API Success Response:**
```json
{ "data": { "id": "...", "name": "...", "created_at": "2026-03-29T10:00:00Z" } }
```

**API Error Response (Guided Recovery):**
```json
{
  "error": {
    "code": "SESSION_EXPIRED",
    "message": "Sua sessão de trabalho expirou por inatividade.",
    "help": "Sessões são preservadas automaticamente. Volte à lista de projetos para retomar de onde parou.",
    "actions": [
      { "label": "Voltar aos projetos", "route": "/projects" },
      { "label": "Tentar novamente", "action": "retry" }
    ],
    "severity": "recoverable"
  }
}
```

**Datas:** ISO 8601 UTC sempre (`2026-03-29T13:00:00Z`). Frontend converte para timezone local na exibição.

**Nulls:** `null` explícito em JSON, nunca omitir campo. Pydantic schema define quais campos são `Optional`.

### Process Patterns

**Loading states:** Variável nomeada `isLoading{Action}`: `isLoadingSession`, `isSubmitting`. TanStack Query gerencia automático (`isLoading`, `isFetching`).

**Authentication flow:**
1. Login → recebe access + refresh token
2. Access token em memória (React Context)
3. Refresh token em httpOnly cookie (`SameSite=Strict`, `Secure=True`)
4. API client intercepta 401 → tenta refresh → retry original request
5. Refresh falha → redirect para login
6. Refresh token rotation: cada uso invalida o token anterior
7. Refresh token reuse detection: se token já usado for apresentado → revogar TODOS os tokens do user → forçar re-login

**Validation:**
- Backend: Pydantic valida toda entrada (schemas obrigatórios em todo router)
- Frontend: Validação local antes de submit (feedback imediato)
- Nunca confiar em validação frontend — backend é source of truth

**Upload Security:**
- `MAX_UPLOAD_SIZE = 20MB` (configurável via env)
- Validar MIME type real do arquivo (não confiar na extensão)
- Parsers processam em chunks — nunca carregar arquivo inteiro em memória
- Guided Recovery para uploads excedentes: "O arquivo excede o limite de 20MB. Tente dividir o documento ou remover imagens."

### Resilience Patterns (Chaos Monkey validated)

**SSE auto-reconnect:**
- `sseClient.ts` → reconnect com backoff exponencial ao detectar `EventSource.onerror`
- Frontend ao reconectar → `GET /sessions/{id}/messages` → reconcilia com última mensagem completa
- `message_id` único garante idempotência — frontend ignora duplicados
- Flag `isReconnecting` exibe banner: "Reconectando..."

**LLM unavailability:**
- `llm_client.py` → timeout máximo configurável (default: 60s)
- Após exaustão de fallbacks LiteLLM → `LLMUnavailableError`
- SSE envia chunk de erro: `event: error\ndata: {"code": "LLM_UNAVAILABLE"}`
- Frontend: após 30s sem chunk, exibe: "A resposta está demorando. Aguarde ou tente novamente."

**Write-ahead save:**
- Mensagem do user salva no banco ANTES de enviar ao LLM
- Se crash, user pode re-enviar; se LLM respondeu e DB voltou, retry de save da resposta
- Backend salva resposta COMPLETA no banco quando stream finaliza (independente do client estar conectado)

**DB connection failure:**
- `error_handlers.py` → DB errors retornam Guided Recovery: "Instabilidade temporária. Sua sessão está segura. Tente novamente em alguns segundos."
- Connection pool com health check e auto-reconnect (SQLAlchemy pool_pre_ping=True)

### TDD Rules

**Obrigatório em todo o projeto.** Compatível com ciclo red-green-refactor do BMAD dev agent (Amelia).

| Aspecto | Regra |
|---------|------|
| Ciclo | **Red → Green → Refactor** — testes escritos ANTES da implementação |
| Backend | Pytest com async support (`pytest-asyncio`) |
| Frontend | Vitest + React Testing Library |
| Coverage threshold | **≥ 80%** por módulo |
| Unit tests | Obrigatórios para toda service e business logic |
| Integration tests | Obrigatórios para endpoints de API (TestClient FastAPI) |
| E2E tests | Para fluxos críticos: sessão de elicitação, export de artefato |
| Regression | Full test suite executado ANTES de marcar task complete |
| Naming | `test_{modulo}_test_{funcionalidade}.py` (back), `{Component}.test.tsx` (front) |
| Multi-tenant isolation | **Obrigatório**: fixture padrão com 2 tenants em `conftest.py`. Todo model/query testado com isolamento — dados do tenant B nunca visíveis para tenant A |

**Regra de ouro:** Nenhum código novo sem teste correspondente. Nenhum teste sem estar passando.

### Enforcement Guidelines

**Todo agente IA que implementar código DEVE:**
1. Seguir naming conventions definidas acima (snake_case backend, PascalCase components)
2. Usar Guided Recovery para QUALQUER erro que o usuário possa ver
3. Incluir `tenant_id` filter em TODA query de banco (via TenantMixin)
4. Retornar respostas no wrapper `{ "data": ... }` ou `{ "error": ... }`
5. Usar ISO 8601 UTC para todas as datas
6. Escrever testes no diretório `tests/` do módulo correspondente
7. Usar type hints em todo código Python e TypeScript interfaces no frontend
8. Seguir ciclo TDD red-green-refactor para todo código novo
9. Manter coverage ≥ 80% no módulo modificado

**Anti-patterns (NUNCA fazer):**
- ❌ Query sem filtro de `tenant_id`
- ❌ Endpoint sem schema Pydantic de entrada/saída
- ❌ Erro genérico sem `help` e `actions`
- ❌ Datas em formato não-ISO
- ❌ Código sem testes
- ❌ Testes que não rodam (broken tests)
- ❌ Misturar camelCase e snake_case no mesmo layer
- ❌ Upload sem validação de tamanho e MIME type
- ❌ Novo model sem teste de isolamento multi-tenant
- ❌ SSE endpoint sem tratamento de desconexão/reconnect

## Project Structure & Boundaries

### Requirements to Components Mapping

| Área FR (PRD) | Módulo Backend | Componente Frontend |
|--------------|---------------|-------------------|
| FR1-FR6 Contexto e Organização | `modules/projects/` | `pages/ProjectsPage`, `components/layout/` |
| FR7-FR11 Enriquecimento de Contexto | `modules/documents/` | `components/shared/DocumentUpload` |
| FR12-FR19 Tradução Assistida (Core) | `modules/engine/` + `modules/sessions/` | `pages/SessionPage`, `components/chat/` |
| FR20-FR25 Artefatos e Saída | `modules/artifacts/` | `components/artifacts/`, `pages/ArtifactExportPage` |
| FR38-FR40 Identidade e Acesso | `modules/auth/` | `pages/LoginPage`, `contexts/AuthContext` |

### Complete Project Directory Structure

```
reqstudio/
├── docker-compose.yml
├── docker-compose.dev.yml
├── .env.example
├── .env
├── .gitignore
├── README.md
├── scripts/
│   ├── find-ports.sh              # Auto-detect portas livres
│   └── find-ports.ps1             # Versão Windows
│
├── reqstudio-api/                  # ═══ BACKEND (Python/FastAPI) ═══
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── pyproject.toml
│   ├── .env.example
│   ├── alembic.ini
│   ├── alembic/
│   │   ├── env.py
│   │   ├── script.py.mako
│   │   └── versions/
│   │
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                # FastAPI factory, middleware, CORS
│   │   │
│   │   ├── core/                  # Cross-cutting
│   │   │   ├── __init__.py
│   │   │   ├── config.py          # Pydantic BaseSettings
│   │   │   ├── security.py        # JWT encode/decode, password hashing
│   │   │   ├── middleware.py       # TenantMiddleware, RequestIdMiddleware
│   │   │   ├── dependencies.py    # get_db, get_current_user, get_tenant_id
│   │   │   ├── exceptions.py      # GuidedRecoveryError, error catalog
│   │   │   ├── error_handlers.py  # Global exception handlers
│   │   │   └── telemetry.py       # OpenTelemetry setup
│   │   │
│   │   ├── db/                    # Database layer
│   │   │   ├── __init__.py
│   │   │   ├── base.py            # DeclarativeBase, TenantMixin
│   │   │   ├── session.py         # AsyncSession factory
│   │   │   └── seed.py            # Seed data (workflows, agents BMAD)
│   │   │
│   │   ├── modules/               # Domain modules
│   │   │   ├── auth/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── router.py      # POST /login, /register, /refresh
│   │   │   │   ├── schemas.py     # LoginRequest, TokenResponse, UserCreate
│   │   │   │   ├── models.py      # User
│   │   │   │   ├── service.py     # authenticate, create_user, refresh_token
│   │   │   │   └── tests/
│   │   │   │       ├── test_router.py
│   │   │   │       └── test_service.py
│   │   │   │
│   │   │   ├── projects/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── router.py      # CRUD /api/v1/projects
│   │   │   │   ├── schemas.py     # ProjectCreate, ProjectResponse
│   │   │   │   ├── models.py      # Project (TenantMixin)
│   │   │   │   ├── service.py     # create, list, get, update, delete
│   │   │   │   └── tests/
│   │   │   │       ├── test_router.py
│   │   │   │       └── test_service.py
│   │   │   │
│   │   │   ├── sessions/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── router.py      # CRUD + SSE /api/v1/sessions
│   │   │   │   ├── schemas.py     # SessionCreate, MessageCreate, SessionState
│   │   │   │   ├── models.py      # Session, Message (TenantMixin)
│   │   │   │   ├── service.py     # create, send_message, get_history
│   │   │   │   └── tests/
│   │   │   │       ├── test_router.py
│   │   │   │       └── test_service.py
│   │   │   │
│   │   │   ├── engine/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── router.py      # POST /api/v1/engine/elicit (SSE)
│   │   │   │   ├── schemas.py     # ElicitRequest, ElicitChunk
│   │   │   │   ├── models.py      # Workflow, WorkflowStep, Agent (seed)
│   │   │   │   ├── service.py     # Elicitation Engine (orquestração)
│   │   │   │   ├── context_builder.py  # Monta prompt com isolamento
│   │   │   │   ├── workflows/     # Definições hardcoded MVP
│   │   │   │   │   ├── briefing.py
│   │   │   │   │   ├── prd.py
│   │   │   │   │   └── ux.py
│   │   │   │   └── tests/
│   │   │   │       ├── test_service.py
│   │   │   │       ├── test_context_builder.py
│   │   │   │       └── test_workflows.py
│   │   │   │
│   │   │   ├── documents/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── router.py      # POST /api/v1/documents/upload
│   │   │   │   ├── schemas.py     # DocumentUpload, DocumentResponse
│   │   │   │   ├── models.py      # Document, DocumentChunk (TenantMixin)
│   │   │   │   ├── service.py     # upload, parse, chunk
│   │   │   │   ├── parsers/
│   │   │   │   │   ├── pdf_parser.py
│   │   │   │   │   ├── markdown_parser.py
│   │   │   │   │   └── spreadsheet_parser.py
│   │   │   │   └── tests/
│   │   │   │       ├── test_router.py
│   │   │   │       └── test_parsers.py
│   │   │   │
│   │   │   └── artifacts/
│   │   │       ├── __init__.py
│   │   │       ├── router.py      # CRUD + export /api/v1/artifacts
│   │   │       ├── schemas.py     # ArtifactCreate, ArtifactExport
│   │   │       ├── models.py      # Artifact (JSONB state, TenantMixin)
│   │   │       ├── service.py     # create, update_state, get_coverage
│   │   │       ├── renderers/
│   │   │       │   ├── markdown_renderer.py
│   │   │       │   └── pdf_renderer.py
│   │   │       └── tests/
│   │   │           ├── test_router.py
│   │   │           ├── test_service.py
│   │   │           └── test_renderers.py
│   │   │
│   │   └── integrations/          # External providers
│   │       ├── __init__.py
│   │       ├── llm_client.py      # LiteLLM wrapper (multi-provider)
│   │       └── tests/
│   │           └── test_llm_client.py
│   │
│   └── tests/                     # Integration/E2E tests
│       ├── conftest.py            # Fixtures globais, TestDB
│       ├── integration/
│       │   ├── test_auth_flow.py
│       │   └── test_elicitation_flow.py
│       └── e2e/
│           └── test_full_session.py
│
└── reqstudio-ui/                   # ═══ FRONTEND (React/Vite) ═══
    ├── Dockerfile
    ├── package.json
    ├── vite.config.ts
    ├── tsconfig.json
    ├── tailwind.config.js
    ├── components.json            # shadcn config
    ├── index.html
    │
    ├── src/
    │   ├── main.tsx               # Entry point
    │   ├── App.tsx                # Router setup
    │   ├── index.css              # Tailwind directives + tokens
    │   │
    │   ├── components/
    │   │   ├── ui/                # shadcn/ui (auto-gerados)
    │   │   ├── chat/
    │   │   │   ├── ChatBubble.tsx
    │   │   │   ├── ChatInput.tsx
    │   │   │   ├── TypingIndicator.tsx
    │   │   │   └── MessageList.tsx
    │   │   ├── artifacts/
    │   │   │   ├── ArtifactCard.tsx
    │   │   │   ├── ArtifactViewer.tsx
    │   │   │   ├── CoverageBar.tsx
    │   │   │   └── SectionEditor.tsx
    │   │   ├── layout/
    │   │   │   ├── Header.tsx
    │   │   │   ├── TabBar.tsx
    │   │   │   ├── SplitView.tsx
    │   │   │   └── MobileNav.tsx
    │   │   └── shared/
    │   │       ├── SaveIndicator.tsx
    │   │       ├── ErrorBanner.tsx
    │   │       ├── LoadingSpinner.tsx
    │   │       └── DocumentUpload.tsx
    │   │
    │   ├── pages/
    │   │   ├── LoginPage.tsx
    │   │   ├── ProjectsPage.tsx
    │   │   ├── ProjectDetailPage.tsx
    │   │   ├── SessionPage.tsx    # Core — split chat + artifact
    │   │   └── ArtifactExportPage.tsx
    │   │
    │   ├── hooks/
    │   │   ├── useAuth.ts
    │   │   ├── useSession.ts
    │   │   ├── useArtifact.ts
    │   │   ├── useSSE.ts          # Server-Sent Events client
    │   │   └── useProjects.ts
    │   │
    │   ├── services/
    │   │   ├── apiClient.ts       # fetch wrapper tipado
    │   │   └── sseClient.ts       # EventSource wrapper
    │   │
    │   ├── contexts/
    │   │   ├── AuthContext.tsx
    │   │   └── TenantContext.tsx
    │   │
    │   ├── types/
    │   │   ├── api.ts             # Request/Response types
    │   │   ├── session.ts
    │   │   ├── artifact.ts
    │   │   └── project.ts
    │   │
    │   └── lib/
    │       ├── utils.ts           # cn(), formatDate(), etc.
    │       └── constants.ts       # API_BASE_URL, ROUTES
    │
    └── tests/
        ├── setup.ts               # Vitest setup
        ├── components/
        │   ├── ChatBubble.test.tsx
        │   └── ArtifactCard.test.tsx
        └── hooks/
            ├── useAuth.test.ts
            └── useSSE.test.ts
```

### Architectural Boundaries

**API Boundaries:**
```
Frontend ──HTTP/SSE──→ /api/v1/* ──→ Router ──→ Service ──→ DB
                                                  │
                                          LiteLLM (LLM provider)
```
- Frontend nunca acessa LLM diretamente
- Todo acesso ao DB passa pelo Service layer (nunca direto no Router)
- TenantMiddleware intercepta antes de qualquer Router

**Component Boundaries (Frontend):**
- `pages/` → orquestra hooks + components, nunca lógica de negócio
- `hooks/` → toda comunicação com API, gerenciamento de estado
- `components/` → renderização pura, recebe props
- `services/` → HTTP/SSE transport layer, sem lógica de negócio

**Data Boundaries:**
- `TenantMixin` → todo model com `tenant_id`, filtro automático
- `context_builder.py` → valida 100% do contexto pertence ao `project_id` antes de enviar ao LLM
- `JSONB` → `artifact_state` evolui livremente; metadados em colunas tipadas

### Data Flow — Fluxo de Elicitação (Core)

```
1. User digita mensagem → ChatInput → useSession.sendMessage()
2. POST /api/v1/sessions/{id}/messages → sessions/router
3. sessions/service → engine/service.elicit()
4. engine/context_builder → monta prompt (mensagens + artefato + docs)
5. engine/service → integrations/llm_client (LiteLLM) → SSE stream
6. SSE chunks → sessions/router → EventSource → useSSE → ChatBubble
7. Resposta final → engine/service atualiza artifact_state → DB
8. Frontend refresh → useArtifact → ArtifactViewer atualizado
```

### Integration Points

**Internal Communication:**
- Frontend ↔ Backend: REST API (JSON) + SSE (streaming)
- Engine ↔ LLM: LiteLLM SDK (HTTP para providers externos)
- Modules ↔ DB: SQLAlchemy async sessions

**External Integrations:**
- LLM Providers: Anthropic Claude, OpenAI, Google Gemini, Ollama (via LiteLLM)
- Observability: OpenTelemetry → SigNoz (opcional)

**Docker Compose Services:**
- `api` (FastAPI) ↔ `db` (PostgreSQL): rede interna Docker
- `frontend` (Nginx/Vite) → `api`: proxy reverso em produção

## Architecture Validation Results

### Coherence Validation ✅

**Decision Compatibility:**
- FastAPI (async) + SQLAlchemy 2.0 (async) + PostgreSQL = cadeia async completa
- LiteLLM + SSE + FastAPI StreamingResponse = pipeline de streaming coerente
- Pydantic v2 como validação em schemas E config (BaseSettings) = consistente
- shadcn/ui + Tailwind + Vite = stack frontend bem integrada

**Pattern Consistency:**
- `snake_case` ponta a ponta (DB → API → JSON → Frontend) elimina conversões
- TDD obrigatório + BMAD dev agent cycle = alinhados
- TenantMixin + middleware + context_builder = 3 camadas de isolamento coerentes

**Structure Alignment:**
- Módulos por domínio (auth, projects, sessions, engine, documents, artifacts) mapeiam 1:1 com áreas FR do PRD
- Testes co-localizados suportam TDD por módulo

### Requirements Coverage ✅

**FR Coverage (MVP):**

| FR | Suporte Arquitetural | Status |
|----|---------------------|--------|
| FR1-FR6 (Contexto/Organização) | `modules/projects/` + TenantMixin + `seed.py` | ✅ |
| FR7-FR11 (Enriquecimento) | `modules/documents/` + `parsers/` + `context_builder.py` | ✅ |
| FR12-FR19 (Tradução Assistida) | `modules/engine/` + `modules/sessions/` + `workflows/` + SSE | ✅ |
| FR20-FR25 (Artefatos/Saída) | `modules/artifacts/` + JSONB + `renderers/` + CoverageBar | ✅ |
| FR38-FR40 (Identidade/Acesso) | `modules/auth/` + JWT + TenantMixin + middleware | ✅ |

FR26-FR42 (Growth/Vision): diferidos por design. Estrutura modular permite adição sem refatoração.

**NFR Coverage:**

| NFR | Suporte | Status |
|-----|---------|--------|
| NFR1 (IA ≤30s) | SSE streaming + LiteLLM timeout config | ✅ |
| NFR2 (UI ≤2s) | Vite HMR + lazy loading + code splitting | ✅ |
| NFR5-6 (HTTPS, bcrypt) | `core/security.py` + passlib | ✅ |
| NFR7 (JWT) | 15min access + 7d refresh (mais seguro que PRD 24h) | ✅ |
| NFR8 (zero vazamento) | TenantMixin + middleware + context_builder + test fixture | ✅ |
| NFR10-11 (10x escala) | PostgreSQL MVP + modular monolith | ✅ |
| NFR12 (custo IA) | LiteLLM cost tracking + OpenTelemetry | ✅ |
| NFR14 (modo degradado) | Resilience Patterns (Chaos Monkey validated) | ✅ |
| NFR16 (mobile-first) | Tailwind responsive + UX Spec mobile patterns | ✅ |
| NFR19 (abstração provider) | LiteLLM = 100+ providers | ✅ |

### Gap Analysis ✅

Todos os gaps críticos foram resolvidos durante a validação:

| Gap Identificado | Severidade | Resolução |
|-----------------|-----------|----------|
| NFR14 modo degradado sem LLM | Alta | Resilience Patterns: LLM unavailability + SSE error events |
| SSE disconnect mid-stream | Média | Auto-reconnect + reconciliação de mensagens |
| Upload malicioso/oversized | Média | Upload Security: MAX_UPLOAD_SIZE + MIME validation |
| TenantMixin bypass risk | Crítica | Test fixture obrigatório com 2 tenants |
| JWT refresh token reuse | Baixa | Refresh reuse detection + revogação total |
| DB crash mid-session | Alta | Write-ahead save + pool_pre_ping + Guided Recovery |

### Architecture Completeness Checklist

**✅ Requirements Analysis**
- [x] Project context analisado (Steps 1-2)
- [x] Scale e complexity avaliados
- [x] Technical constraints identificados
- [x] Cross-cutting concerns mapeados

**✅ Architectural Decisions**
- [x] Decisões críticas documentadas com versões (Step 3-4)
- [x] Technology stack totalmente especificado
- [x] Integration patterns definidos
- [x] Performance considerations endereçados

**✅ Implementation Patterns**
- [x] Naming conventions estabelecidas (Step 5)
- [x] Structure patterns definidos
- [x] Communication patterns especificados
- [x] Process patterns documentados
- [x] TDD rules com enforcement
- [x] Resilience patterns validados (Chaos Monkey)

**✅ Project Structure**
- [x] Estrutura completa de diretórios (Step 6)
- [x] Component boundaries estabelecidos
- [x] Integration points mapeados
- [x] Requirements → structure mapping completo

### Architecture Readiness Assessment

**Overall Status:** ✅ READY FOR IMPLEMENTATION

**Confidence Level:** **HIGH** — 100% dos FRs do MVP mapeados, stack coerente, patterns abrangentes, resilience validada.

**Key Strengths:**
- Stack async uniforme (Python ponta a ponta)
- LiteLLM resolve multi-provider com mínimo código
- Guided Recovery errors elevam qualidade da UX
- TDD obrigatório com BMAD compatibility confirmada
- Modelo de dados forward-compatible com MetaCognition V2
- Resilience patterns validados via Chaos Monkey

**Areas for Future Enhancement:**
- E2E test framework (Playwright/Cypress) — definir quando frontend estiver maduro
- CI/CD pipeline — diferido, a definir pós-MVP
- Recovery mais sofisticado (queue de retry, notificação push)

### Implementation Handoff

**AI Agent Guidelines:**
- Seguir TODAS as decisões arquiteturais exatamente como documentadas
- Usar implementation patterns consistentemente em todos os módulos
- Respeitar boundaries de projeto e domínio
- Consultar este documento para QUALQUER dúvida arquitetural

**Sequência de implementação recomendada:**
1. Infra foundation (Docker/PostgreSQL/FastAPI skeleton)
2. Auth module (JWT/TenantMixin/middleware)
3. Projects module (CRUD com isolamento)
4. Sessions + Engine module (SSE streaming + LiteLLM)
5. Documents module (upload + parsing)
6. Artifacts module (JSONB + export)
