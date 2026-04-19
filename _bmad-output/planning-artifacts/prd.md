---
stepsCompleted: ['step-01-init', 'step-02-discovery', 'step-02b-vision', 'step-02c-executive-summary', 'step-03-success', 'step-04-journeys', 'step-05-domain', 'step-06-innovation', 'step-07-project-type', 'step-08-scoping', 'step-09-functional', 'step-10-nonfunctional', 'step-11-polish', 'step-12-complete']
lastEdited: '2026-04-18'
editHistory:
  - date: '2026-03-27'
    changes: 'Adição de FRs (42 FRs, 7 áreas) e NFRs (20 NFRs, 6 categorias). Polish: remoção de duplicação (Escopo do Produto), limpeza de implementation leakage residual, padronização terminológica.'
  - date: '2026-04-18'
    changes: 'Pós-MVP user testing: adição de FR43–FR47 (Engajamento e Acompanhamento de Progresso). Atualização de FR4, FR12, FR17. Jornadas J1 e J3 atualizadas para refletir abertura pelo agente, transições de etapa e painel de progresso lateral. Escopo MVP atualizado.'
inputDocuments: ['product-brief.md']
workflowType: 'prd'
documentCounts:
  briefs: 1
  research: 0
  brainstorming: 0
  projectDocs: 0
classification:
  projectType: "MVP: Web App (SPA) com backend leve → V2: SaaS B2B multi-tenant"
  domain: "AI-Powered Requirements Engineering Platform"
  complexity: "Média (MVP) / Média-Alta (V2)"
  projectContext: "Greenfield (código) / Brownfield (paradigma UX do BMAD)"
  differentiator: "BMAD como motor de elicitação multi-agente"
---

# Product Requirements Document - ReqStudio

**Author:** Glauber Costa
**Date:** 2026-03-25

## Executive Summary

O ReqStudio é uma plataforma de Requirements Engineering potencializada por IA, projetada para transformar especialistas de domínio em membros produtivos de times de desenvolvimento desde o primeiro dia. A plataforma opera em duas pontas: uma entrada acessível e não-técnica — onde analistas de negócio, product managers e consultores contribuem com seu conhecimento de domínio através de conversas guiadas — e uma saída técnica e profissional — artefatos estruturados em formatos legíveis por humanos (Markdown, PDF) e por máquinas (JSON, prompts de IA para agentes de desenvolvimento).

O produto utiliza o BMAD (Breakthrough Method of Agile AI-Driven Development) como motor de elicitação, aproveitando sua metodologia madura de workflows multi-agente sem recriá-la. O ReqStudio abstrai essa complexidade metodológica numa interface web que esconde o "como" e expõe o "o quê" — o usuário conduz sessões de requisitos sem saber que está executando BMAD por baixo.

O contexto de mercado é urgente: a IA está achatando o custo de desenvolvimento de software, transformando aplicações em commodities. Software houses que não aumentarem drasticamente sua produtividade serão superadas. Requisitos assertivos desde o dia 1 eliminam retrabalho e aceleram entregas — o ReqStudio é a ferramenta para essa corrida produtiva.

### O Que Torna Este Produto Especial

- **Motor BMAD integrado** — metodologia de elicitação multi-agente validada, não reinventada. O ReqStudio é a GUI do BMAD para quem não é dev.
- **Saída dual: humana e máquina** — artefatos exportáveis em Markdown/PDF para stakeholders e em JSON/prompts de IA para pipelines de desenvolvimento e agentes coding assistants.
- **Organização e histórico persistente** — projetos armazenados com contexto completo, sessões resumíveis, evolução rastreável. O diferencial vs. colar prompts no ChatGPT.
- **Isolamento e segurança por projeto** — dados de cada projeto/cliente são isolados desde o design, atendendo consultores que gerenciam múltiplos clientes com confidencialidade.

## Classificação do Projeto

| Dimensão | Classificação |
|----------|--------------|
| **Tipo de Produto** | MVP: Web App (SPA) com backend leve → V2: SaaS B2B multi-tenant |
| **Domínio** | AI-Powered Requirements Engineering Platform |
| **Complexidade** | Média (MVP) / Média-Alta (V2) |
| **Contexto** | Greenfield (código) / Brownfield (paradigma UX do BMAD) |
| **Diferencial Técnico** | BMAD como motor de elicitação multi-agente |

