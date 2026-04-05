---
stepsCompleted: ['step-01-validate-prerequisites', 'step-02-design-epics', 'step-03-create-stories']
inputDocuments: ['prd.md', 'architecture.md', 'ux-design-specification.md']
totalEpics: 8
totalStories: 39
mvpStories: 31
growthStories: 8
---

# ReqStudio - Epic Breakdown

## Overview

This document provides the complete epic and story breakdown for ReqStudio, decomposing the requirements from the PRD, UX Design and Architecture requirements into implementable stories. Total: 8 epics, 39 stories. MVP: Epics 1-6 (31 stories). Growth/Vision: Epics 7-8 (8 stories).

## Requirements Inventory

### Functional Requirements

**Contexto e Organização (FR1-FR6):** Projetos como containers isolados, resumo de progresso, zero vazamento.
**Enriquecimento de Contexto (FR7-FR11):** Import de docs (PDF, MD), citação de fontes nos artefatos.
**Tradução Assistida (FR12-FR19):** Core — sessão multi-etapa com agentes IA, linguagem não-técnica, construção progressiva.
**Artefatos e Saída (FR20-FR25):** Saída dual (humano + máquina), export MD/JSON, cobertura por seção.
**Evolução Colaborativa (FR26-FR31):** Stakeholders, feedback, re-análise com IA, notificações — Growth.
**Brownfield (FR32-FR37):** Import de docs existentes, análise de codebase — Growth/Vision.
**Identidade e Acesso (FR38-FR42):** Auth, tenant isolation, RBAC — MVP parcial.

Faseamento: FR1-FR25 + FR38-FR40 = MVP | FR26-FR35 + FR41-FR42 = Growth | FR36-FR37 = Vision

### NonFunctional Requirements

**Performance:** NFR1 (IA ≤30s), NFR2 (UI ≤2s), NFR3 (export ≤5s), NFR4 (sessões simultâneas).
**Segurança:** NFR5 (HTTPS), NFR6 (bcrypt), NFR7 (JWT 15min+7d), NFR8 (zero vazamento), NFR9 (dados IA).
**Escalabilidade:** NFR10 (10x), NFR11 (PostgreSQL MVP), NFR12 (custo IA monitorado).
**Disponibilidade:** NFR13 (99.5%), NFR14 (modo degradado), NFR15 (sessão preservada).
**Acessibilidade:** NFR16 (mobile-first 360px), NFR17 (WCAG 2.1 AA), NFR18 (teclado).
**Integração:** NFR19 (abstração provider), NFR20 (export Notion/Jira).

### Additional Requirements

- Starter Template: FastAPI + Vite + React + shadcn/ui — setup manual, primeira story
- PostgreSQL desde MVP via Docker Compose (3 serviços)
- Monolito modular: auth, projects, sessions, engine, documents, artifacts
- LiteLLM como abstração multi-provedor LLM
- SSE para streaming, JSON canônico para artefatos
- TenantMixin + middleware + Context Builder = 3 camadas isolamento
- Guided Recovery Error Pattern para todos os erros
- TDD obrigatório ≥ 80% coverage, OpenTelemetry desde MVP
- Workflows/Agents como seed data (compatível MetaCognition V2+)

### UX Design Requirements

UX-DR1 (input adaptativa), UX-DR2 (ChatMessage), UX-DR3 (ArtifactCard), UX-DR4 (CoverageBar), UX-DR5 (SaveIndicator), UX-DR6 (CitationBadge), UX-DR7 (DisagreementPanel), UX-DR8 (WelcomeScreen), UX-DR9 (split/tabbed view), UX-DR10 (artifact feed mobile), UX-DR11 (design tokens indigo+âmbar), UX-DR12 (Inter+JetBrains Mono), UX-DR13 (espaçamento 4px base), UX-DR14 (dark mode), UX-DR15 (hierarquia botões), UX-DR16 (anti-modal), UX-DR17 (loading states), UX-DR18 (touch 44px), UX-DR19 (focus ring), UX-DR20 (transição fases), UX-DR21 (hierarquia cromática).

### FR Coverage Map

| FR | Epic | Descrição |
|----|------|-----------|
| FR1-FR6 | Epic 3 | Projetos como Espaços de Trabalho |
| FR7-FR8, FR11 | Epic 4 | Enriquecimento de Contexto |
| FR9-FR10, FR12-FR19 | Epic 5 | Sessão de Elicitação |
| FR20-FR25 | Epic 6 | Artefatos e Exportação |
| FR26-FR31, FR41-FR42 | Epic 7 | Evolução Colaborativa |
| FR32-FR37 | Epic 8 | Elicitação Brownfield |
| FR38-FR40 | Epic 2 | Identidade e Acesso |

## Epic List

### Epic 1: Infraestrutura e Fundação do Projeto
Esqueleto rodando localmente — FastAPI, React/Vite/shadcn, PostgreSQL via Docker Compose. TDD, Design System Foundation, OpenTelemetry.
**FRs cobertos:** Nenhum (fundação). **NFRs:** NFR2, NFR5, NFR16.

### Epic 2: Identidade, Acesso e Isolamento de Dados
Cadastro, login, JWT (15min+7d rotation), TenantMixin, zero vazamento.
**FRs cobertos:** FR38, FR39, FR40. **NFRs:** NFR5-NFR8.

### Epic 3: Projetos como Espaços de Trabalho
CRUD projetos, dashboard com progresso, boas-vindas contextuais, arquivamento.
**FRs cobertos:** FR1-FR6. **NFRs:** NFR2, NFR8.

### Epic 4: Enriquecimento de Contexto — Importação de Documentos
Import PDF/MD, parsing, chunking, gerenciamento de docs.
**FRs cobertos:** FR7, FR8, FR11. **NFRs:** NFR8.

### Epic 5: Sessão de Elicitação — O Core do Produto
Sessão conversacional com IA, SSE streaming, duas fases, split/tabbed view.
**FRs cobertos:** FR9-FR10, FR12-FR19. **NFRs:** NFR1, NFR4, NFR14, NFR15, NFR19.

