# Story 7.2: Transição de Etapa e Resumo Automático

Status: done

## Story

As a usuário em sessão de elicitação,
I want que Mary sinalize explicitamente quando uma etapa é concluída e qual vem a seguir,
so that eu sinta o progresso e saiba o objetivo do próximo bloco (FR44, FR45).

## Acceptance Criteria

1. **Mensagem de transição gerada ao avançar de etapa (steps 1–4)**
Given sessão em andamento com step N concluído (N < 5)
When `_advance_workflow` executa a transição step N → step N+1
Then backend gera mensagem de transição chamando o LLM com `TRANSITION_TEMPLATE`
And mensagem é persistida como `role="assistant"` na sessão com o próximo `message_index`
And conteúdo declara o que foi alcançado na etapa N e anuncia o objetivo da etapa N+1
And tom é direto e energizante, sem bajulação

2. **Resumo de 1 linha armazenado em `step_summaries`**
Given mensagem de transição gerada para step N
When backend processa a resposta do LLM
Then extrai resumo de 1 linha da linha prefixada com `[RESUMO]:` na resposta
And armazena em `workflow_position.step_summaries[str(N)]`
And `workflow_position` atualizado é persistido junto com a sessão

3. **Mensagem de conclusão ao encerrar step 5**
Given sessão no step 5 (último)
When `_advance_workflow` marca `session.status = "completed"`
Then backend gera mensagem de encerramento com `COMPLETION_TEMPLATE` (não transição)
And mensagem inclui síntese de todas as etapas concluídas
And `step_summaries["5"]` armazenado com resumo da última etapa

4. **Invariante: mensagem de transição APÓS advance do step counter**
Given processo de advance
When step counter é incrementado
Then mensagem de transição referencia o step JÁ avançado (novo step atual, não anterior)
And `workflow_position.current_step` já contém N+1 no momento da chamada LLM

5. **Idempotência — sem mensagem de transição no kickstart**
Given função `kickstart()` da Story 7.1
When kickstart é executado
Then `_advance_workflow` NÃO é chamado (kickstart não persiste resposta como par elicitação)
And `step_summaries` permanece ausente/vazio após kickstart

6. **Cobertura de testes ≥ 80%**
Given implementação concluída
When suíte relevante executada
Then `_advance_workflow` coberto por testes que verificam mensagem persistida e step_summaries
And mock de `stream_completion` usado em todos os testes de transição (sem chamada LLM real)

## Tasks / Subtasks

- [x] Task 1: Seed — templates de transição em `seed_workflows.py` (AC: 1, 2, 3)
  - [x] Adicionar `STEP_NAMES` dict: `{1: "Contexto", 2: "Usuários e stakeholders", 3: "Objetivos de negócio", 4: "Processo atual", 5: "Restrições"}`
  - [x] Adicionar `TRANSITION_TEMPLATE` com instrução para Mary
  - [x] Adicionar `COMPLETION_TEMPLATE` para step 5 (encerramento completo)

- [x] Task 2: Engine — modificar `_advance_workflow()` em `elicitation.py` (AC: 1, 2, 3, 4)
  - [x] Importar `TRANSITION_TEMPLATE`, `COMPLETION_TEMPLATE`, `STEP_NAMES`, `SEED_AGENT` de `seed_workflows`
  - [x] Ao avançar step N → N+1: incrementa primeiro, chama LLM, extrai [RESUMO]:, persiste mensagem
  - [x] Ao concluir último step: gera mensagem de conclusão, armazena step_summaries, status=completed
  - [x] Adicionado helper `_extract_summary(response)` com fallback de 120 chars
  - [x] `session.workflow_position = new_position` (reatribuição forçada para SQLAlchemy)

- [x] Task 3: Testes em `test_advance_workflow_transition.py` (AC: 1, 2, 3, 6)
  - [x] `test_advance_workflow_persists_transition_message`: step 1 → 2, verifica 3 mensagens e [RESUMO]:
  - [x] `test_advance_workflow_stores_step_summary`: verifica `step_summaries["1"]` e `current_step=2`
  - [x] `test_advance_workflow_step_counter_increments_before_llm`: verifica AC 4 (counter antes do LLM)
  - [x] `test_advance_workflow_completion_step5`: status=completed, step_summaries, mensagem de conclusão
  - [x] `test_extract_summary_with_tag`, `test_extract_summary_fallback`, `test_extract_summary_empty`
  - [x] `test_kickstart_nao_popula_step_summaries`: AC 5 — kickstart não chama _advance_workflow
  - [x] Testes regressivos atualizados: `test_elicit_full_pipeline` e `test_kickstart_sessao_com_mensagens_retorna_409`

## Dev Notes

### O que muda na `_advance_workflow()`

Atualmente (elicitation.py:165–200) `_advance_workflow` apenas:
1. Lê `workflow_position.current_step`
2. Conta total de steps
3. Incrementa ou marca `completed=True`

Após esta story, `_advance_workflow` também:
1. Chama LLM para gerar mensagem de transição
2. Extrai e armazena resumo em `step_summaries`
3. Persiste mensagem como `role="assistant"`