## Critérios de Sucesso

### Sucesso do Usuário

O ReqStudio atinge sucesso quando o especialista de domínio:

- **Se sente produtivo desde o primeiro uso** — o ambiente orienta sem impor tecnicismos, explicando em linguagem de negócio o que cada etapa faz e por que importa.
- **Sai da sessão preparado para a reunião com o time técnico** — ao ler o output não-técnico, o especialista tem confiança para discutir regras de negócio com desenvolvedores, que já tiveram acesso ao documento técnico complementar.
- **Percebe que o artefato "faz sentido"** — o documento gerado reflete fielmente o conhecimento de domínio que o especialista contribuiu, sem distorções ou generalizações de IA.

**Métrica mensurável:** % de sessões em que o usuário exporta pelo menos um artefato e retorna ao projeto dentro de 7 dias (indica valor percebido + engajamento contínuo).

### Sucesso do Negócio

- **Modelo pay-per-use sustentável** — cada sessão gera receita proporcional ao consumo de IA, sem barreiras de assinatura para experimentação.
- **Ambiente quase ubíquo** — o especialista incorpora o ReqStudio como ferramenta do dia-a-dia, não como evento pontual. Sinal: frequência de uso semanal por usuário ativo.
- **Comprovação de valor** — o ReqStudio demonstra ganho mensurável em assertividade e produtividade do time. Sinal de fracasso: incapacidade de comprovar esse ganho após 90 dias de operação.

**Métricas mensuráveis:**

| Métrica | Target (3 meses) | Target (12 meses) |
|---------|-------------------|---------------------|
| Sessões pay-per-use concluídas | > 100 | > 1.000 |
| Receita por sessão média | Validar break-even vs. custo API | Margem positiva estável |
| Retenção semanal de usuários ativos | > 30% | > 50% |
| NPS (comprovação de valor) | > 40 | > 60 |

### Sucesso Técnico

- **Tempo de resposta da IA ≤ 30 segundos** por interação — limite do aceitável; acima disso, o fluxo conversacional quebra.
- **Feedback loop integrado** — o usuário pode avaliar e corrigir artefatos gerados, e essas avaliações retroalimentam o ambiente para evolução contínua do produto e do framework BMAD.
- **Isolamento de dados por projeto** — zero vazamento de contexto entre projetos/clientes, verificável por auditoria.
- **Disponibilidade ≥ 99.5%** — para um produto pay-per-use, indisponibilidade = receita perdida.

**Métrica mensurável:** Taxa de artefatos que recebem feedback negativo < 15% (indica qualidade do motor de elicitação).

### Resultados Mensuráveis

| Resultado | Como Medir | Target |
|-----------|-----------|--------|
| Especialista preparado para reunião técnica | Survey pós-sessão: "Sinto-me preparado para discutir com o time de dev?" | > 80% sim |
| Artefatos utilizados por devs | Tracking de download/acesso do documento técnico | > 60% das sessões |
| Retorno ao projeto | Usuário reabre projeto em < 7 dias | > 40% |
| Qualidade percebida | Feedback negativo em artefatos | < 15% |
| Tempo até primeiro artefato | Tracking de duração da sessão | < 30 minutos |


## Jornadas de Usuário

### Jornada 1 — Ana, a Especialista de Domínio (Happy Path)

**Quem:** Ana, 30 anos, gerente de operações logísticas. Entende tudo de last-mile delivery, nunca escreveu um requisito de software.

**Cena de abertura:** Ana foi incluída num projeto para digitalizar o processo de rastreamento de entregas. O CTO pediu pra ela "documentar o que precisa". Ela não sabe por onde começar.

**Ação:** Recebe um convite por e-mail: "Você foi adicionada ao projeto 'Track&Trace' no ReqStudio." Clica, faz login, e abre o chat do projeto. A agente Mary se apresenta: *"Olá, Ana. Sou a Mary, analista de requisitos. Vamos trabalhar em 5 etapas para mapear tudo que o time técnico vai precisar: Contexto, Usuários, Objetivos, Processo atual e Restrições. Pode começar me contando o problema central que este projeto precisa resolver."* À esquerda do chat, um painel mostra as 5 etapas — todas esmaecidas, aguardando.