### Epic 5.5: Dívida Técnica e Fundações para Artefatos
Action items críticos da Retro Epic 5 formalizados como pré-condições para o Epic 6. Retorno intencional ao ciclo do Epic 5.
**FRs cobertos:** FR8, FR9 (parcial), FR15. **NFRs:** NFR11, NFR12.

### Epic 6: Artefatos — Geração, Visualização e Exportação
JSON canônico, rendering dual, cobertura, export MD/JSON, versionamento.
**FRs cobertos:** FR20-FR25. **NFRs:** NFR3, NFR20.

### Epic 7: Evolução Colaborativa (Growth)
RBAC, publicação seletiva, feedback por seção, re-análise com IA, notificações.
**FRs cobertos:** FR26-FR31, FR41-FR42.

### Epic 8: Elicitação Brownfield (Growth/Vision)
Import docs existentes, gap analysis, impacto, conexão repo.
**FRs cobertos:** FR32-FR37.

---

## Epic 1: Infraestrutura e Fundação do Projeto

Esqueleto do projeto rodando localmente com TDD, Design System Foundation e padrões cross-cutting.

### Story 1.1: Inicialização do Backend FastAPI com Docker Compose

As a desenvolvedor,
I want um backend FastAPI funcional com PostgreSQL rodando via Docker Compose,
So that eu tenha a fundação de infraestrutura para implementar todos os módulos.

**Acceptance Criteria:**

**Given** o repositório clonado e Docker instalado
**When** eu executo `docker-compose up`
**Then** o serviço `api` (FastAPI) inicia na porta configurável via `.env` (default 8000)
**And** o serviço `db` (PostgreSQL 16) inicia na porta configurável (default 5432)
**And** o endpoint `GET /health` retorna `{"status": "ok"}` com HTTP 200
**And** a estrutura de diretórios segue o padrão arquitetural (`app/core/`, `app/modules/`, `app/db/`, `app/integrations/`)
**And** Alembic está configurado e conectado ao PostgreSQL
**And** `conftest.py` global com fixtures de TestDB e 2 tenants está criado
**And** Pytest + Ruff estão configurados e `pytest` roda sem erros
**And** `.env.example` com todas as variáveis documentadas existe
**And** Pydantic `BaseSettings` valida variáveis na startup (fail fast)
**And** script `find-ports` (`.sh` + `.ps1`) detecta portas livres

### Story 1.2: Inicialização do Frontend React/Vite com shadcn/ui

As a desenvolvedor,
I want um frontend React + TypeScript + Vite com shadcn/ui configurado,
So that eu tenha a fundação de UI para implementar as telas do ReqStudio.

**Acceptance Criteria:**

**Given** o repositório com o backend funcional (Story 1.1)
**When** eu acesso `http://localhost:{FRONTEND_PORT}` no browser
**Then** uma página placeholder do ReqStudio é exibida
**And** React 18+ com TypeScript strict, shadcn/ui inicializado, Tailwind CSS com CSS variables
**And** estrutura de diretórios conforme arquitetura (`components/`, `pages/`, `hooks/`, `services/`, `contexts/`, `types/`, `lib/`)
**And** React Router v6 com lazy loading configurado
**And** Vitest + ESLint configurados e rodando sem erros
**And** serviço `frontend` adicionado ao `docker-compose.yml`

### Story 1.3: Design System Foundation — Tokens, Tipografia e Tema

As a desenvolvedor,
I want os design tokens, tipografia e sistema de tema implementados,
So that todos os componentes usem uma base visual consistente conforme a UX Spec.

**Acceptance Criteria:**

**Given** o frontend inicializado (Story 1.2)
**When** eu abro o `index.css`
**Then** CSS variables definidas: paleta indigo (primary, hover, light, user-message), âmbar (accent, light), semânticas (success, warning, error, info), neutros (background, surface, border, text-primary/secondary/muted)
**And** Inter via Google Fonts + JetBrains Mono carregados
**And** type scale como tokens CSS (display 30px a caption 12px)
**And** espaçamento base 4px (space-1 a space-8), border-radius (sm a full), sombras (sm a lg)
**And** dark mode via toggle com variáveis ajustadas
**And** contraste 4.5:1 verificável (NFR17)

### Story 1.4: Core Backend — Middleware, Error Handling e Telemetria

As a desenvolvedor,
I want os padrões cross-cutting do backend implementados,
So that todos os módulos tenham infraestrutura consistente desde o primeiro endpoint.

**Acceptance Criteria:**

**Given** o backend funcional (Story 1.1)
**When** uma request chega ao FastAPI
**Then** `RequestIdMiddleware` adiciona UUID no header `X-Request-ID`
**And** `TenantMiddleware` preparado para extrair `tenant_id` do JWT
**And** `GuidedRecoveryError` implementado com `code`, `message`, `help`, `actions`, `severity`
**And** `error_handlers.py` retorna JSON `{"error": {...}}` para GuidedRecoveryError
**And** catálogo inicial de erros como enum (SESSION_EXPIRED, VALIDATION_ERROR, INTERNAL_ERROR)
**And** OpenTelemetry SDK com tracing básico, logs structured JSON
**And** CORS configurável via `.env`, rate limiting via slowapi
**And** testes ≥ 80% coverage

---

## Epic 2: Identidade, Acesso e Isolamento de Dados

Cadastro, login, JWT com refresh rotation e isolamento por tenant.

### Story 2.1: Registro de Usuário com E-mail e Senha

As a visitante do ReqStudio,
I want criar uma conta com e-mail e senha,
So that eu possa acessar a plataforma e iniciar meus projetos.

**Acceptance Criteria:**

**Given** `POST /api/v1/auth/register` disponível
**When** envio payload com `email` e `password` válidos
**Then** User criado com senha bcrypt, tenant criado automaticamente, HTTP 201
**And** e-mail duplicado → Guided Recovery `EMAIL_ALREADY_EXISTS`
**And** senha fraca (<8 chars) → Guided Recovery `WEAK_PASSWORD`
**And** testes: registro sucesso, duplicado, senha fraca, isolamento multi-tenant

