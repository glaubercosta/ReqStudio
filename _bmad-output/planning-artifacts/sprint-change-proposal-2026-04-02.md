# Sprint Change Proposal — Epic 5.5: Dívida Técnica e Fundação para Artefatos

**Data:** 2026-04-02  
**Facilitador:** Bob (Scrum Master)  
**Classificação:** Moderate — Backlog reorganization  

---

## 1. Resumo do Problema

**Trigger:** Início do Epic 6 sem que os action items críticos da Retrospectiva do Epic 5 fossem formalizados como stories implementáveis.

**Contexto de descoberta:** Na retro do Epic 5 (2026-03-31), foram identificados 6 action items de alta prioridade que constituem **pré-condições técnicas e de UX** para que o Epic 6 (Artefatos) entregue valor real ao usuário. Esses itens foram documentados informalmente na retro mas nunca inseridos no `sprint-status.yaml` como epic/stories rastreáveis.

**Evidência direta (epic-5-retro-2026-03-31.md, seção 6):**
```
### Pré-condições Técnicas
- [ ] A1: System prompts BMAD-quality (afeta qualidade dos artefatos gerados)
- [ ] A2: Retomar sessão (workflow UX precisa funcionar)
- [ ] A5: Migration automática no startup
```

**Impacto sem correção:** O Epic 6 seria implementado sobre uma base defeituosa — artefatos gerados por uma IA genérica (sem qualidade BMAD), sessões inacessíveis para retomada, e risco de perda de dados por migrações manuais.

---

## 2. Análise de Impacto

### Epic Impact

| Épico | Impacto |
|-------|---------|
| **Epic 5** (done) | Nenhum — o épico está concluído. Epic 5.5 é um retorno intencional e contextualizado para honrar os action items registrados. |
| **Epic 6** (backlog) | Desbloqueado pelo 5.5 — especialmente Story 6.1 depende de A5 (migration) e A1 (qualidade do artefato gerado). |
| **Epics 7 e 8** | Nenhum impacto. |

### Story Impact

Nenhuma story existente é modificada. O Epic 5.5 adiciona 5 novas stories como épico intermediário.

### Artifact Conflicts

| Artefato | Mudança Necessária |
|----------|-------------------|
| `epics.md` | Adicionar Epic 5.5 com 5 stories, após Epic 5 |
| `sprint-status.yaml` | Adicionar seção `epic-5-5` com status `backlog` |

### Technical Impact

- Nenhuma breaking change arquitetural
- A5 (migration automática) resolve risco de dados identificado desde o Epic 2

---

## 3. Abordagem Recomendada

**Opção escolhida:** Direct Adjustment — Inserir Epic 5.5 no plano atual

**Rationale:**
- Escopo contido (5 stories, todos internos)
- Nenhum épico existente é alterado ou renumerado
- A numeração "5.5" contextualiza historicamente que houve uma necessidade de retorno ao Epic 5 antes de avançar
- Baixo risco, alto valor — resolve dívida técnica e gaps de UX antes de construir sobre eles

**Esforço estimado:** Médio (3-5 sessões de dev)  
**Risco:** Baixo

---

## 4. Propostas de Mudança Detalhadas

### 4.1 Adição ao `epics.md`

**Após linha 566 (separador `---` do Epic 5), inserir:**

