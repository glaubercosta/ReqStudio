# Story 5.5-1: System Prompts com Qualidade BMAD Real

Status: done

## Story

As a Ana (especialista de domínio),
I want que a IA conduza a sessão com personalidade, técnicas de elicitação e regras claras,
so that eu perceba diferença real entre o ReqStudio e um chatbot genérico.

## Acceptance Criteria

1. **Given** seed data de Agents e WorkflowSteps no banco  
   **When** sessão de elicitação inicia  
   **Then** system prompt do agente contém persona definida, técnicas de elicitação (5 Whys, cenários negativos, JTBD), regras de verbosidade (máx 3 perguntas por turno) e pelo menos 2 exemplos few-shot de boas respostas

2. **Given** a sessão está na Fase 1 (contextualização)  
   **When** a IA responde à narrativa inicial do usuário  
   **Then** o tom é de ouvinte ativo — a resposta demonstra compreensão específica do domínio do usuário, sem bullet points desnecessários, sem repetir o que foi dito

3. **Given** a sessão está na Fase 2 (guiada)  
   **When** a IA faz perguntas estruturadas  
   **Then** cada step vai além de uma pergunta genérica: desafia com evidência dos docs importados, aponta inconsistência ou lacuna, e abre espaço explícito para o usuário expandir

4. **Given** o system prompt é carregado pelo Elicitation Engine  
   **When** `build_context()` é chamado  
   **Then** o `system_prompt` do Agent injetado tem comprimento > 800 chars (verificável em teste)

5. **Given** o re-seed é executado com `--force`  
   **When** `python -m app.seeds.seed_workflows --force`  
   **Then** o seed substitui o prompt antigo pelo novo sem deixar dados órfãos

## Tasks / Subtasks

- [x] **Task 1: Reescrever o `system_prompt` do Agent Mary no seed** (AC: 1, 2, 4)
  - [x] Definir persona completa: nome, papel, tom, estilo de comunicação
  - [x] Incluir regras de verbosidade explícitas (máx 3 perguntas, parágrafos curtos)
  - [x] Adicionar instruções para Fase 1 (ouvinte ativo, sem interromper)
  - [x] Adicionar instruções para Fase 2 (desafiar com evidência, técnicas de elicitação)
  - [x] Incluir pelo menos 2 exemplos few-shot no formato turno user/assistant
  - [x] Validar comprimento > 800 chars

- [x] **Task 2: Reescrever os `prompt_template` dos WorkflowSteps no seed** (AC: 3)
  - [x] Step 1: abrir com resumo dos docs (se houver) OU pergunta acolhedora de domínio
  - [x] Step 2: aprofundar usuários afetados com JTBD — "O que eles estão tentando realizar?"
  - [x] Step 3: explorar resultado de negócio + impacto se não resolver
  - [x] Step 4: mapear processo atual com técnica dos cenários extremos (melhor/pior caso)
  - [x] Step 5: identificar restrições com validação por contraponto — "E se X não fosse possível?"

- [x] **Task 3: Adicionar instrução de transição entre fases no Engine** (AC: 2, 3)
  - [x] Verificar em `elicitation.py` onde a transição de fase é sinalizada
  - [x] Garantir que o system prompt inclua instrução explícita de como sinalizar Fase 2

- [x] **Task 4: Atualizar testes do seed** (AC: 5)
  - [x] Verificar se existe teste para `seed_workflows.py`
  - [x] Adicionar/atualizar teste que valida: prompt length > 800, keywords de personalidade presentes, few-shot examples no formato correto

## Dev Notes

### Causa Raiz Documentada (Retro Epic 5 — Gap 3.1)

O arquivo atual `reqstudio/reqstudio-api/app/seeds/seed_workflows.py` contém:

**System prompt atual (3 linhas genéricas — INSUFICIENTE):**
```python
SEED_AGENT = {
    "system_prompt": (
        "Você é Mary, analista de requisitos. Conduza a elicitação de forma "
        "objetiva e empática. Seja concisa: perguntas curtas e diretas, "
        "respostas de no máximo 3 parágrafos. Fale em português do Brasil. "
        "Nunca chame o usuário de 'especialista' — use o nome dele."
    ),
}
```