**Escalada:** O ReqStudio guia Ana etapa por etapa — sem jargão. Pergunta sobre quem usa o sistema, quando, qual a dor, o que seria o ideal. Ana importa o SLA do contrato de entregas e a normativa regulatória do setor. A IA integra esses documentos como contexto e desafia: *"Seu SLA menciona 'atraso'. Quanto atraso é aceitável? O que acontece quando passa desse limite?"* Ana refina.

**Momento de momentum:** Após a segunda etapa, Mary transiciona: *"Contexto e stakeholders mapeados. Agora quero entender o que define sucesso para este projeto."* O painel à esquerda acende as duas primeiras etapas — Ana clica numa delas e vê o resumo capturado. Pensa: *"isso está evoluindo de verdade."*

**Clímax:** Ana termina a sessão, exporta o artefato e lê o documento não-técnico. Pensa: *"É exatamente isso. Se eu levar isso pra reunião, o time técnico vai entender."*

**Resolução:** Na reunião com os devs, Ana está confiante. Os devs já leram o documento técnico (JSON/Markdown) e já têm visão do escopo. A conversa é produtiva, não é tradução.

### Jornada 2 — Felipe (Dev) + Ana (Re-análise Assistida por IA)

**Quem:** Felipe (dev fullstack, 28 anos) e Ana (especialista), colaborando assíncronamente no mesmo projeto.

**Cena de abertura:** Felipe recebe notificação: "Novos artefatos técnicos disponíveis no projeto Track&Trace." Acessa o ReqStudio como stakeholder técnico.

**Ação — Dúvida simples:** Felipe encontra ambiguidade na regra de "entrega parcial". Registra a dúvida no artefato com tag para Ana. Ana responde diretamente: *"Parcial acima de 80% conta como completa."* Artefato atualizado.

**Ação — Dúvida que exige re-análise:** Felipe levanta questão complexa: *"E se o cliente recusar a entrega parcial e pedir reentrega? Novo SLA? Quem paga o frete?"* Ana percebe que esse cenário não foi coberto na elicitação.

**Escalada (loop de re-análise):** Ana clica em **"Aprofundar com IA"** a partir da dúvida do Felipe. O ReqStudio reabre uma sessão guiada focada no ponto específico. O agente de IA já tem o contexto do projeto:

> *"Ana, Felipe levantou o cenário de recusa de entrega parcial. Vamos explorar: (1) Gera novo SLA ou estende o existente? (2) Quem absorve o custo de reentrega? (3) Existe limite de reentregas?"*

Ana responde guiada pela IA. Novos requisitos emergem. O artefato é **evoluído** com edge cases atualizados e histórico de decisão registrado.

**Clímax:** Felipe recebe notificação: *"Artefato atualizado — nova seção: Regras de reentrega."* Encontra requisitos técnicos prontos, com rastreabilidade até a pergunta que gerou a mudança.

**Resolução:** O produto evolui colaborativamente. A IA é facilitadora da **evolução contínua** dos requisitos, não só da criação inicial.

### Jornada 3 — Carla, a Consultora Multi-Cliente (Isolamento + Organização)

**Quem:** Carla, 42 anos, consultora independente. Gerencia requisitos para 5 clientes de domínios diferentes.

**Cena de abertura:** Carla terminou sessão de briefing pro cliente de saúde. Precisa mudar pro cliente de varejo em 10 minutos.

**Ação:** No dashboard do ReqStudio, Carla vê seus 5 projetos organizados. Muda do projeto "ClinicaPlus" pro projeto "RetailX" com um clique. Contexto muda completamente — agentes, histórico, artefatos. Zero contaminação.

**Escalada:** No projeto RetailX, Carla retoma de onde parou na semana anterior. Mary a recebe: *"Bem-vinda de volta, Carla. Na última sessão cobrimos Contexto, Usuários e Objetivos de negócio. A próxima etapa é Processo atual. Quer continuar ou revisitar algo já coberto?"* Carla responde continuar, importa a normativa fiscal relevante e segue sem perder contexto.

**Clímax:** Ao exportar o PRD do RetailX, Carla baixa em Markdown para importar no Notion do cliente. O artefato não tem referência alguma ao cliente de saúde. Isolamento confirmado.

