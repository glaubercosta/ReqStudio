# Story 7.4: Painel Lateral de Progresso da Sessão

Status: ready-for-dev

## Story

As a usuário em sessão de elicitação,
I want visualizar o progresso das 5 etapas em tempo real no painel lateral,
so that eu sinta o trabalho evoluir e consulte o que foi capturado em cada etapa (FR46).

## Acceptance Criteria

1. **Painel lista 5 etapas com indicação visual de estado**
Given sessão ativa em qualquer etapa
When painel de progresso está no estado expandido
Then 5 etapas são listadas com seus nomes
And etapas concluídas (step < current_step) são exibidas com cor intensa (`var(--rs-success)` ou `var(--rs-primary)`)
And etapa atual (`step == current_step`) é destacada com fundo suave (`var(--rs-primary-light)`)
And etapas pendentes (step > current_step) são exibidas com cor esmaecida (`var(--rs-text-muted)`)

2. **Resumo de 1 linha visível para etapas concluídas**
Given painel expandido
When há etapas concluídas com `step_summaries` no `workflow_position`
Then cada etapa concluída exibe seu resumo de 1 linha abaixo do nome
And clique no resumo expande o texto completo (toggle por etapa)

3. **Painel é recolhível**
Given painel no estado expandido
When usuário clica no botão de toggle (ícone ×/☰ ou seta)
Then painel recolhe com animação suave (CSS transition)
And ao recolher: somente ícones/indicadores coloridos permanecem visíveis (versão compacta)
And clique novamente: painel expande

4. **Atualização reativa ao concluir etapa**
Given painel aberto durante sessão ativa
When frontend recebe evento SSE `done` do elicit (TanStack Query invalida `['session', sessionId]`)
Then painel reflete novo `workflow_position.current_step` e novo `step_summaries` automaticamente
And nenhum refresh manual necessário

5. **Substituição da barra de progresso atual**
Given SessionPage com o painel de progresso linear atual (data-testid="session-progress-panel")
When painel lateral é implementado
Then a barra de progresso linear DEVE SER REMOVIDA do header do chat
And todo o estado visual de progresso passa a ser responsabilidade do novo painel lateral
And a informação "Etapa N de 5" / percentual ainda é acessível via painel lateral expandido

6. **Responsividade — mobile**
Given viewport < 1024px (mobile)
When painel de progresso está em modo mobile
Then painel é acessível via botão toggle no header do chat (ícone de progresso)
And ao clicar: painel aparece como overlay ou accordion abaixo do header
And clique fora do painel ou no botão toggle: fecha

7. **Cobertura de testes ≥ 80%**
Given implementação concluída
When suíte relevante executada
Then `SessionProgressPanel` coberto por testes que verificam:
  - Renderização das 5 etapas com classes corretas por estado
  - Toggle de expandir/recolher
  - Exibição de step_summaries quando presentes

## Tasks / Subtasks

- [ ] Task 1: Novo componente `SessionProgressPanel.tsx` (AC: 1, 2, 3, 6)
  - [ ] Criar `reqstudio-ui/src/components/chat/SessionProgressPanel.tsx`
  - [ ] Props:
    ```typescript
    interface SessionProgressPanelProps {
      currentStep: number          // workflow_position.current_step
      totalSteps: number           // 5
      stepNames: string[]          // ELICITATION_STEPS
      stepSummaries: Record<string, string>  // workflow_position.step_summaries ?? {}
      isCompleted: boolean         // session.status === 'completed'
      isCollapsed: boolean
      onToggleCollapse: () => void
    }
    ```
  - [ ] Estado por etapa: `done` (step < currentStep), `active` (step === currentStep), `pending` (step > currentStep)
  - [ ] Versão expandida: lista vertical com nome + resumo por etapa concluída
  - [ ] Versão recolhida: lista compacta de dots/ícones coloridos por estado
  - [ ] Toggle de resumo individual: `expandedSummaries: Set<number>` (estado local)
  - [ ] Animação: `transition-all duration-200` para expand/collapse
  - [ ] Usar `var(--rs-success)` para etapas concluídas, `var(--rs-primary)` com fundo `var(--rs-primary-light)` para etapa atual, `var(--rs-text-muted)` para pendentes