**Ordem crítica (AC 4)**: incrementar `current_step` ANTES de chamar LLM, para que o prompt possa referenciar "etapa N concluída → etapa N+1 começa" com os nomes corretos.

### Chamada LLM dentro de `_advance_workflow`

`stream_completion` já é importado em `elicitation.py`. Para a chamada de transição, montar `messages` mínimo:
```python
messages = [
    {"role": "system", "content": SEED_AGENT["system_prompt"]},
    {"role": "user", "content": TRANSITION_TEMPLATE.format(
        completed_step_num=current_step,
        completed_step_name=STEP_NAMES[current_step],
        next_step_num=current_step + 1,
        next_step_name=STEP_NAMES.get(current_step + 1, ""),
    )},
]
```

Acumular resposta completa sem yield (o cliente SSE já está processando o último chunk do elicit principal):
```python
full_transition = ""
async for chunk in stream_completion(messages):
    full_transition += chunk.content
```

### Parsing do `[RESUMO]:` tag

Formato esperado na resposta do LLM (instruído pelo TRANSITION_TEMPLATE):
```
[RESUMO]: Sistema de gestão de estoque para rede de 15 farmácias captado com clareza
 
Excelente progresso! Mapeamos o contexto central do projeto...
```

Extração:
```python
def _extract_summary(response: str) -> str:
    first_line = response.strip().splitlines()[0] if response.strip() else ""
    if first_line.startswith("[RESUMO]:"):
        return first_line[len("[RESUMO]:"):].strip()
    return response.strip()[:120]  # fallback
```

### SQLAlchemy JSON mutation detection

`workflow_position` é um campo JSON. SQLAlchemy não detecta mutações em dicts aninhados automaticamente. Sempre reatribuir o objeto completo:
```python
new_position = dict(session.workflow_position or {})
new_position["current_step"] = current_step + 1
new_position.setdefault("step_summaries", {})[str(current_step)] = summary
session.workflow_position = new_position  # reatribuição forçada
```

Isso é diferente de `session.workflow_position["key"] = value` que SQLAlchemy não rastreia.

### `step_summaries` schema

Adicionado ao JSON existente de `workflow_position` — sem migração de banco necessária (campo JSON já existente). Exemplo de estado após 2 etapas:
```json
{
  "current_step": 3,
  "step_summaries": {
    "1": "Sistema de gestão de estoque para rede de farmácias — contexto inicial mapeado",
    "2": "Usuários: atendentes de balcão e gerentes de estoque; JTBD: garantir disponibilidade sem excesso"
  }
}
```

### Frontend — sem mudanças nesta story

A mensagem de transição é persistida no backend e aparece na lista de mensagens quando TanStack Query invalida após o `done` SSE do elicit principal (comportamento existente em `useSession.ts`). A Story 7.4 (painel lateral) consome `step_summaries` via API de sessão — fora do escopo desta story.

### Arquivos a tocar

| Arquivo | Mudança |
|---------|---------|
| `reqstudio-api/app/seeds/seed_workflows.py` | Adicionar `STEP_NAMES`, `TRANSITION_TEMPLATE`, `COMPLETION_TEMPLATE` |
| `reqstudio-api/app/modules/engine/elicitation.py` | Modificar `_advance_workflow()`, adicionar `_extract_summary()` |
| `reqstudio-api/app/modules/engine/tests/test_advance_workflow_transition.py` | Testes novos |

### Impacto na Story 7.1 (kickstart)

A função `kickstart()` da Story 7.1 NÃO chama `_advance_workflow`. O kickstart apenas:
1. Chama LLM com `KICKSTART_TEMPLATE`
2. Persiste resposta como `role="assistant"`, `message_index=0`
3. NÃO avança step, NÃO gera transição

Esta story (7.2) modifica `_advance_workflow`, que é chamado APENAS dentro de `elicit()` no par user+assistant. As duas stories são independentes no código.

### References