**Resolução:** Carla gerencia 5 clientes com a mesma ferramenta, cada um com seu espaço isolado. O ReqStudio é a ferramenta ubíqua do cotidiano dela.

### Jornada 4 — Marcos, Admin/Ops (Gestão da Plataforma - V2+)

**Quem:** Marcos, 35 anos, ops engineer responsável pela infraestrutura do ReqStudio (perspectiva SaaS).

**Cena de abertura:** Dashboard de ops mostra uso crescente: 200 sessões ativas, consumo de API subindo.

**Ação:** Marcos monitora métricas: tempo de resposta da IA (p95 = 18s ✅), taxa de erro (0.3% ✅), custo API/sessão (dentro do budget ✅). Vê pico de uso às 10h.

**Escalada:** Usuário reporta timeout. Marcos investiga: sessão com prompt excessivamente longo. Ajusta rate limiting.

**Resolução:** Plataforma escala com visibilidade. Marcos intervém na infraestrutura, não no conteúdo.

### Resumo de Requisitos Revelados

| Jornada | Capacidades Reveladas |
|---------|----------------------|
| **Ana (Especialista)** | Onboarding guiado, sessão conversacional, saída dual, exportação, linguagem não-técnica, importação de docs de contexto |
| **Felipe + Ana (Dev + Re-análise)** | Acesso stakeholder, artefato técnico estruturado, dúvidas/feedback, re-análise assistida por IA, evolução incremental, notificações, rastreabilidade |
| **Carla (Consultora)** | Multi-projeto, isolamento de dados, resumo de sessão, exportação customizável, troca de contexto, importação de docs por projeto |
| **Marcos (Admin)** | Dashboard de monitoramento, métricas uso/custo, alertas, rate limiting, gestão de infra |

**Capacidade transversal:** Importação de documentos de referência (PDFs, Markdowns, planilhas, normas, contratos). A IA usa como contexto na elicitação, referencia nas regras geradas e cita fontes nos artefatos.

## Requisitos de Domínio (Escopo Futuro)

Os seguintes tópicos foram identificados como relevantes mas diferidos para versões pós-MVP:

### Segurança e Privacidade de Dados
- Isolamento multi-tenant (schema isolation vs. row-level security)
- Política de dados enviados à API de IA (retenção, anonimização)
- Criptografia em repouso e em trânsito; avaliação de necessidade de E2E

### Dependência de LLM API
- Resiliência a indisponibilidade da API (modo degradado, cache de sessão)
- Estratégia de custo: absorção vs. repasse de variações de preço da API
- Compatibilidade entre versões de modelo (output consistency)
- Avaliação de suporte multi-provedor (OpenAI, Google) como hedge

### Propriedade Intelectual dos Artefatos
- Titularidade dos artefatos gerados (usuário vs. plataforma)
- Política de uso de dados para treinamento/fine-tuning (proibição)
- Direito ao esquecimento e exclusão completa de dados

## Inovação e Padrões Novos

### Áreas de Inovação Detectadas

1. **Elicitação multi-agente com workflow estruturado** — O ReqStudio orquestra agentes IA especializados (BMAD) para elicitação de requisitos. Nenhum produto no mercado combina isso com uma GUI acessível para não-técnicos.

2. **Saída dual: humana + machine-readable** — Tradução automática de linguagem de negócio em artefatos legíveis por humanos (Markdown/PDF) E por máquinas (JSON, prompts de IA). Ferramentas existentes fazem um ou outro.

3. **Feedback loop evolutivo** — Projetos retroalimentam o ambiente: avaliações de artefatos e dúvidas de devs evoluem a qualidade dos requisitos e eventualmente o próprio framework. Flywheel inédito em ferramentas de requisitos.

4. **Colaboração stakeholder com passagem de bastão** — Especialistas, devs e consultores contribuem no mesmo projeto em momentos diferentes, com re-análise assistida por IA quando feedback exige aprofundamento.

### Contexto de Mercado e Concorrência

**Não existe concorrente direto.** O mercado está dividido em:

- **Geradores de PRD** (WriteMyPRD, ChatPRD, MakePRD, Beam AI) — single-shot, sem metodologia, sem persistência
- **Requirements Management enterprise** (Visure, Jama, aqua cloud) — completos mas inacessíveis, caros, voltados pra devs/QA
- **Multi-agente acadêmico** (MetaGPT, papers ArXiv) — conceito validado mas não produtizado para não-técnicos