### Story 2.2: Login e Emissão de Tokens JWT

As a usuário registrado,
I want fazer login e receber tokens de acesso,
So that eu possa acessar meus projetos de forma segura.

**Acceptance Criteria:**

**Given** usuário registrado
**When** `POST /api/v1/auth/login` com credenciais corretas
**Then** access_token (JWT 15min) no corpo, refresh_token (7d) como httpOnly cookie (SameSite=Strict, Secure=True)
**And** claims: user_id, tenant_id, exp, iat
**And** credenciais erradas → Guided Recovery `INVALID_CREDENTIALS`
**And** dependencies `get_current_user` e `get_tenant_id` funcionam
**And** testes: login sucesso, credenciais erradas, token expirado, claims

### Story 2.3: Refresh Token com Rotation e Proteção contra Reuso

As a usuário autenticado,
I want que minha sessão seja renovada automaticamente,
So that eu não perca meu trabalho durante sessão longa.

**Acceptance Criteria:**

**Given** refresh token válido (httpOnly cookie)
**When** `POST /api/v1/auth/refresh`
**Then** novo access_token + novo refresh_token, anterior invalidado (rotation)
**And** token já usado (reuse) → revoga TODOS tokens do user → `TOKEN_REUSE_DETECTED` blocking
**And** token expirado → `SESSION_EXPIRED`
**And** modelo RefreshToken com: id, user_id, token_hash, expires_at, used_at, revoked_at
**And** testes: refresh, rotation, reuse detection + revogação, expirado

### Story 2.4: TenantMixin e Isolamento de Dados no Banco

As a desenvolvedor,
I want que todo model tenha isolamento automático por tenant,
So that zero vazamento de dados entre tenants ocorra (NFR8).

**Acceptance Criteria:**

**Given** `TenantMixin` em `app/db/base.py`
**When** model herda de TenantMixin
**Then** coluna `tenant_id` (UUID, NOT NULL, indexed) adicionada automaticamente
**And** toda query filtra por `tenant_id` do request
**And** conftest.py com 2 tenants (`tenant_a`, `tenant_b`)
**And** CRUD com tenant A não visível em tenant B
**And** registro sem tenant_id → NOT NULL constraint error
**And** testes: isolamento completo, coverage ≥ 80%

### Story 2.5: Tela de Login e Registro no Frontend

As a Ana (especialista de domínio),
I want uma tela de login limpa e acolhedora,
So that eu me sinta segura para criar minha conta ou fazer login.

**Acceptance Criteria:**

**Given** frontend acessado sem autenticação
**When** rota `/login` carregada
**Then** campos e-mail/senha, botão "Entrar" (indigo), link "Criar conta"
**And** modo registro: e-mail + senha + confirmação, validação inline
**And** sucesso → token em memória (AuthContext) → redirect `/projects`
**And** erros Guided Recovery inline (UX-DR16)
**And** apiClient intercepta 401 → refresh → retry → redirect login
**And** responsivo 360px+, design tokens do Story 1.3
**And** testes: renderização, validação, submit sucesso/erro, interceptor 401

---

## Epic 3: Projetos como Espaços de Trabalho

CRUD projetos, dashboard com progresso, boas-vindas contextuais, arquivamento.

### Story 3.1: CRUD de Projetos no Backend

As a usuário autenticado,
I want criar, listar, acessar, atualizar e arquivar projetos,
So that eu tenha espaços de trabalho organizados para cada cliente.

**Acceptance Criteria:**

**Given** módulo `modules/projects/`
**When** `POST /api/v1/projects` com name, description, business_domain
**Then** Project criado com tenant_id do JWT, status active, HTTP 201
**And** `GET /api/v1/projects` → lista paginada (active default, ?status=archived)
**And** `PATCH /api/v1/projects/{id}` → atualizar/arquivar sem perda de dados (FR5)
**And** `GET /api/v1/projects/{id}` → dados completos com progress_summary JSONB
**And** projeto de outro tenant → HTTP 404 (não 403)
**And** model Project: TenantMixin, id, name, description, business_domain, status, progress_summary (JSONB), created_at, updated_at
**And** testes: CRUD, isolamento, arquivamento, paginação, coverage ≥ 80%

### Story 3.2: Dashboard de Projetos no Frontend

As a Carla (consultora multi-cliente),
I want ver meus projetos num dashboard com progresso visual,
So that eu gerencie múltiplos clientes com status instantâneo.

**Acceptance Criteria:**

**Given** rota `/projects` autenticada
**When** ProjectsPage carrega
**Then** grid de project cards (3-4 col desktop, 2 tablet, lista mobile)
**And** card: nome, domínio, barra progresso, data última atividade
**And** botão "+ Novo Projeto" sempre visível (primário indigo)
**And** empty state: ilustração + "Crie seu primeiro projeto" (UX-DR17)
**And** skeleton pulse durante loading (UX-DR17)
**And** click card → `/projects/{id}`
**And** useProjects hook com TanStack Query, responsivo 360px+, ≤ 2s (NFR2)

### Story 3.3: Criação e Edição de Projeto no Frontend

As a Ana,
I want criar um novo projeto informando nome, descrição e domínio,
So that eu tenha um espaço dedicado para meus requisitos.

**Acceptance Criteria:**

**Given** botão "+ Novo Projeto" clicado
**When** formulário exibido
**Then** campos: Nome (obrigatório), Descrição (textarea), Domínio de negócio
**And** validação inline, botão "Criar projeto" + "Cancelar"
**And** sucesso → redirect `/projects/{id}` + toast 3s
**And** edição via menu dropdown no card, PATCH com feedback
**And** erros Guided Recovery inline (UX-DR16)

### Story 3.4: Detalhe do Projeto com Boas-vindas Contextuais