**Steps atuais (5 perguntas genéricas sem profundidade):**
```python
SEED_STEPS = [
    {"position": 1, "prompt_template": "Me conte em poucas frases: qual problema seu projeto resolve? Quem é afetado?"},
    {"position": 2, "prompt_template": "Quem são os usuários principais? Algum outro grupo é afetado?"},
    ...
]
```

**Causa raiz:** Sem personalidade real, sem técnicas de elicitação, sem few-shot examples → IA genérica e verbosa.

### Referência: Skills BMAD como Inspiração

Os agents BMAD reais (ex: `bmad-agent-pm`, `bmad-agent-analyst`) têm 800+ linhas de definição de persona, técnicas, regras e exemplos. O dev DEVE ler os arquivos em:
- `c:\Users\Glauber\codes\ReqStudio\.agent\skills\bmad-agent-analyst\SKILL.md`
- `c:\Users\Glauber\codes\ReqStudio\.agent\skills\bmad-agent-pm\SKILL.md`

Especificamente: tom de comunicação, técnicas de elicitação usadas, regras de verbosidade, e como os exemplos few-shot são estruturados.

### Arquivo Principal a Modificar

**`reqstudio/reqstudio-api/app/seeds/seed_workflows.py`** — este é o único arquivo de produção a ser alterado.

### Estrutura do System Prompt BMAD-Quality (Referência)

O novo `system_prompt` deve ter as seguintes seções:

```
## Identidade e Papel
[Nome, papel, missão, o que NÃO fazer]

## Princípios de Comunicação
[Tom, linguagem, tamanho de respostas, regras de verbosidade]

## Técnicas de Elicitação
[5 Whys, JTBD, cenários negativos, contraponto, abertura para expandir]

## Fase 1 — Contextualização (Usuário como Narradora)
[Como ouvir ativamente, como demonstrar compreensão, quando NÃO perguntar]

## Fase 2 — Descoberta Guiada (IA como Facilitadora)
[Como fazer perguntas estruturadas, como desafiar com evidência dos docs]

## Exemplos Few-Shot
[2+ exemplos concretos de turno user/assistant bem executado]

## Restrições
[O que nunca fazer: não ser genérica, não repetir, não usar jargão técnico]
```

### Instrução de Transição entre Fases

Em `reqstudio/reqstudio-api/app/modules/engine/elicitation.py`, verificar como o `workflow_position` avança e onde o Elicitation Engine decide passar do Step 1-2 (Fase 1) para os steps seguintes (Fase 2). A instrução de transição deve estar no system prompt, não no código.

### Convenções de Código a Seguir (project-context.md)

- Ler `reqstudio/reqstudio-api/app/modules/sessions/` antes de modificar qualquer coisa no engine — para absorver padrões locais
- Todas as strings longas em Python: usar parênteses `(...)` com concatenação implícita ou triple-quotes `"""`
- O seed usa `asyncio.run()` — manter essa estrutura
- Para re-seed com `--force`: verificar que a deleção cascateada de `WorkflowStep` antes do `Workflow` é feita corretamente (já existe no código atual — não quebrar)

### Arquivo de Teste de Referência

Antes de escrever/modificar testes, leia:  
`reqstudio/reqstudio-api/app/modules/sessions/tests/` — para absorver o padrão de testes do projeto.

O teste do seed deve verificar:
- `len(agent.system_prompt) > 800`
- `"5 Whys" in agent.system_prompt or "cenário" in agent.system_prompt.lower()`
- `len(steps) == 5`
- Cada `step.prompt_template` tem mais de 100 chars (profundidade mínima)

### Project Structure Notes