O ReqStudio ocupa o **gap entre acessibilidade e profundidade metodológica** — uma categoria de produto nascente.

### Abordagem de Validação

- **Teste mínimo de viabilidade:** Sessão completa de elicitação com 5-10 especialistas reais de domínio. Medir: (a) tempo até primeiro artefato, (b) autoavaliação "estou preparado pra reunião com devs", (c) custo API por sessão vs. valor percebido.
- **Teste de custo:** Estimar tokens consumidos por sessão completa (briefing → PRD). Calcular break-even entre custo API e preço pay-per-use aceitável para o mercado.

### Mitigação de Riscos de Inovação

| Risco | Probabilidade | Impacto | Mitigação |
|-------|:---:|:---:|-----------|
| Custo de IA por sessão inviabiliza pay-per-use | Alta | Crítico | Prompt caching, otimização de tokens, modelos menores para etapas simples, monitoramento de custo em tempo real |
| Qualidade insuficiente dos artefatos | Média | Alto | Feedback loop integrado, métricas de qualidade, evolução contínua dos prompts |
| Não-técnicos não adotam a ferramenta | Média | Alto | UX research intensivo, testes com usuários reais, linguagem 100% de negócio |
| Dependência de API única (Anthropic) | Baixa | Alto | Abstração de provider, avaliação futura de multi-provedor |

## Requisitos Específicos — SaaS B2B

### Visão Geral do Tipo de Projeto

O ReqStudio é uma Web App SPA (MVP) com evolução planejada para SaaS B2B multi-tenant. O MVP foca na experiência do analista de negócios como usuário primário, com suporte a colaboração de stakeholders sob controle do analista.

### Modelo de Isolamento (Tenant)

- **MVP:** Banco de dados único (SQLite) com isolamento lógico por tenant (`tenant_id` em todas as tabelas). Projetos pertencem a um tenant.
- **V2 (SaaS):** Migração para PostgreSQL com row-level security (RLS) para reforçar isolamento por tenant no nível do banco.
- **Implicação arquitetural:** Toda query é filtrada por `tenant_id`, garantido via middleware. Mais simples de operar que banco-por-projeto.

### Modelo de Permissões (RBAC)

| Papel | Criar sessão IA | Editar artefatos | Publicar artefatos | Visualizar artefatos | Feedback/Dúvidas |
|-------|:---:|:---:|:---:|:---:|:---:|
| **Analista (owner)** | ✅ | ✅ | ✅ (controla visibilidade) | ✅ | ✅ |
| **Stakeholder (dev/PM)** | ❌ | ❌ | ❌ | ✅ (somente publicados) | ✅ |
| **Admin (V2+)** | ❌ | ❌ | ❌ | ✅ (auditoria) | ❌ |

O analista é o **gatekeeper**: decide quando e quais artefatos são visíveis para os demais stakeholders. Stakeholders podem ver artefatos publicados e registrar dúvidas/feedback.

### Tiers de Assinatura

- **MVP:** Sem tiers. Modelo pay-per-use simples (a implementar no Growth).
- **Growth/V2:** Tiers planejados (Free trial, Pro, Enterprise) — a definir em fase posterior.

### Integrações

- **MVP:** Sem integrações externas além da API do provedor de IA.
- **Growth:** OAuth (Google), export para Notion/Jira/Linear.
- **Vision:** Webhooks, API pública.

### Compliance e Segurança

- **MVP:** Boas práticas de segurança web (HTTPS, hash de senhas, tokens JWT, sanitização de input).
- **Growth:** Avaliação de LGPD/GDPR conforme expansão geográfica.

### Restrições Técnicas de Produto

- **Interface:** SPA com foco em UX mobile-first e não-técnica. Decisão de framework no documento de Arquitetura.
- **Processamento de IA:** Todas as chamadas à API de IA são intermediadas pelo backend — o frontend nunca acessa a API diretamente.
- **Persistência:** Isolamento por tenant desde o MVP, com caminho de migração para multi-tenancy reforçada. Decisão de banco no documento de Arquitetura.
- **Autenticação:** Fluxo simples (e-mail + senha) no MVP. Decisão de implementação (JWT, OAuth, etc.) no documento de Arquitetura.
- **Motor de elicitação:** Integração com motor metodológico externo estruturado. Decisão de qual motor no documento de Arquitetura.