As a Ana,
I want que ao acessar meu projeto o sistema me mostre onde parei,
So that eu retome sem perder tempo relembrando o contexto (FR4).

**Acceptance Criteria:**

**Given** rota `/projects/{id}`
**When** ProjectDetailPage renderiza
**Then** WelcomeScreen (UX-DR8): greeting, nome projeto, progresso checklist, próximo passo, botão "Continuar sessão"
**And** sem sessões anteriores: "Vamos começar! Descreva o problema..."
**And** com sessões: lista de sessões, docs importados, artefatos
**And** zero vazamento de contexto (FR3, FR6), responsivo 360px+

### Story 3.5: Arquivamento de Projetos e Filtro por Status

As a Carla,
I want arquivar projetos concluídos e filtrar por status,
So that eu mantenha meu dashboard limpo sem perder dados (FR5).

**Acceptance Criteria:**

**Given** projeto ativo no dashboard
**When** "Arquivar" selecionado
**Then** confirmação inline → projeto muda para archived, desaparece da lista ativa
**And** aba "Arquivados" → projetos archived, opção "Restaurar"
**And** restauração volta para active com dados intactos
**And** confirmações inline (UX-DR16)

---

## Epic 4: Enriquecimento de Contexto — Importação de Documentos

Import PDF/Markdown, parsing, chunking, gerenciamento de docs do projeto.

### Story 4.1: Upload e Parsing de Documentos no Backend

As a Ana,
I want importar documentos de referência ao meu projeto,
So that a IA use como contexto para a elicitação (FR7).

**Acceptance Criteria:**

**Given** `POST /api/v1/projects/{project_id}/documents` com multipart upload
**When** PDF ou Markdown válido enviado
**Then** Document salvo (id, project_id, tenant_id, filename, mime_type, size_bytes, status processing→ready)
**And** parser acionado (pdf_parser, markdown_parser), chunks salvos em DocumentChunk
**And** >20MB → Guided Recovery `UPLOAD_TOO_LARGE`
**And** MIME inválido → Guided Recovery `UNSUPPORTED_FILE_TYPE`
**And** validação MIME real (não extensão), parsers em chunks
**And** models Document + DocumentChunk com TenantMixin
**And** testes: upload, parsing, limite, MIME, isolamento, coverage ≥ 80%

### Story 4.2: Listagem e Gerenciamento de Documentos do Projeto

As a Ana,
I want ver quais documentos estão ativos e poder removê-los,
So that eu saiba que contexto a IA está usando (FR11).

**Acceptance Criteria:**

**Given** `GET /api/v1/projects/{project_id}/documents`
**When** lista solicitada
**Then** docs do projeto com filename, mime_type, size, status, chunk_count, created_at
**And** `DELETE /api/v1/projects/{project_id}/documents/{id}` → remove doc + chunks, HTTP 204
**And** doc de outro tenant → HTTP 404
**And** testes: listagem, remoção, isolamento

### Story 4.3: Interface de Upload de Documentos no Frontend

As a Ana,
I want uma forma simples de importar documentos ao projeto,
So that eu traga SLAs, normas e contratos sem fricção (FR7, FR8).

**Acceptance Criteria:**

**Given** ProjectDetailPage → seção "Documentos de Referência"
**When** "Importar documento" clicado
**Then** file picker (desktop) ou Web Share API (mobile, com fallback)
**And** barra de progresso durante upload
**And** status "Processando..." → "Pronto"
**And** erro → Guided Recovery inline (UX-DR16)
**And** remover → confirmação inline → lista atualizada
**And** componente DocumentUpload, responsivo 360px+

---

## Epic 5: Sessão de Elicitação — O Core do Produto

Sessão conversacional com IA, SSE streaming, duas fases, split/tabbed view, pausar/retomar.

### Story 5.1: Modelo de Dados de Sessões e Mensagens

As a desenvolvedor,
I want os models de Session e Message persistidos com estado de workflow,
So that sessões sejam pausáveis, retomáveis e rastreáveis (FR15).

**Acceptance Criteria:**

**Given** módulo `modules/sessions/`
**When** models criados
**Then** Session: id, project_id, tenant_id, workflow_id (FK), workflow_position (JSON), status (active/paused/completed), artifact_state (JSONB), created_at, updated_at
**And** Message: id, session_id, tenant_id, role (user/assistant/system), content, message_index, metadata (JSONB), created_at
**And** TenantMixin em ambos
**And** seed data: Workflow, WorkflowStep, Agent com dados BMAD hardcoded
**And** endpoints: CRUD sessions + messages paginadas
**And** testes: CRUD, seed data, isolamento, coverage ≥ 80%

### Story 5.2: Context Builder — Montagem de Prompt com Isolamento

As a desenvolvedor,
I want um Context Builder que monte o prompt com contexto completo e isolado,
So that toda chamada à IA tenha contexto priorizado e seguro (FR9, FR6).

**Acceptance Criteria:**

**Given** `engine/context_builder.py`
**When** `build_context(session_id)` chamado
**Then** monta prompt com prioridade: system prompt > docs referência > artifact_state > mensagens recentes > mensagens antigas
**And** excede limite tokens → trunca mensagens antigas primeiro
**And** valida 100% pertence ao project_id → senão `ContextIsolationError`
**And** testes: montagem, priorização, truncamento, isolamento, contagem tokens

### Story 5.3: LiteLLM Integration — Abstração Multi-Provider com Streaming

As a desenvolvedor,
I want wrapper LiteLLM com streaming e cost tracking,
So that o ReqStudio funcione com múltiplos providers (NFR19).

**Acceptance Criteria:**

**Given** `integrations/llm_client.py`
**When** `stream_completion(messages)` chamado
**Then** usa LiteLLM com provider configurável via .env, retorna async generator de chunks
**And** fallback automático (LiteLLM built-in), após exaustão → `LLMUnavailableError`
**And** timeout configurável (60s default) → `LLMTimeoutError`
**And** cost tracking via OpenTelemetry: tokens input/output, custo USD, latência
**And** testes mock: streaming, fallback, timeout, cost tracking