- [ ] Task 2: Integração em `SessionPage.tsx` (AC: 4, 5, 6)
  - [ ] Adicionar estado `isProgressPanelCollapsed: boolean` (default: `false` — expandido por padrão)
  - [ ] Adicionar `stepSummaries` derivado de `session?.workflow_position?.step_summaries ?? {}`
  - [ ] Em `SessionChatPanel` props: adicionar `stepSummaries`, `isProgressPanelCollapsed`, `onToggleProgressPanel`
  - [ ] Dentro de `SessionChatPanel`: substituir o bloco `data-testid="session-progress-panel"` (linhas 197-219 do SessionPage.tsx) pelo `<SessionProgressPanel>` no lugar adequado
  - [ ] Layout desktop: painel lateral à ESQUERDA do chat, posicionado entre o header do chat e a área de mensagens — largura 220px expandido, 40px recolhido
  - [ ] Layout mobile: botão toggle no header do chat, painel aparece como accordion acima das mensagens
  - [ ] Atualização reativa: `stepSummaries` já é reativo via `session?.workflow_position` (TanStack Query atualiza `['session', sessionId]` após cada `done` SSE)

- [ ] Task 3: Testes em `SessionProgressPanel.test.tsx` (AC: 7)
  - [ ] `test_renders_5_steps_with_names`: verifica que todas as etapas aparecem com nomes corretos
  - [ ] `test_step_states_visual`: etapa concluída tem data-state="done", atual="active", pendente="pending"
  - [ ] `test_toggle_collapse`: clicar no botão alterna `isCollapsed`
  - [ ] `test_shows_summary_for_completed_steps`: com `stepSummaries={"1": "resumo"}`, verifica texto visível
  - [ ] `test_expand_summary_on_click`: clique no resumo expande o conteúdo
  - [ ] `test_completed_session_all_done`: `isCompleted=true` → todas as 5 etapas no estado `done`

## Dev Notes

### Layout atual vs. novo

**Atual** (`SessionChatPanel` em `SessionPage.tsx`):
```
┌─────────────────────────────────────────────┐
│ Header (voltar, nome projeto, status)        │
├─────────────────────────────────────────────┤
│ Progress bar linear (linhas 197-219)        │  ← REMOVER
├─────────────────────────────────────────────┤
│ Área de mensagens (scroll)                  │
├─────────────────────────────────────────────┤
│ ChatInput                                   │
└─────────────────────────────────────────────┘
```

**Novo (desktop)**:
```
┌──────────────────────────────────────────────────────────┐
│ Header (voltar, nome projeto, status)                    │
├───────────────┬──────────────────────────────────────────┤
│ Progress Panel│ Área de mensagens (scroll)               │
│ (220px ou 40px│                                          │
│  recolhido)   │                                          │
├───────────────┴──────────────────────────────────────────┤
│ ChatInput (largura total)                               │
└──────────────────────────────────────────────────────────┘
```

**Mobile**: botão no header abre accordion/overlay sobre mensagens.

### `ELICITATION_STEPS` já existe em `SessionPage.tsx`

```typescript
// SessionPage.tsx:25–31
const ELICITATION_STEPS = [
  'Contexto',
  'Usuários e stakeholders',
  'Objetivos de negócio',
  'Processo atual',
  'Restrições',
]
```

Esse array deve ser passado como `stepNames` prop para `SessionProgressPanel`. Não duplicar — importar ou passar via prop.

### `workflow_position` no frontend

