# Requisitos Complementares — Story 6.2 (Renderização Dual)

**Data:** 2026-04-05  
**Origem:** Elicitação dirigida (perfil BMAD Analyst) para complementar a Story `6.2`  
**Artefato-base:** `_bmad-output/implementation-artifacts/6-2-renderizacao-dual-visao-negocio-tecnica.md`

---

## 1. Objetivo

Refinar a Story 6.2 para garantir que a renderização dual (negócio e técnica) seja:
- semanticamente consistente entre visões,
- confiável para uso por analistas e times técnicos,
- pronta para integração com exportação/versionamento das stories 6.4 e 6.5.

---

## 2. Escopo Atual da 6.2 (já coberto)

- `view=business|technical` no endpoint de render.
- Renderização em Markdown para ambas visões.
- Fonte única de verdade: `artifact_state`.
- Aviso para baixa cobertura (`⚠️ Pendente de aprofundamento`).

---

## 3. Requisitos Complementares Propostos

### RC-6.2-01 — Paridade estrutural entre visões
As a Ana,  
I want que ambas as visões mantenham a mesma quantidade e ordem de seções,  
so that negócio e técnico discutam exatamente o mesmo escopo.

**Critério de aceite:**
- Dado o mesmo `artifact_state`, as visões `business` e `technical` devem ter a mesma lista ordenada de `section.id`.

### RC-6.2-02 — Normalização de linguagem técnica (Gherkin PT/EN)
As a time técnico,  
I want que conteúdo com padrões de cenário seja renderizado como bloco Gherkin de forma robusta,  
so that critérios fiquem legíveis e executáveis.

**Critérios de aceite:**
- Detectar e formatar blocos com `Given/When/Then` e `Dado/Quando/Então`.
- Detecção deve ser case-insensitive.
- Se o conteúdo já estiver em bloco de código, não duplicar delimitadores.

### RC-6.2-03 — Rastreabilidade explícita por seção
As a desenvolvedor,  
I want identificar cada seção técnica por ID estável,  
so that comentários, versões e automações referenciem seções sem ambiguidade.

**Critérios de aceite:**
- Visão técnica mantém `section.id` no heading.
- Visão de negócio não exibe ID no heading.
- O mapeamento título->id é preservado por render em todas as versões.

### RC-6.2-04 — Compatibilidade de markdown segura
As a plataforma,  
I want que renderização não permita conteúdo malformado quebrar o documento,  
so that export e leitura permaneçam confiáveis.

**Critérios de aceite:**
- Quebras de heading e blocos de código mal fechados não podem corromper o Markdown final.
- Conteúdo vazio/whitespace em seção gera placeholder explícito (`_Sem conteúdo detalhado._`).

### RC-6.2-05 — Observabilidade de render
As a time de produto,  
I want rastrear falhas e latência de render,  
so that gargalos e regressões sejam detectados cedo.

**Critérios de aceite:**
- Emitir logs estruturados com `artifact_id`, `view`, `section_count`, `render_time_ms`.
- Falhas de render devem retornar erro guiado padronizado (sem stacktrace no payload).

### RC-6.2-06 — Performance mínima para sessões reais
As a Ana,  
I want obter a renderização rapidamente,  
so that a revisão durante a sessão não quebre meu fluxo.

**Critérios de aceite:**
- P95 de render <= 500ms para artefatos com até 100 seções em ambiente de referência MVP.

---

## 4. Critérios de Aceite Incrementais (6.2+)

Para considerar a 6.2 realmente pronta para escala de uso:

1. Passar testes existentes de 6.2 sem regressão.
2. Adicionar testes para paridade estrutural entre visões.
3. Adicionar testes para Gherkin em PT-BR e case-insensitive.
4. Adicionar testes para seção vazia e markdown resiliente.
5. Validar telemetria/log de render com campos mínimos.

---

## 5. Decisões Pendentes de Elicitação

1. A visão de negócio deve ocultar completamente IDs técnicos ou permitir toggle opcional?
Status: **Decidido** — toggle opcional.

2. O limiar de baixa cobertura (atual `< 0.3`) permanece fixo ou vira configuração por tenant?
Status: **Decidido** — permanece fixo no MVP (`< 0.3`).

3. O placeholder de seção vazia deve ser padrão único para todo produto?
Status: **Decidido** — padronizar no MVP como `_Sem conteúdo detalhado._` em todas as visões.

4. Queremos suporte explícito a outros formatos de critério além de Gherkin nesta story?
Status: **Decidido** — não incluir nesta story por enquanto.

## 5.1 Decisões Consolidadas (2026-04-05)

- `toggle` opcional para exibir IDs técnicos na visão de negócio.
- Limiar de baixa cobertura fixo no MVP (`< 0.3`).
- Sem expansão de formatos além de Gherkin nesta story.
- Placeholder único de seção vazia: `_Sem conteúdo detalhado._`.

---

## 6. Recomendação de Priorização

**Prioridade Alta (entrar já em 6.2x):**
- RC-6.2-01 (paridade estrutural),
- RC-6.2-02 (Gherkin PT/EN robusto),
- RC-6.2-04 (resiliência markdown).

**Prioridade Média:**
- RC-6.2-03 (rastreabilidade já parcial, formalizar testes),
- RC-6.2-05 (observabilidade).

**Prioridade Baixa:**
- RC-6.2-06 (SLO formal pode entrar com hardening de performance do Epic 6).