## Requisitos Funcionais

Requisitos organizados por áreas de capacidade (WHAT), não por tecnologia (HOW). Cada FR é uma capacidade testável e independente de implementação. Para decisões técnicas de implementação, ver documento de Arquitetura.

### Contexto e Organização

Projetos como containers de contexto isolados — a unidade de trabalho do ReqStudio.

- FR1: Usuário pode criar projeto com nome, descrição e domínio de negócio
- FR2: Usuário pode listar, acessar e alternar entre projetos ativos
- FR3: Cada projeto mantém contexto isolado — artefatos, sessões e documentos de referência pertencem exclusivamente ao projeto
- FR4: O painel do projeto exibe resumo visual do progresso (etapas concluídas, percentual) e próximos passos — visível na tela inicial do projeto, antes de entrar na sessão
- FR5: Usuário pode arquivar projetos concluídos sem perda de dados
- FR6: Zero vazamento de contexto entre projetos — verificável por auditoria

### Enriquecimento de Contexto

Documentos de referência como combustível de qualidade — quanto mais contexto, melhor o artefato gerado.

- FR7: Usuário pode importar documentos de referência (PDF, Markdown, planilhas, normas, contratos) como contexto do projeto
- FR8: Usuário pode importar documentos a qualquer momento da sessão, e o sistema incorpora imediatamente como contexto
- FR9: IA referencia documentos importados durante a sessão de elicitação para fundamentar perguntas e desafiar respostas
- FR10: Artefatos gerados citam fontes dos documentos de referência quando aplicável
- FR11: Usuário pode visualizar quais documentos de referência estão ativos no contexto do projeto

### Tradução Assistida

O core do produto — sessão guiada que transforma conhecimento de domínio em requisitos estruturados.

- FR12: Sistema conduz sessões de elicitação multi-etapa com agentes especializados, produzindo artefatos progressivamente; o agente lidera a abertura e as transições de etapa (ver Arquitetura para decisões de motor de elicitação)
- FR13: Sessão utiliza linguagem não-técnica — zero jargão de desenvolvimento, explicações em linguagem de negócio
- FR14: IA identifica gaps nos requisitos e sugere cenários não cobertos proativamente
- FR15: Usuário pode pausar sessão e retomá-la posteriormente sem perda de contexto
- FR16: Quando documentos de referência estão disponíveis, sistema pode gerar proposta inicial de artefato para refinamento pelo usuário
- FR17: No início do projeto (primeiro acesso ao chat), o agente inicia sessão de descoberta guiada a partir do problema do usuário
- FR18: Cada etapa da sessão é validada pelo usuário antes de avançar — construção progressiva, não geração em lote
- FR19: IA desafia respostas do usuário e solicita refinamento quando detecta ambiguidade ou generalização

### Engajamento e Acompanhamento de Progresso

Momentum visível — o usuário sente o trabalho evoluir em tempo real, etapa a etapa.

- FR43: No início do projeto (primeiro acesso ao chat), o agente envia mensagem inicial apresentando-se, declarando o número e nome das etapas do processo e convidando o usuário a começar
- FR44: Ao concluir cada etapa, o agente emite mensagem de transição declarando o que foi alcançado e anunciando o objetivo da próxima etapa — tom direto, sem bajulação
- FR45: O agente gera e armazena um resumo de uma linha por etapa concluída no momento da transição
- FR46: A interface da sessão exibe painel lateral de progresso recolhível contendo: estado visual das etapas (concluídas em cores intensas, pendentes em cores esmaecidas) e resumo por etapa concluída oculto por padrão e expansível com um clique
- FR47: Ao retomar projeto em sessão existente, o agente envia greeting de retorno com: resumo das etapas concluídas, próxima etapa programada e opção para o usuário continuar ou revisitar etapa anterior

### Artefatos e Saída

O produto tangível — o artefato gerado é o que o usuário leva e pelo que julga o ReqStudio.