```markdown
## Epic 5.5: Dívida Técnica e Fundações para Artefatos

Action items críticos da Retrospectiva do Epic 5, formalizados como pré-condições para o Epic 6.
Retorno intencional ao ciclo do Epic 5 para honrar gaps identificados no teste real.

**FRs cobertos:** FR9 (parcial — qualidade da elicitação), FR15 (retomar sessão)
**NFRs cobertos:** NFR12 (telemetria), NFR11 (migrations)
**Origem:** epic-5-retro-2026-03-31.md, Action Items A1–A5

---

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

**Origem:** Retro Epic 5 — Action Item A1 (Crítico)

---

### Story 5.5-2: Retomar Sessão Existente na ProjectDetailPage

As a Ana,
I want que ao acessar meu projeto o sistema detecte sessões em andamento e me ofereça continuar,
So that eu retome de onde parei sem criar uma sessão nova desnecessariamente (FR15, FR4).

**Acceptance Criteria:**

**Given** rota `/projects/{id}` com sessão `active` ou `paused` existente
**When** ProjectDetailPage renderiza
**Then** `GET /api/v1/projects/{id}/sessions?status=active,paused` retorna sessões existentes
**And** se existir sessão → botão \"Continuar sessão\" → navega para `/sessions/{session_id}`
**And** se não existir → botão \"Iniciar elicitação\" → cria nova sessão
**And** WelcomeScreen exibe: última interação, % cobertura atual, próximo passo
**And** `progress_summary` do projeto atualizado pelo Elicitation Engine após cada mensagem
**And** testes: detecção ativa, detecção pausada, fallback sem sessão, progress_summary atualizado

**Origem:** Retro Epic 5 — Action Item A2 (Alta)

---

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

**Origem:** Retro Epic 5 — Action Items A5 (Alta) + A6 (Média)

---

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
**And** status inline no chat: \"📄 Processando contrato.pdf...\" → \"✅ Pronto — adicionado ao contexto\"
**And** próxima mensagem do usuário já tem o doc available no Context Builder
**And** erro → Guided Recovery inline (sem modal): \"Arquivo muito grande. Tente um PDF menor.\"
**And** testes: upload sucesso, erro MIME, erro tamanho, injeção no contexto, mobile fallback

**Origem:** Retro Epic 5 — Action Item A3 (Média)

---

### Story 5.5-5: Telemetria Baseline — Tokens e Custo por Mensagem

As a Ana,
I want ver quanto a sessão está consumindo de IA em tempo real,
So that eu tenha transparência sobre o uso e custo da plataforma (NFR12).

**Acceptance Criteria:**

**Given** mensagem enviada e resposta finalizada (chunk `done: true`)
**When** Elicitation Engine salva resposta
**Then** colunas `input_tokens`, `output_tokens`, `cost_usd`, `model` salvas na tabela `messages` (role=assistant)
**And** mini-widget visível no header da SessionPage: \"💰 $0.02 · 1.2k tokens\"
**And** tooltip expandido: input tokens, output tokens, modelo usado, latência
**And** sem sessão ativa: widget oculto
**And** testes: persistência das métricas, widget renderizado, tooltip com breakdown, modelo correto

**Origem:** Retro Epic 5 — Action Item A4 (Média)
```

### 4.2 Adição ao `sprint-status.yaml`

**Inserir nova seção entre epic-5 e epic-6:**

```yaml
  # ═══════════════════════════════════════════════════
  # Epic 5.5: Dívida Técnica e Fundações para Artefatos
  # (Action items da Retro Epic 5 — pré-condições para Epic 6)
  # ═══════════════════════════════════════════════════
  epic-5-5: backlog
  5-5-1-system-prompts-bmad-quality: backlog
  5-5-2-retomar-sessao-projectdetailpage: backlog
  5-5-3-migration-automatica-startup: backlog
  5-5-4-upload-documento-chatinput: backlog
  5-5-5-telemetria-baseline-tokens-custo: backlog
  epic-5-5-retrospective: optional
```

---

## 5. Handoff de Implementação

**Escopo:** Moderate — Inserção de épico intermediário com reorganização mínima de backlog

**Handoff:**
| Papel | Responsabilidade |
|-------|-----------------|
| **Scrum Master (Bob)** | Atualizar `epics.md` e `sprint-status.yaml` após aprovação |
| **Dev (Amelia)** | Implementar stories na sequência: 5.5-3 → 5.5-2 → 5.5-1 → 5.5-4 → 5.5-5 (infra first) |
| **PO (Alice)** | Revisar system prompts da Story 5.5-1 junto com o Arquiteto |

**Sequência de implementação recomendada:**
1. **5.5-3** (migration) — desbloqueia tudo, resolve risco imediato
2. **5.5-2** (retomar sessão) — restaura UX essencial
3. **5.5-1** (system prompts) — eleva qualidade do produto antes dos artefatos
4. **5.5-4** (upload no chat) — fluxo completo de importação mid-session
5. **5.5-5** (telemetria) — visibilidade e NFR12

**Critérios de sucesso:**
- `docker-compose up` do zero sobe sem intervenção manual
- Ana consegue retomar sessão existente ao abrir projeto
- Primeira resposta da IA demonstra personalidade e técnicas de elicitação
- Upload de doc funciona via botão 📎 no chat
- Mini-widget de custo visível no header da sessão

---

*Gerado em: 2026-04-02 | Correct Course Workflow | Bob (Scrum Master)*