- [elicitation.py:165](reqstudio/reqstudio-api/app/modules/engine/elicitation.py#L165) — `_advance_workflow()` atual a modificar
- [elicitation.py:109-148](reqstudio/reqstudio-api/app/modules/engine/elicitation.py#L109) — loop SSE com padrão de acumulação de `full_response`
- [seed_workflows.py:117](reqstudio/reqstudio-api/app/seeds/seed_workflows.py#L117) — `SEED_STEPS` com step names implícitos
- [seed_workflows.py:21](reqstudio/reqstudio-api/app/seeds/seed_workflows.py#L21) — `SEED_AGENT` com system_prompt para usar nos messages de transição
- [test_progress_summary.py](reqstudio/reqstudio-api/app/modules/engine/tests/test_progress_summary.py) — padrão de mock para testes do engine
- Story 7.1: [7-1-kickstart-projeto-mensagem-inicial-mary.md](_bmad-output/implementation-artifacts/7-1-kickstart-projeto-mensagem-inicial-mary.md)
- [project-context.md](project-context.md) — GuidedRecoveryError, TenantScope, convenções de teste

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6 (Amelia — bmad-agent-dev)

### Debug Log References

- Ruff I001 import sort: imports de `seed_workflows` separados em blocos individuais após `ruff --fix`
- Ruff E501 em `COMPLETION_TEMPLATE`: linha encurtada substituindo "no máximo 15 palavras" por frase menor
- Testes regressivos (`test_elicit_full_pipeline`, `test_kickstart_sessao_com_mensagens_retorna_409`): `seed_workflows` tem 1 step → completion path gerava 3ª mensagem; asserções atualizadas de `== 2` para `== 3`

### Completion Notes List

- `_advance_workflow` agora chama LLM internamente para gerar mensagem de transição (step N→N+1) ou conclusão (último step)
- Ordem AC 4 respeitada: `current_step` incrementado ANTES de chamar o LLM
- Reatribuição `session.workflow_position = new_position` força detecção de mutação JSON no SQLAlchemy
- `_extract_summary` helper público (importável em testes) extrai tag `[RESUMO]:` ou retorna fallback de 120 chars
- 202 testes passando (zero regressões)

### File List

- `reqstudio/reqstudio-api/app/seeds/seed_workflows.py` — adicionados `STEP_NAMES`, `TRANSITION_TEMPLATE`, `COMPLETION_TEMPLATE`
- `reqstudio/reqstudio-api/app/modules/engine/elicitation.py` — `_advance_workflow()` reescrito + `_extract_summary()` adicionado
- `reqstudio/reqstudio-api/tests/test_advance_workflow_transition.py` — 8 novos testes (todos passando)
- `reqstudio/reqstudio-api/tests/test_elicitation.py` — asserção `len(messages)` atualizada para 3
- `reqstudio/reqstudio-api/tests/test_elicitation_kickstart.py` — asserção `len(messages)` atualizada para 3

### Review Findings

- [x] [Review][Defer] COMPLETION_TEMPLATE — design ambíguo: LLM é instruído a sintetizar 5 etapas mas recebe summaries 1..N-1 apenas; etapa N nunca tem transcript no prompt [elicitation.py:440-460] — deferred, requer reavaliação com PM antes de decidir abordagem
- [x] [Review][Patch] AC 4 — persistência atômica: reescrever `_advance_workflow` para fazer `session.workflow_position = new_position` + `await scope.db.commit()` ANTES de `stream_completion(...)`, e a mensagem de transição é commitada em segundo commit ao final do stream (decidido: AC exige estado persistido N+1 antes do LLM) [elicitation.py:295-410] — aplicado
- [x] [Review][Patch] `_advance_workflow` LLM stream errors deixam estado inconsistente: user msg salvo, transition msg parcial pode persistir, step não avança; envolver em try/except com rollback explícito [elicitation.py:295-410] — aplicado: `try/except` em ambos os ramos com `logger.exception` + re-raise; step advance já é persistido antes do LLM (AC 4) então não há estado parcial
- [x] [Review][Patch] Resumo do LLM sem cap de tamanho: extração via `[RESUMO]:` retorna texto bruto pós-tag; LLM runaway pode armazenar 50KB no JSON column [elicitation.py:411-413] — aplicado: `_SUMMARY_MAX_CHARS = 200`
- [x] [Review][Patch] Test `test_advance_workflow_step_counter_increments_before_llm` usa `or "2"` na asserção — disjunção trivializa o teste; AC 4 não é verificada [test_advance_workflow_transition.py:1432-1452] — aplicado: assert exige `"Usuários e stakeholders"` no prompt
- [x] [Review][Patch] `_extract_summary` parser frágil: falha com whitespace antes do tag, markdown wrapping, smart quotes; sem telemetria de fallback rate [elicitation.py:405-413] — aplicado: busca em qualquer linha, `_normalize_summary_line` tolera markdown `**`/`*`
- [x] [Review][Patch] Mensagem de transição visível ao usuário contém o tag interno `[RESUMO]:`; tag deve ser stripado antes de persistir como `content` [elicitation.py:343] — aplicado via `_strip_summary_tag()`; testes ajustados (contrato invertido)
- [x] [Review][Patch] `_advance_workflow` usa `_SEED_AGENT["system_prompt"]` direto, bypassando `_load_agent_system_prompt()` (DB-loaded) usado por kickstart/return_greeting — inconsistência [elicitation.py:389] — aplicado
- [x] [Review][Defer] Engine importa de `app.seeds.seed_workflows` (6 imports separados após ruff): cheiro arquitetural, mover templates para módulo `prompts` próprio [elicitation.py:75-96] — deferred, refatoração não-bloqueante
- [x] [Review][Defer] Persona "Mary" hard-coded em 3 locais (`_load_agent_system_prompt` fallback + `_SEED_AGENT`); rename de agente quebraria silenciosamente — deferred, DRY pequeno
- [x] [Review][Defer] `status_code=409` em `GuidedRecoveryError` é metadata morto para rotas SSE (sempre retornam 200 com event:error); clarificar contrato [exceptions.py:28-29] — deferred, contrato API