- FR20: Sistema gera artefatos em formato não-técnico (legível por stakeholders de negócio) e formato técnico (estruturado para devs e agentes IA)
- FR21: Usuário visualiza artefato sendo construído progressivamente durante a sessão
- FR22: Usuário pode exportar artefatos em Markdown e JSON
- FR23: Artefatos técnicos são exportáveis como prompts/contexto para agentes de desenvolvimento IA
- FR24: Artefato mantém histórico de evolução com rastreabilidade de quem/quando/por que cada requisito mudou
- FR25: Cada seção do artefato exibe indicador de cobertura da elicitação (seções bem exploradas vs. pendentes de aprofundamento)

### Evolução Colaborativa (Growth)

Feedback de stakeholders evolui artefatos — o produto não é para criação única, mas para evolução contínua.

- FR26: Stakeholder (dev/PM) pode visualizar artefatos publicados pelo analista
- FR27: Stakeholder pode registrar dúvidas e feedback em seções específicas do artefato
- FR28: Analista pode iniciar re-análise assistida por IA a partir de feedback de stakeholder
- FR29: Re-análise mantém contexto completo do projeto e foca no ponto levantado
- FR30: Artefato é evoluído incrementalmente — novas versões preservam histórico e rastreabilidade
- FR31: Stakeholders recebem notificação quando artefatos são atualizados

### Evolução de Produto Existente — Brownfield (Growth/Vision)

Elicitação de requisitos para evolução de produtos que já existem, não apenas criação greenfield.

- FR32: Usuário pode importar documentação de projeto existente (README, architecture.md, docs técnicos) como contexto de produto brownfield (Growth)
- FR33: Em projetos brownfield, sessão de elicitação foca em gaps entre o que existe e o que se deseja
- FR34: IA identifica possíveis impactos de novos requisitos sobre funcionalidades existentes
- FR35: Artefatos de evolução referenciam componentes existentes do sistema e indicam áreas de impacto
- FR36: Usuário pode conectar repositório de código como fonte de contexto do projeto (Vision)
- FR37: Sistema analisa codebase existente e gera sumário de capacidades, stack tecnológica e padrões identificados (Vision)

### Identidade e Acesso

Infraestrutura de confiança — pré-requisito para o produto existir, não feature diferenciadora.

- FR38: Usuário pode criar conta e autenticar via e-mail e senha
- FR39: Sessões autenticadas via token (JWT) com expiração configurável
- FR40: Dados de cada projeto são isolados por tenant — nenhum usuário acessa dados de outro tenant
- FR41: Analista controla quais artefatos são visíveis para stakeholders (publicação seletiva) (Growth)
- FR42: Sistema suporta papéis com permissões diferenciadas: Analista (owner), Stakeholder (leitura + feedback), Admin (auditoria) (Growth)

### Faseamento dos Requisitos Funcionais

| Fase | FRs Incluídos |
|------|---------------|
| **MVP** | FR1–FR25, FR38–FR40, FR43–FR47 (Contexto, Enriquecimento, Tradução, Artefatos, Auth básica, Engajamento e Progresso) |
| **Growth** | FR26–FR35, FR41–FR42 (Colaboração, Brownfield docs, RBAC) |
| **Vision** | FR36–FR37 (Conexão a codebase, análise automática de código) |

## Requisitos Não-Funcionais

Requisitos de qualidade seletivos — apenas categorias relevantes para o contexto do ReqStudio. Cada NFR é mensurável e testável.

### Performance

- NFR1: Tempo de resposta da IA ≤ 30 segundos por interação — acima disso, o fluxo conversacional quebra e o usuário perde engajamento
- NFR2: Interface carrega em ≤ 2 segundos após login (p95)
- NFR3: Exportação de artefato completa em ≤ 5 segundos para documentos de até 50 páginas
- NFR4: Sistema suporta sessões simultâneas sem degradação observável para o usuário individual

### Segurança

- NFR5: Dados em trânsito criptografados via HTTPS/TLS 1.2+
- NFR6: Senhas armazenadas com hash seguro (bcrypt ou equivalente)
- NFR7: Tokens JWT com expiração máxima de 24h e refresh token rotation
- NFR8: Zero vazamento de dados entre tenants — testável via auditoria automatizada
- NFR9: Dados enviados à API de IA não são retidos pelo provedor para treinamento (garantia contratual com provedor)

### Escalabilidade