### Story 5.4: Elicitation Engine — Orquestração de Sessão com Workflow

As a desenvolvedor,
I want um Elicitation Engine que orquestre a sessão seguindo o workflow,
So that a IA conduza sessão multi-etapa com construção progressiva (FR12, FR18).

**Acceptance Criteria:**

**Given** `engine/service.py`
**When** `elicit(session_id, user_message)` chamado
**Then** pipeline: write-ahead save → load workflow position → context builder → LLM stream → save response → update workflow_position + artifact_state
**And** workflow step completo → avança posição
**And** docs referenciados (FR9), fontes citadas (FR10)
**And** desconexão mid-stream → backend salva resposta completa independente do client
**And** workflows hardcoded: briefing.py, prd.py
**And** testes: pipeline, write-ahead, progression, crash recovery

### Story 5.5: SSE Endpoint — Streaming de Respostas

As a desenvolvedor,
I want endpoint SSE que transmita respostas em tempo real,
So that o frontend exiba typing indicator e artefato crescendo (FR21).

**Acceptance Criteria:**

**Given** `POST /api/v1/sessions/{id}/messages` com `Accept: text/event-stream`
**When** usuário envia mensagem
**Then** StreamingResponse com SSE events: `event: message\ndata: {"content":"...", "done": false}`
**And** chunk final: `done: true, artifact_updated: true`
**And** erro: `event: error\ndata: {"code": "LLM_UNAVAILABLE"}`
**And** message_id único (idempotência), reconnect via `GET /sessions/{id}/messages?after={id}`
**And** testes: streaming, erro, timeout, idempotência, reconciliação

### Story 5.6: Tela de Sessão — Chat com Split/Tabbed View

As a Ana,
I want tela dividida (desktop) ou tabs (mobile) vendo o artefato crescer,
So that eu perceba meu progresso enquanto contribuo (UX-DR9).

**Acceptance Criteria:**

**Given** rota `/sessions/{id}` em desktop (≥1024px)
**When** SessionPage renderiza
**Then** split view: chat 40% + artefato 60% (fixo MVP), header com SaveIndicator + CoverageBar
**And** mobile (<1024px): tabbed view Conversa | Artefato com badge "Atualizado"
**And** Fase 1: input expansível amplo. Fase 2: input compacto expansível (UX-DR1)
**And** ChatInput com auto-resize, enviar botão + Enter (desktop)
**And** mensagens user em indigo médio (UX-DR21), IA com avatar
**And** responsivo 360px+

### Story 5.7: Streaming de Chat — SSE Client e Typing Indicator

As a Ana,
I want ver a resposta da IA aparecendo em tempo real,
So that eu saiba que está processando e veja o resultado construindo.

**Acceptance Criteria:**

**Given** hook `useSSE`
**When** mensagem enviada via `useSession.sendMessage()`
**Then** typing indicator "Refletindo..." (3 dots animados, UX-DR17)
**And** chunks SSE renderizados progressivamente no ChatMessage streaming mode
**And** `done: true` → typing desaparece, mensagem finalizada
**And** SSE drop → reconnect exponential backoff, banner "Reconectando..."
**And** reconciliação pós-reconnect, idempotência por message_id
**And** 30s sem resposta → Guided Recovery inline
**And** ChatMessage com markdown rendering + citation badges (UX-DR2, UX-DR6)

### Story 5.8: Pausar e Retomar Sessão

As a Ana,
I want pausar e retomar sessão sem perder nada,
So that eu trabalhe no meu ritmo (FR15).

**Acceptance Criteria:**

**Given** sessão ativa, Ana navega para fora
**When** saída detectada
**Then** sessão auto-salva com status `paused`, workflow_position e artifact_state persistidos
**And** WelcomeScreen mostra "Sessão em andamento. Última interação há X."
**And** ao reabrir: mensagens carregadas, artefato restaurado, IA retoma do workflow_position correto
**And** primeira mensagem IA: "Voltamos onde paramos. [resumo]"
**And** desconexão ≤ 5min → SSE reconecta e reconcilia (NFR15)

### Story 5.9: Modo Degradado — IA Indisponível

As a Ana,
I want que se a IA ficar indisponível minha sessão não se perca,
So that eu não perca trabalho por problemas técnicos (NFR14).

**Acceptance Criteria:**

**Given** IA indisponível (LLMUnavailableError)
**When** Ana envia mensagem
**Then** SSE error event `LLM_UNAVAILABLE`
**And** Guided Recovery inline: "IA temporariamente indisponível. Sessão segura."
**And** mensagem da Ana já salva (write-ahead save), sessão não corrompida
**And** DB failure → Guided Recovery + pool_pre_ping auto-reconnect

---

## Epic 5.5: Dívida Técnica e Fundações para Artefatos

Action items críticos da Retrospectiva do Epic 5, formalizados como pré-condições para o Epic 6. Retorno intencional ao ciclo do Epic 5 para honrar gaps identificados no teste real do produto.

**Origem:** `epic-5-retro-2026-03-31.md` — Action Items A1–A5  
**FRs cobertos:** FR8, FR9 (parcial), FR15. **NFRs:** NFR11, NFR12.

### Story 5.5-1: System Prompts com Qualidade BMAD Real

As a Ana (especialista de domínio),
I want que a IA conduza a sessão com personalidade, técnicas de elicitação e regras claras,
So that eu perceba diferença real entre o ReqStudio e um chatbot genérico (FR12, FR13, FR19).

**Acceptance Criteria:**

**Given** seed data de Agents e WorkflowSteps no banco
**When** sessão de elicitação inicia
**Then** system prompt do agente PM contém: persona definida, técnicas de elicitação (5 Whys, JTBD, cenários negativos), regras de verbosidade (máx 3 perguntas por turno), exemplos few-shot de boas respostas
**And** Fase 1 (contextualização): tom de ouvinte ativo, sem interromper fluxo da Ana
**And** Fase 2 (guiada): perguntas estruturadas, desafio baseado em docs, sinalização de transição
**And** resposta curta e clara: sem bullet points desnecessários, sem repetir o que o usuário disse
**And** testes: prompt length > 500 chars, keywords de personalidade presentes, few-shot examples incluídos

