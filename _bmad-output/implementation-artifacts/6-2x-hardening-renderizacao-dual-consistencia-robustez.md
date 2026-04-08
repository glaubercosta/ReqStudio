# Story 6.2x: Hardening da Renderização Dual — Consistência e Robustez

Status: done

## Story

As a Ana e time técnico,  
I want que as visões de negócio e técnica sejam estruturalmente consistentes e resilientes,  
so that revisão, exportação e colaboração ocorram sem ambiguidade e sem quebra de formatação.

## Acceptance Criteria

1. **Paridade estrutural**
Given o mesmo `artifact_state`  
When renderizar `business` e `technical`  
Then ambas visões preservam a mesma ordem e quantidade de seções (`section.id`).

2. **Exibição de IDs técnicos com toggle**
Given heading de seção renderizado  
When visão técnica for solicitada  
Then o ID técnico aparece no heading  
And na visão de negócio o ID fica oculto por padrão, com toggle opcional para exibição.

3. **Gherkin robusto PT/EN**
Given conteúdo com padrões de cenário  
When renderização técnica ocorrer  
Then a detecção de Gherkin cobre `Given/When/Then` e `Dado/Quando/Então` com case-insensitive  
And se já existir bloco de código, não deve haver dupla marcação.

4. **Placeholder canônico para seção vazia**
Given seção com `content` vazio ou whitespace  
When renderizada  
Then exibir `_Sem conteúdo detalhado._`.

5. **Limiar fixo no MVP**
Given regra de cobertura baixa  
When seção tiver cobertura insuficiente  
Then o limiar permanece fixo em `< 0.3` no MVP.

6. **Cobertura de testes de hardening**
Given suíte de testes de artefatos  
When story for concluída  
Then existem testes de regressão para: paridade entre visões, toggle opcional, Gherkin PT/EN, ausência de dupla marcação e placeholder canônico.

## Decisions Baseline

- Toggle opcional na visão de negócio: **aprovado**.
- Limiar de baixa cobertura fixo no MVP (`< 0.3`): **aprovado**.
- Placeholder único para seção vazia: `_Sem conteúdo detalhado._`: **aprovado**.
- Sem novos formatos além de Gherkin nesta story: **aprovado**.

## Planned Files (Scope Lock)

- `reqstudio/reqstudio-api/app/modules/artifacts/renderers/markdown.py`
- `reqstudio/reqstudio-api/app/modules/artifacts/router.py` (somente se necessário para toggle)
- `reqstudio/reqstudio-api/tests/test_artifacts_render.py`
- `reqstudio/reqstudio-ui/src/pages/*` (somente se toggle de visão de negócio for implementado no frontend nesta story)

## Dev Notes

- Implementação aplicada em backend renderer/service/router e testes de render.
- Toggle opcional de IDs foi implementado como query param `show_ids=true|false`.
- Limiar de cobertura baixa mantido fixo em `< 0.3` no MVP.

## Validation Evidence

- `python` smoke test do renderer: **passou** (`renderer-smoke-ok`).
- Execução de `pytest` de artifacts no ambiente da API (`.venv`) com ajustes de ambiente:
  - Comando:
    - `$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD='1'; $env:DEBUG='false'; .venv/Scripts/python.exe -m pytest tests/test_artifacts_render.py tests/test_artifacts.py tests/test_artifacts_coverage.py tests/test_artifacts_export.py -q`
  - Resultado:
    - `18 passed in 17.13s`

## Code Review Follow-up (6.2 + 6.2x)

- Finding sanado: contrato de `view` no endpoint `/export` alinhado com `/render` (`business|technical`).
- Regressão adicionada: teste `test_export_rejects_invalid_view` validando HTTP `422` para `view` inválido.

## Addendum — Correção Guiada PM/QA/DEV (Merenda Escolar)

### Contexto do desvio

- A primeira geração do artefato do projeto **Merenda Escolar** foi feita por script operacional direto no ambiente (`docker exec`) para viabilizar teste funcional imediato.
- Esse caminho bypassou o rito BMAD de validação de audiência (negócio vs técnico) antes da publicação do conteúdo.

### Análise PM

- Problema: linguagem do artefato inicial ficou excessivamente técnica para persona de negócio.
- Impacto: percepção de desalinhamento com objetivo do produto (elicitação acessível para usuário não técnico).
- Decisão: manter a infraestrutura 6.2/6.2x e corrigir apenas o conteúdo do `artifact_state` para linguagem executiva.

### Análise QA

- Verificado que o comportamento de 6.2/6.2x estava correto (dual view, warning, IDs técnicos apenas na visão técnica).
- Falha identificada no nível de dado: conteúdo fonte estava redigido com termos técnicos demais para a visão de negócio.
- Critério de correção: business view sem jargão desnecessário, technical view preservando rastreabilidade.

### Análise DEV

- Ação executada: nova versão do artefato com reescrita das seções em linguagem de gestão pública/operacional.
- Sincronização aplicada em `sessions.artifact_state` para refletir imediatamente na tela de sessão.
- Evidência operacional:
  - `artifact_id`: `69a56017-2f86-445d-82b3-96ce23c9fe74`
  - versão pós-correção: `3`
  - `has_id_in_business=False`
  - `has_id_in_technical=True`
  - warning de baixa cobertura presente para seção pendente.