- **Arquivo seed:** `reqstudio/reqstudio-api/app/seeds/seed_workflows.py`
- **Engine que usa o seed:** `reqstudio/reqstudio-api/app/modules/engine/elicitation.py`
- **Modelos do seed:** `reqstudio/reqstudio-api/app/modules/workflows/models.py` (Agent, Workflow, WorkflowStep)
- **Testes (criar se não existir):** `reqstudio/reqstudio-api/app/seeds/tests/test_seed_workflows.py`

### References

- [Source: epics.md — Story 5.5-1]
- [Source: epic-5-retro-2026-03-31.md — Gap 3.1 e Action Item A1]
- [Source: architecture.md — Seção "Implementation Patterns", seed data como entidades]
- [Source: project-context.md — Seção 5, Quartet Pattern]
- [Source: seeds/seed_workflows.py — código atual com stubs a serem reescritos]

## Dev Agent Record

### Agent Model Used

Claude Sonnet 4.6 (Thinking) via Antigravity — 2026-04-02

### Debug Log References

- Nenhum bloqueador encontrado. Engine (`elicitation.py`) não precisou de mudanças — a instrução de transição de fase pertence ao system_prompt, não ao código.
- O diretório `app/seeds/tests/` foi criado (não existia). O `pyproject.toml` já inclui `testpaths = ["tests", "app"]`, então os novos testes são descobertos automaticamente.
- `conftest.py` dos testes de integração do seed não foi necessário — os fixtures foram criados inline no arquivo de teste.

### Completion Notes List

- Origem: Epic 5.5 — Correct Course workflow (2026-04-02)
- Contexto: Action Item A1 da Retro do Epic 5 — gap mais crítico identificado no teste real do produto
- **Task 1 (AC: 1, 2, 4):** `SEED_AGENT.system_prompt` reescrito com 7 seções: Identidade, Princípios de Comunicação, Técnicas de Elicitação (5 Whys, JTBD, Cenários Extremos, Contraponto, Evidência dos Documentos), Fase 1, Fase 2, Exemplos Few-Shot (2 exemplos), Restrições. Comprimento: ~4.500+ chars (muito acima dos 800 exigidos).
- **Task 2 (AC: 3):** 5 `prompt_template` reescritos com profundidade real. Step 1: abertura adaptativa (docs ou narrativa livre). Step 2: JTBD. Step 3: impacto negativo + métricas. Step 4: cenários extremos + referência a documentos. Step 5: técnica do contraponto.
- **Task 3 (AC: 2, 3):** Verificado `elicitation.py` — a lógica de `_advance_workflow` é puramente posicional (step+1 por turno). A instrução de transição foi inserida no system_prompt (seção Fase 1: "Ao concluir o Step 2, sinalize sutilmente a transição..."). Nenhuma mudança de código no engine necessária.
- **Task 4 (AC: 5):** Criado `app/seeds/tests/test_seed_workflows.py` com 12 testes: 9 estáticos (validam qualidade BMAD sem DB) + 3 de integração (insert, idempotência sem --force, re-seed com --force).

### Change Log

- 2026-04-02: Reescrita completa de `SEED_AGENT.system_prompt` com qualidade BMAD-real (Story 5.5-1)
- 2026-04-02: Reescrita completa dos 5 `SEED_STEPS.prompt_template` com técnicas de elicitação (JTBD, 5 Whys, Cenários Extremos, Contraponto)
- 2026-04-02: Criado `app/seeds/tests/test_seed_workflows.py` com cobertura completa dos ACs

### File List

- `reqstudio/reqstudio-api/app/seeds/seed_workflows.py` (MODIFY)
- `reqstudio/reqstudio-api/app/seeds/tests/__init__.py` (CREATE)
- `reqstudio/reqstudio-api/app/seeds/tests/test_seed_workflows.py` (CREATE)

### Review Findings

- [x] [Review][Patch] Substituir `print()` por chamadas ao `logger` já instanciado [app/seeds/seed_workflows.py:182]
- [x] [Review][Defer] A deleção forçada de Agent poderá quebrar FK se for compartilhado no futuro [app/seeds/seed_workflows.py:200] — deferred, edge case futuro