**Origem:** Retro Epic 5 — Action Item A1 (🔴 Crítico)

### Story 5.5-2: Retomar Sessão Existente na ProjectDetailPage

As a Ana,
I want que ao acessar meu projeto o sistema detecte sessões em andamento e me ofereça continuar,
So that eu retome de onde parei sem criar uma sessão nova desnecessariamente (FR15, FR4).

**Acceptance Criteria:**

**Given** rota `/projects/{id}` com sessão `active` ou `paused` existente
**When** ProjectDetailPage renderiza
**Then** `GET /api/v1/projects/{id}/sessions?status=active,paused` retorna sessões existentes
**And** se existir sessão → botão "Continuar sessão" → navega para `/sessions/{session_id}`
**And** se não existir → botão "Iniciar elicitação" → cria nova sessão
**And** WelcomeScreen exibe: última interação, % cobertura atual, próximo passo
**And** `progress_summary` do projeto atualizado pelo Elicitation Engine após cada mensagem
**And** testes: detecção ativa, detecção pausada, fallback sem sessão, progress_summary atualizado

**Origem:** Retro Epic 5 — Action Item A2 (🔴 Alta)

### Story 5.5-3: Migration Automática no Startup do Container

As a desenvolvedor,
I want que migrações Alembic sejam aplicadas automaticamente no startup,
So that o banco de dados esteja sempre sincronizado com o schema atual sem intervenção manual.

**Acceptance Criteria:**

**Given** container `api` iniciando
**When** FastAPI app factory executa
**Then** `alembic upgrade head` executado automaticamente antes de aceitar requests
**And** `alembic/env.py` importa todos os models de todos os módulos (auth, projects, sessions, engine, documents, artifacts)
**And** startup falha com log claro se migration falhar (fail fast)
**And** `docker-compose up` do zero resulta em schema completo sem intervenção manual
**And** CI gate: `docker-compose up && alembic check` valida schema sincronizado
**And** testes: startup com DB vazio, startup com schema desatualizado, rollback com erro

**Origem:** Retro Epic 5 — Action Items A5 (🔴 Alta) + A6 (🟡 Média)

### Story 5.5-4: Upload de Documento via ChatInput

As a Ana,
I want anexar um documento diretamente na conversa de elicitação,
So that eu enriqueça o contexto da IA sem sair do chat (FR8).

**Acceptance Criteria:**

**Given** `ChatInput` na SessionPage
**When** ícone 📎 clicado
**Then** file picker abre (formatos: PDF, MD, DOCX, XLSX — máx 20MB)
**And** mobile: usa Web Share API (com fallback para file picker tradicional)
**And** upload via `POST /api/v1/projects/{id}/documents` (reutiliza Epic 4)
**And** status inline no chat: "📄 Processando contrato.pdf..." → "✅ Pronto — adicionado ao contexto"
**And** próxima mensagem do usuário já tem o doc disponível no Context Builder
**And** erro → Guided Recovery inline (sem modal): "Arquivo muito grande. Tente um PDF menor."
**And** testes: upload sucesso, erro MIME, erro tamanho, injeção no contexto, mobile fallback

**Origem:** Retro Epic 5 — Action Item A3 (🟡 Média)

### Story 5.5-5: Telemetria Baseline — Tokens e Custo por Mensagem

As a Ana,
I want ver quanto a sessão está consumindo de IA em tempo real,
So that eu tenha transparência sobre o uso e custo da plataforma (NFR12).

**Acceptance Criteria:**

**Given** mensagem enviada e resposta finalizada (chunk `done: true`)
**When** Elicitation Engine salva resposta
**Then** colunas `input_tokens`, `output_tokens`, `cost_usd`, `model` salvas na tabela `messages` (role=assistant)
**And** mini-widget visível no header da SessionPage: "💰 $0.02 · 1.2k tokens"
**And** tooltip expandido: input tokens, output tokens, modelo usado, latência
**And** sem sessão ativa: widget oculto
**And** testes: persistência das métricas, widget renderizado, tooltip com breakdown, modelo correto

**Origem:** Retro Epic 5 — Action Item A4 (🟡 Média)

---

## Epic 6: Artefatos — Geração, Visualização e Exportação

JSON canônico, rendering dual, cobertura por seção, export, versionamento.

### Story 6.0: Gate de QA — Hardening de Sessões e Upload

As a time de produto,
I want fechar os gaps de teste críticos remanescentes da Sprint 5.5 antes de iniciar o core de artefatos,
So that o Epic 6 comece sobre uma base validada e com menor risco de regressão.

**Acceptance Criteria:**

**Given** relatório `qa-audit-sprint-5-5.md`
**When** o gate de hardening for executado
**Then** `useProjectSessions.test.ts` deve testar o hook real (`useProjectSessions`) com `renderHook` + QueryClient, sem duplicar lógica de filtro no teste
**And** existir teste de integração leve validando o callback chain `SessionPage -> ChatInput -> handleUploadSuccess -> sendMessage`
**And** os testes novos devem falhar quando há regressão nesses fluxos
**And** evidência de execução (output de teste) anexada no artefato da story

### Story 6.0b: DoD com Checklist de Evidências e Handoff de Terminal

As a Scrum Master e QA,
I want formalizar no fluxo de desenvolvimento o checklist de evidências e o rito de handoff em Terminal Restricted Mode,
So that cada story seja encerrada com prova objetiva e sem presunção de execução.

**Acceptance Criteria:**