O `session.workflow_position` já é retornado pelo endpoint `GET /sessions/{id}` (campo JSON no modelo Session). O tipo no frontend está sendo usado como `Record<string, unknown>` em `SessionChatPanelProps` (linha 48 de `SessionPage.tsx`).

Para `stepSummaries`, extrair assim:
```typescript
const stepSummaries = (session?.workflow_position?.step_summaries ?? {}) as Record<string, string>
```

### Design tokens existentes

Do design system atual (baseado nas classes Tailwind e CSS vars observadas):
- `var(--rs-success)` — verde para concluído
- `var(--rs-primary)` — azul/primário para etapa atual
- `var(--rs-primary-light)` — fundo suave da etapa atual
- `var(--rs-text-muted)` — cinza para pendente
- `var(--rs-text-primary)` — texto principal
- `var(--muted)` — fundo muted geral
- `var(--border)` — bordas

### Estrutura de `step_summaries` (vinda da Story 7.2)

```typescript
// workflow_position.step_summaries:
{
  "1": "Sistema de gestão de estoque para rede de farmácias",
  "2": "Usuários: atendentes de balcão e gerentes de estoque"
}
```

Chaves são strings (devido ao JSON), valores são strings de 1 linha.

Para exibir pelo índice de etapa (1-based):
```typescript
const summary = stepSummaries[String(stepIndex)] // stepIndex: 1-based
```

### Remoção da barra de progresso linear

Remover o bloco completo (linhas 197-219 de `SessionPage.tsx`):
```tsx
{/* REMOVER este bloco: */}
<div
  className="shrink-0 px-4 py-3"
  style={{ borderBottom: '1px solid var(--border)', background: 'var(--background)' }}
  data-testid="session-progress-panel"
>
  {/* ... progress bar content ... */}
</div>
```

As variáveis `currentStep`, `totalSteps`, `completed`, `progressPercent`, `currentStepLabel` (linhas 130-140) podem ser mantidas no `SessionChatPanel` e passadas para `SessionProgressPanel` ou recalculadas dentro do novo componente.

### Dependência de Story 7.2

`step_summaries` é populado pela Story 7.2. Antes de 7.2 ser implementada, `step_summaries` estará sempre vazio — o painel funcionará corretamente mostrando apenas nomes das etapas sem resumos. Sem blocker.

### Arquivos a tocar

| Arquivo | Mudança |
|---------|---------|
| `reqstudio-ui/src/components/chat/SessionProgressPanel.tsx` | Novo componente |
| `reqstudio-ui/src/pages/SessionPage.tsx` | Integrar SessionProgressPanel, remover barra linear |
| `reqstudio-ui/src/tests/SessionProgressPanel.test.tsx` | Testes do novo componente |

### References

- [SessionPage.tsx:25-31](reqstudio/reqstudio-ui/src/pages/SessionPage.tsx#L25) — `ELICITATION_STEPS` array
- [SessionPage.tsx:130-219](reqstudio/reqstudio-ui/src/pages/SessionPage.tsx#L130) — lógica atual de progresso e barra linear a remover
- [SessionPage.tsx:48](reqstudio/reqstudio-ui/src/pages/SessionPage.tsx#L48) — tipo `workflowPosition` em SessionChatPanelProps
- [ChatMessage.tsx](reqstudio/reqstudio-ui/src/components/chat/ChatMessage.tsx) — padrão de componente de chat para referência de estilo
- [SessionTelemetryWidget.tsx](reqstudio/reqstudio-ui/src/components/chat/SessionTelemetryWidget.tsx) — exemplo de widget inline no header do chat
- Story 7.2: [7-2-transicao-etapa-resumo-automatico.md](_bmad-output/implementation-artifacts/7-2-transicao-etapa-resumo-automatico.md) — schema de `step_summaries`
- [project-context.md](project-context.md) — padrões de teste de componente React

## Dev Agent Record

### Agent Model Used

_a preencher pelo dev agent_

### Debug Log References

### Completion Notes List

### File List