- NFR10: Arquitetura suporta 10x crescimento de usuários ativos sem reescrita — via escalabilidade horizontal
- NFR11: Modelo de dados migra de SQLite para PostgreSQL com RLS sem mudança de API
- NFR12: Custo de IA por sessão monitorado em tempo real com alertas de threshold

### Disponibilidade

- NFR13: Disponibilidade ≥ 99.5% em horário comercial (8h–22h, timezone do tenant)
- NFR14: Resiliência a indisponibilidade da API de IA: modo degradado com notificação ao usuário (sem perda de sessão em andamento)
- NFR15: Sessão em andamento preservada em caso de desconexão do usuário — retomável em ≤ 5 minutos

### Acessibilidade

- NFR16: Interface desenvolvida com abordagem mobile-first — funcional a partir de 360px (smartphone), otimizada para tablet (768px+) e desktop (1024px+)
- NFR17: Contraste de texto conforme WCAG 2.1 AA (mínimo 4.5:1)
- NFR18: Interface navegável via teclado para ações primárias

### Integração

- NFR19: Abstração de provedor de IA — trocar de Anthropic para outro provedor sem mudança no frontend ou na lógica de sessão
- NFR20: Exportação produz arquivos compatíveis com importação em Notion e Jira (validável via teste de import)

## Escopo do Projeto e Desenvolvimento Faseado

### Estratégia e Filosofia do MVP

**Abordagem:** Experience MVP com validação de problema — a UX não-técnica é indissociável do valor entregue. Se o especialista desiste por conta da interface, nunca chega ao output.

**Recurso mínimo:** Desenvolvedor solo fullstack com experiência em IA (API de LLM) e frontend SPA.

### Feature Set do MVP (Fase 1)

**Jornada Core:** Ana (especialista de domínio, solo)

**Capacidades Must-Have:**
- Autenticação simples (e-mail + senha)
- Criação e gerenciamento de projetos (multi-projeto)
- Importação de documentos de referência (PDF, Markdown)
- Sessão de elicitação guiada com IA
- Geração de artefatos com saída dual (não-técnico + técnico)
- Exportação de artefatos (Markdown, JSON)
- Persistência de projetos e sessões (banco leve com isolamento por tenant)
- UX não-técnica — linguagem de negócio, zero jargão
- Engajamento e momentum: abertura de projeto pelo agente, transições de etapa sinalizadas, painel lateral de progresso recolhível, greeting de retorno ao projeto

**Explicitamente fora do MVP:**
- Colaboração stakeholder (Felipe+Ana) → Phase 2
- Re-análise assistida por IA a partir de feedback → Phase 2
- Billing pay-per-use → Phase 2
- Admin/Ops dashboard → Phase 2+
- Party Mode e Advanced Elicitation na UI → Phase 2
- White-label, integrações, API pública → Phase 3

### Pós-MVP (Fase 2 — Growth)

- Colaboração stakeholder com passagem de bastão
- Re-análise assistida por IA (loop de feedback dev → especialista)
- Sistema de dúvidas/feedback nos artefatos
- Billing pay-per-use funcional
- Feedback loop (avaliação de artefatos → melhoria do sistema)
- Notificações de mudanças em artefatos
- Importação de documentação de projeto para elicitação brownfield
- Indicador de confiança/cobertura por seção do artefato

### Expansão (Fase 3 — Vision)

- Admin dashboard e métricas operacionais
- Integrações (Jira, Notion, Linear, OAuth Google)
- White-label para consultores
- API pública e webhooks
- Templates de domínio específico
- Retroalimentação automática do framework BMAD
- Conexão direta a repositórios de código para evolução brownfield
- Análise automática de codebase existente

### Mitigação de Riscos

| Risco | Tipo | Mitigação |
|-------|------|-----------|
| **Persistência de contexto entre sessões** | Técnico (mais arriscado) | PoC focada nesse ponto antes de construir o restante. Testar: salvar/restaurar sessão BMAD de/para banco |
| Custo de IA por sessão | Financeiro | Monitoramento de tokens desde dia 1, prompt caching, modelos menores para etapas simples |
| Adoção por não-técnicos | Mercado | Testes com 5-10 especialistas reais antes de polir features secundárias |
| Escopo creep | Processo | MVP estrito: só jornada da Ana. Tudo que não serve Ana solo vai pra Phase 2 |