**Given** `project-context.md` seção 7 e action item AI-3 da retro Epic 5.5
**When** uma story for movida para `review` ou `done`
**Then** o artefato da story deve incluir bloco "Evidências de Validação" com comandos e outputs relevantes
**And** comandos críticos que dependem do usuário devem ser registrados como "Waiting for Manual Execution" no fluxo da story
**And** nenhum fechamento de story ocorre sem evidência anexada na conversa e no arquivo da story
**And** template/checklist de PR/review atualizado para refletir o novo DoD

### Story 6.0c: Hardening de UX do Chat e Confiabilidade de Sessão

As a Ana,
I want que o chat tenha fluxo contínuo e que minha sessão seja estável durante uso normal,
So that eu consiga conduzir a elicitação sem fricção operacional e sem perda de contexto.

**Acceptance Criteria:**

**Given** SessionPage ativa com mensagens da IA em streaming
**When** novas mensagens chegam
**Then** a rolagem acompanha automaticamente a resposta até o final do streaming, sem exigir interação manual na barra lateral
**And** mensagens longas do usuário não sobrepõem os blocos da IA (layout resiliente com quebra/limite de altura)
**And** botão de upload permanece habilitado quando `projectId` existe e o estado de loading não está ativo
**And** upload via ChatInput executa o fluxo completo (`pick -> upload -> status inline -> contexto disponível`) sem ficar inativo sem motivo
**And** sessão não expira abruptamente em uso contínuo de curta duração (3-4 min) sem feedback ao usuário
**And** em caso de expiração real, UX mostra mensagem guiada e ação de recuperação (relogin/retomar), sem saída brusca
**And** widget de custo/tokens exibe valor consistente e estável entre renders (normalização de arredondamento/precisão)
**And** testes: regressão de autoscroll, layout de mensagem longa, upload ativo/inativo, fluxo de sessão expirada com recovery, consistência de formatação do custo

### Story 6.0d: Fidelidade da Persona BMAD na Elicitação

As a Ana,
I want que o agente se comporte como um facilitador BMAD real desde o início da sessão,
So that eu perceba uma entrevista profissional, com identidade clara e progresso perceptível.

**Acceptance Criteria:**

**Given** primeira mensagem da sessão
**When** o agente inicia a conversa
**Then** o agente se apresenta com nome e papel claramente
**And** usa o nome de exibição do usuário (quando disponível) em vez do prefixo do e-mail
**And** declara objetivo e estrutura da entrevista (fases e expectativa de encerramento)
**And** mantém estilo 100% BMAD para elicitação inicial (perguntas direcionadas, progressão clara e sem massificar)
**And** sinaliza evolução e proximidade de fechamento ao longo dos blocos da entrevista
**And** painel de etapas/progresso fica visível também durante a tela de trabalho da sessão (não apenas no retorno ao projeto)
**And** testes: prompt/seed com elementos obrigatórios de apresentação e identidade, cenários de UX cobrindo abertura da sessão e progressão

### Story 6.1: Modelo de Artefato com JSON Canônico e Versionamento

As a desenvolvedor,
I want modelo de artefato com JSON canônico e versionamento,
So that artefatos sejam flexíveis, rastreáveis e renderizáveis (FR24).

**Acceptance Criteria:**

**Given** módulo `modules/artifacts/`
**When** models criados
**Then** Artifact: id, session_id, project_id, tenant_id, artifact_type, title, artifact_state (JSONB), coverage_data (JSONB), version, status (draft/complete), timestamps
**And** ArtifactVersion: id, artifact_id, tenant_id, version, artifact_state snapshot, change_reason, changed_by, created_at
**And** artifact_state schema: `{"sections": [{"id", "title", "content", "coverage", "sources", "last_updated"}], "metadata": {"total_coverage"}}`
**And** atualização → nova ArtifactVersion automática, version incrementado
**And** endpoints: list, get, get versions
**And** testes: CRUD, versionamento, JSONB, isolamento

### Story 6.2: Renderização Dual — Visão de Negócio e Técnica

As a Ana,
I want ver artefato em linguagem de negócio e em formato técnico,
So that eu e o time técnico tenhamos acesso adequado (FR20).

**Acceptance Criteria:**

**Given** `artifacts/renderers/markdown_renderer.py`
**When** `render(artifact, view="business")` → Markdown com linguagem de negócio, prosa clara
**When** `render(artifact, view="technical")` → Markdown técnico, Given/When/Then
**And** endpoint `GET /api/v1/artifacts/{id}/render?view=business|technical`
**And** ambas visões do mesmo artifact_state JSONB (source of truth)
**And** seções cobertura baixa → "⚠️ Pendente de aprofundamento"

### Story 6.3: Cobertura por Seção do Artefato

As a Ana,
I want ver quais seções foram bem exploradas e quais precisam mais,
So that eu saiba onde investir tempo (FR25).

**Acceptance Criteria:**

**Given** `artifacts/service.py`
**When** `calculate_coverage(artifact_id)` chamado
**Then** cobertura por seção (0.0-1.0) baseada em interações e validações
**And** CoverageBar global: <30% muted, 30-70% âmbar, >70% success (UX-DR4)
**And** ArtifactCard mobile: complete (verde), active (âmbar "Ao vivo"), pending (opacidade) (UX-DR3)

### Story 6.4: Exportação de Artefatos em Markdown e JSON

As a Ana,
I want exportar artefato em Markdown e JSON,
So that eu leve o resultado para reuniões e pipelines (FR22, FR23).

**Acceptance Criteria:**

**Given** `GET /api/v1/artifacts/{id}/export?format=markdown&view=business|technical`
**When** solicitado
**Then** download `.md` com metadados (projeto, versão, cobertura)
**And** format=json → `.json` com artifact_state completo, compatível como prompt IA (FR23)
**And** ≤ 5s para 50 páginas (NFR3), compatível Notion/Jira (NFR20)

### Story 6.5: Tela de Visualização e Exportação de Artefatos

As a Ana,
I want tela dedicada para revisar e exportar artefato completo,
So that eu verifique resultado final e baixe no formato certo.

**Acceptance Criteria:**

**Given** rota `/artifacts/{id}`
**When** desktop: documento completo com scroll, toggle Negócio/Técnico, CoverageBar, citation badges (UX-DR6)
**When** mobile: Artifact as Feed — cards por seção scroll vertical (UX-DR10, UX-DR3)
**And** botão "Exportar" → opções MD negócio, MD técnico, JSON
**And** histórico versões com data, razão, autor (FR24)
**And** responsivo 360px+

---

## Epic 7: Evolução Colaborativa (Growth)

RBAC, publicação seletiva, feedback por seção, re-análise com IA, notificações.

### Story 7.1: RBAC — Papéis e Permissões Diferenciadas

As a administrador,
I want papéis diferenciados (Analista, Stakeholder, Admin),
So that cada usuário acesse apenas o permitido (FR42).

**Acceptance Criteria:**

**Given** modelo ProjectMember (project_id, user_id, tenant_id, role)
**When** RBAC implementado
**Then** 3 papéis: analyst (owner), stakeholder (leitura+feedback), admin (auditoria)
**And** dependency `require_role(roles)` verifica papel
**And** stakeholder tentando criar sessão → Guided Recovery `INSUFFICIENT_PERMISSIONS`
**And** endpoints: convite por e-mail, listagem de membros

### Story 7.2: Publicação Seletiva de Artefatos

As a Ana,
I want controlar quais artefatos stakeholders veem,
So that eu publique quando confiante (FR41).

**Acceptance Criteria:**

**Given** artefato draft
**When** "Publicar" clicado → status published, stakeholders veem
**And** "Despublicar" → volta draft, stakeholders perdem acesso
**And** stakeholder lista → apenas published
**And** PATCH requer role analyst

### Story 7.3: Feedback e Dúvidas por Seção do Artefato

As a Felipe,
I want registrar dúvidas em seções específicas do artefato,
So that Ana saiba onde preciso esclarecimento (FR27).

**Acceptance Criteria:**

**Given** ArtifactComment (artifact_id, section_id, user_id, tenant_id, content, type question/feedback, status open/resolved)
**When** Felipe comenta em seção → comentário vinculado, badge numérico
**And** Ana vê comentários, pode marcar "Resolvido"
**And** endpoints: CRUD comments, filtro por seção

### Story 7.4: Re-análise Assistida por IA a partir de Feedback

As a Ana,
I want iniciar re-análise focada no ponto levantado,
So that eu aprofunde requisitos sem recomeçar (FR28, FR29).

**Acceptance Criteria:**

**Given** comentário de stakeholder
**When** "Aprofundar com IA" clicado
**Then** nova sessão com contexto completo + artefato + comentário (FR29)
**And** IA abre com resumo do comentário + perguntas direcionadas
**And** artefato evoluído incrementalmente, nova versão com referência ao comentário (FR30)

### Story 7.5: Notificações de Atualização de Artefatos

As a Felipe,
I want ser notificado quando artefatos atualizam,
So that eu fique informado sem verificar manualmente (FR31).

**Acceptance Criteria:**

**Given** artefato publicado atualizado
**When** mudança salva
**Then** stakeholders recebem notificação (model Notification)
**And** badge no header, dropdown com tipo/título/resumo/data
**And** click → navega para artefato, browser notifications (desktop)

---

## Epic 8: Elicitação Brownfield (Growth/Vision)

Import docs existentes, gap analysis, impacto, conexão repo.

### Story 8.1: Importação de Documentação de Projeto Existente

As a Ana,
I want importar documentação técnica de projeto existente,
So that a IA entenda o que já existe (FR32).

**Acceptance Criteria:**

**Given** projeto com project_type `brownfield`
**When** docs técnicos (README, architecture.md) importados
**Then** parseados e chunked (reutiliza Epic 4), sumário automático gerado
**And** tag document_category: brownfield_docs

### Story 8.2: Elicitação Focada em Gaps e Análise de Impacto

As a Ana,
I want que a sessão foque nos gaps entre existente e desejado,
So that eu não repita requisitos e identifique impactos (FR33, FR34).

**Acceptance Criteria:**

**Given** sessão brownfield com docs
**When** sessão inicia
**Then** Context Builder inclui sumário existente, IA foca em gaps
**And** impacto detectado → IA sinaliza proativamente (FR34)
**And** artefato inclui seções "Áreas de Impacto" e "Requisitos Preservados" (FR35)

### Story 8.3: Conexão a Repositório de Código (Vision)

As a Ana,
I want conectar repositório de código do projeto,
So that a IA analise codebase automaticamente (FR36, FR37).

**Acceptance Criteria:**

**Given** projeto brownfield
**When** URL do repositório fornecida
**Then** sistema analisa: linguagens, frameworks, estrutura, dependências
**And** sumário gerado como documento de referência, disponível no Context Builder
**And** análise assíncrona (processing → ready)

---

## Backlog V2 — Melhorias Identificadas em Testes

### Enhancement: Perfil do Usuário para Personalização da IA

**Origem:** Feedback do primeiro teste manual do Epic 5
**Prioridade:** Alta (impacto direto na experiência)

**Descrição:**
Coletar preferências do usuário para personalizar a interação da IA: nome de exibição, tratamento preferido (Sr./Sra./nenhum), estilo de comunicação (direto vs. detalhado), expertise no domínio e idioma preferido.

**Campos propostos:**

| Campo | Exemplo | Uso pela IA |
|-------|---------|-------------|
| `display_name` | "Glauber" | Como quer ser chamado |
| `honorific` | "Sr." / "Sra." / nenhum | Formalidade |
| `communication_style` | "direto" / "detalhado" | Verbosidade |
| `domain_expertise` | "engenharia de software" | Nível técnico |
| `preferred_language` | "pt-BR" | Idioma |

**Impacto:**
- Novo modelo `UserProfile` (1:1 com `User`)
- Wizard de onboarding pós-primeiro-login
- Context Builder injeta perfil no system prompt
- Tela de settings `/profile`
