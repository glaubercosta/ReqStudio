# ReqStudio — Lições Aprendidas (Agent Evolution Backlog)

> **Propósito:** Registrar fricções e oportunidades de melhoria nos agentes BMAD identificadas durante o desenvolvimento do ReqStudio.
> **Importante:** Estas lições NÃO devem ser aplicadas aos agentes agora. Devem ser revisadas em uma sessão dedicada de evolução de agentes, considerando compatibilidade com o BMAD original.

---

## Lição 1 — Detecção de Conflito de Portas no Setup

**Sprint / Story:** Epic 1 / Story 1.2 (Frontend React/Vite)
**Severidade:** Baixa (não quebrou o produto, mas gerou fricção e retrabalho)

### O que aconteceu
O `docker compose up` falhou porque as portas padrão (`8000`, `5173`) estavam ocupadas por outros projetos rodando na mesma máquina de desenvolvimento. O script `find-ports.ps1` havia sido criado como parte da Story 1.1, mas não estava integrado ao fluxo de onboarding (README).

### Causa raiz
O agente `bmad-dev-story` não possui nenhuma etapa que verifique conflitos de infraestrutura local antes de implementar serviços com portas fixas. A criação do script de detecção de portas foi tratada como um entregável isolado, sem garantia de que seria usado no fluxo correto.

### Sugestão de evolução para o agente (genérica)

O agente deve aplicar um **"Princípio de Verificação de Pré-condições de Infraestrutura"** antes de qualquer implementação que envolva recursos exclusivos de sistema (portas de rede, volumes, sockets, PIDs, sockets de banco de dados, etc.):

1. **Identificar recursos exclusivos exigidos pela story** — qualquer recurso que só pode ser usado por um processo por vez (portas TCP/UDP, dispositivos, named pipes, etc.)
2. **Verificar se já existe um mecanismo de detecção no projeto** — se sim, referenciar; se não, criar antes de definir valores padrão
3. **Integrar a verificação ao fluxo de onboarding** — o mecanismo de detecção deve estar documentado como passo obrigatório *antes* da configuração do ambiente, independente do tipo de recurso
4. **Documentar valores padrão como sugestões, não verdades** — arquivos de configuração (`.env`, `docker-compose.yml`, etc.) devem deixar claro que os valores padrão assumem ausência de conflitos e que o usuário deve verificar antes de usar

---

## Lição 2 — Instalação do Frontend em Múltiplas Etapas

**Sprint / Story:** Epic 1 / Story 1.2 (Frontend React/Vite)
**Severidade:** Baixa (resolvido com retrabalho, sem impacto no produto)

### O que aconteceu
O shadcn/ui falhou na primeira tentativa de `npx shadcn@latest init` porque:
1. O `vite.config.ts` ainda não tinha o plugin do Tailwind CSS v4
2. O `tsconfig.json` não tinha o alias `@/` configurado

Esses pré-requisitos foram configurados em mensagens separadas, no meio do fluxo, em vez de estarem prontos antes do `shadcn init`.

### Causa raiz
A story foi criada com tasks sequenciais corretamente ordenadas, mas o agente não traduziu essa dependência em instrução clara de "configure X antes de executar Y" para o usuário. As instruções de instalação foram passadas de forma incremental e reativa, em vez de proativa e completa.

### Sugestão de evolução para o agente (genérica)

O agente deve aplicar um **"Princípio de Setup Atômico"** para stories que envolvem instalação e configuração de dependências com ordem de execução não-trivial:

1. **Mapear o grafo de dependências de instalação antes de gerar instruções** — identificar quais configurações são pré-requisito para quais comandos de instalação/inicialização
2. **Gerar um script de setup único e sequencial** como entregável obrigatório de qualquer story de inicialização de serviço/ferramenta — independente de ser frontend, backend, CLI, plugin ou qualquer outra tecnologia
3. **Nunca fornecer instruções de instalação de forma incremental e reativa** — todos os comandos necessários devem ser apresentados no início, agrupados por dependência, com a ordem explicitamente documentada
4. **O script de setup deve ser idempotente** — executável múltiplas vezes sem efeitos colaterais (verificar se já instalado antes de instalar)

---

## Lição 3 — Conflito de Porta Entre Dev Local (Vite) e Docker

**Sprint / Story:** Epic 1 / Story 1.3 (Design System)
**Severidade:** Baixa (sem impacto no produto, mas comportamento inesperado)

### O que aconteceu
Ao rodar `npm run dev` com o container Docker do frontend já ativo na porta `5174`, o Vite detectou que `5174` estava ocupada e subiu automaticamente para `5175`. O comportamento é correto (Vite auto-increment é feature), mas inesperado para o desenvolvedor.

### Causa raiz
Não foi definida uma distinção explícita entre **porta do dev server local** (`npm run dev`) e **porta do container Docker** (`FRONTEND_PORT`). Como ambos usam a mesma faixa de portas sem configuração explícita, o auto-increment do Vite gera saída sempre diferente dependendo do que estiver rodando.

### Sugestão de evolução para o agente (genérica)

O agente deve aplicar um **"Princípio de Segregação de Portas por Contexto de Execução"** para projetos com múltiplos modos de execução (local direto, Docker, CI, etc.):

1. **Identificar todos os contextos de execução** — dev local, Docker, CI/CD, produção, testes, etc.
2. **Atribuir portas distintas por contexto** — cada modo de execução deve ter sua porta explicitamente configurada e documentada
3. **Tornar as portas configuráveis** — via variável de ambiente ou arquivo de config, nunca hardcoded sem documentação
4. **Documentar a tabela de portas** no README — deixar explícito qual servico usa qual porta em qual contexto

---

## Lição 4 — Dockerfile pip --user: Pacotes Inacessíveis para Usuário Não-Root

**Sprint / Story:** Epic 1 / Story 1.4 (Backend Middleware)
**Severidade:** Alta (container em crashloop, bloqueou execução de testes)

### O que aconteceu
O container da API crashava com `Permission denied` ao tentar executar o `uvicorn`. O `pip install --user` no builder copiava pacotes para `/root/.local/bin`, mas o runtime usava um usuário não-root (`appuser`) sem acesso a esse diretório.

### Causa raiz
O Dockerfile usava `pip install --user` no estágio builder e copiava `/root/.local` para o runtime. Ao trocar para `USER appuser`, esse diretório ficou inacessível.

### Sugestão de evolução para o agente (genérica)

O agente deve aplicar um **"Princípio de Compatibilidade de Permissões em Multi-Stage Builds"**:

1. **Nunca usar `pip install --user` em Dockerfiles com usuário não-root** — instalar sempre em `/usr/local` (sem `--user`) para garantir acesso universal
2. **Testar explicitamente o binário principal** como parte do build (`RUN uvicorn --version`) para falhar no build e não no runtime
3. **Generalização:** qualquer ferramenta instalada em diretório do usuário (npm global, gem, go install, cargo install) deve ser instalada em path acessível pelo usuário de runtime

---

## Lição 5 — pytest pythonpath: ModuleNotFoundError em Container Docker

**Sprint / Story:** Epic 1 / Story 1.4 (Backend Middleware)
**Severidade:** Média (bloqueou execução de testes, resolvido sem rebuild)

### O que aconteceu
`pytest tests/ -v` dentro do container retornava `ModuleNotFoundError: No module named 'app'`, apesar do código estar em `/app/app/`. O pytest não adicionava o diretório corrente ao `sys.path` automaticamente.

### Causa raiz
O `pyproject.toml` não tinha `pythonpath = ["."]` na seção `[tool.pytest.ini_options]`. O pytest moderno (6+) não adiciona o diretório raiz ao `sys.path` por padrão sem esta configuração.

### Sugestão de evolução para o agente (genérica)

O agente deve aplicar um **"Princípio de Configuração Explícita de Path para Testes"**:

1. **Sempre incluir `pythonpath` na configuração de testes** ao criar qualquer projeto Python com pytest — não assumir que o path será detectado automaticamente
2. **Validar a execução de testes no ambiente de destino** (container, CI) como parte da story, não apenas localmente
3. **Generalização:** para qualquer framework de testes (Jest, Vitest, JUnit, RSpec), garantir que a configuração de module resolution esteja explícita no arquivo de configuração do projeto

---

## Lição 6 — Dependências Abandonadas: passlib + bcrypt Incompatibilidade

**Sprint / Story:** Epic 2 / Story 2.1 (Registro de Usuário)
**Severidade:** Alta (testes falhando em runtime, não detectável sem execução)

### O que aconteceu
`passlib[bcrypt]>=1.7.4` foi adicionado ao `requirements.txt`. O pip instalou `bcrypt 4.x` (versão mais recente), que tem API incompatível com `passlib 1.7.4`. O erro só foi detectado ao rodar os testes no container — `ValueError: password cannot be longer than 72 bytes` — mesmo para senhas de 9 chars.

### Por que o ambiente do desenvolvedor detectou e o agente não?

O agente escreve código mas **não executa**: não há um ambiente onde `pip install` roda antes de propor a solução. O erro de runtime só surge na execução real. Isso é uma limitação estrutural do modelo de operação de agentes de código.

Adicionalmente, a constraint `>=1.7.4` permitiu ao pip instalar qualquer versão de `bcrypt`, incluindo 4.x — que quebrou a integração. Uma constraint mais restrita (`bcrypt<4.0.0`) teria evitado o problema.

### Causa raiz
`passlib` não é mantido desde 2019 e nunca foi atualizado para suportar `bcrypt >= 4.0`. O agente escolheu uma biblioteca popular mas desatualizada sem verificar o status de manutenção.

### Sugestão de evolução para o agente (genérica)

O agente deve aplicar um **"Princípio de Verificação de Saúde da Dependência"** antes de recomendar qualquer biblioteca:

1. **Verificar data do último release** — bibliotecas sem atualização há >2 anos merecem atenção especial
2. **Verificar compatibilidade explícita com versões recentes** das dependências transitivas
3. **Preferir dependências diretas** em vez de wrappers quando o wrapper é o único ponto de falha (ex: usar `bcrypt` diretamente em vez de `passlib` que só o wrappa)
4. **Usar constraints de versão restritivas** (`>=4.0.0,<5.0.0`) em vez de apenas lower bound (`>=1.7.4`) para dependências com histórico de breaking changes
5. **Generalização:** esse princípio se aplica a qualquer ecossistema — npm (pacotes abandonados), pip, gem, cargo — sempre verificar `last published` antes de escolher

---

## Lição 7 — CI/CD e Git: Infraestrutura de Versionamento Ausente do Epic 1

**Sprint / Story:** Epic 1 (Infraestrutura e Fundação)
**Severidade:** Média (não bloqueou desenvolvimento, mas criou dívida técnica de processo)

### O que aconteceu
Duas sprints foram completadas (Epic 1 completo + Story 2.1 e 2.2) sem que o repositório git fosse sequer inicializado. Não havia `git init`, não havia remote configurado, e não havia pipeline de CI/CD. Esses elementos foram adicionados manualmente após a demanda do usuário, fora do fluxo normal de desenvolvimento.

### Causa raiz
O Epic 1 foi definido pelos agentes com foco nos aspectos técnicos de código (API, frontend, design system) mas **omitiu as histórias de infraestrutura de versionamento e entrega contínua**, que são pré-requisitos para qualquer projeto profissional:

- Sem story de "git init + remote + branch strategy"
- Sem story de "CI pipeline (testes automáticos no PR)"
- Sem story de "CD pipeline (deploy automatizado)"

### Responsabilidade no BMAD

| Agente | Deveria ter feito |
|--------|-----------------|
| **Winston (Arquiteto)** | Incluir seção de CI/CD na `architecture.md` |
| **Bob (Scrum Master)** | Questionar ausência de stories de versionamento no sprint planning |
| **Dev Agent** | Criar `.github/workflows/*.yml` como parte de qualquer story de infrastructure |

### Sugestão de evolução para o agente (genérica)

O agente deve aplicar um **"Princípio de Infraestrutura Mínima de Entrega"**: todo Epic 1 (ou equivalente) de qualquer projeto **deve** incluir obrigatoriamente:

1. **Story de Versionamento:** `git init`, branch strategy (main/develop/feature), `.gitignore`, `.gitattributes`
2. **Story de CI:** Pipeline de testes automáticos disparado no PR (GitHub Actions, GitLab CI, CircleCI, etc.)
3. **Story de CD:** Pipeline de deploy para ambiente de staging (mínimo) com rollback automatizado
4. **Generalização:** Isso se aplica independente de linguagem, framework ou plataforma — é um prerequisito universal para projetos de software profissionais

### Action item para este projeto

A story de CI/CD deve ser criada e adicionada ao backlog antes do início do Epic 3:
- `POST /register` e `POST /login` devem passar em CI antes de qualquer PR ser mergeado
- Deploy automatizado no Docker Hub ou registry equivalente

---

## Tópicos para Discussão na Sessão de Evolução de Agentes





## Lição 8 — Migrations Alembic: Diferença entre Ambiente de Teste e Produção

**Sprint / Story:** Story 2.3 (RefreshToken model)
**Severidade:** Alta (bloqueou o uso da funcionalidade em produção)

### O que aconteceu
O modelo `RefreshToken` foi criado e testado com sucesso (41/41 testes passando), mas ao usar o frontend integrado à API em PostgreSQL, o endpoint `/register` retornou **500 Internal Server Error** com erro CORS. A causa real era que a tabela `refresh_tokens` não existia no PostgreSQL — apenas no SQLite em memória dos testes.

### Causa raiz
Os testes usam `Base.metadata.create_all()` — que cria todas as tabelas automaticamente. O PostgreSQL de produção depende de **Alembic migrations** explícitas. Ao adicionar o modelo `RefreshToken`, a migration correspondente não foi gerada nem aplicada.

### Regra de ouro (para o agente)
> **Toda nova model = nova migration Alembic.** Após criar um modelo, gerar e aplicar a migration é tão obrigatório quanto escrever os testes.

### Checklist de conclusão de story com nova model
1. `[ ]` Model criado e testado
2. `[ ]` `alembic revision --autogenerate -m "feat: <descrição>"` executado
3. `[ ]` Migration revisada (verificar que não destruiu tabelas existentes)
4. `[ ]` `alembic upgrade head` aplicado no ambiente de staging/produção
5. `[ ]` Verificado via `alembic current` que a migração foi aplicada

### Solução aplicada
```bash
docker compose exec api alembic revision --autogenerate -m "feat: add refresh_tokens table (Story 2.3)"
docker compose exec api alembic upgrade head
docker compose restart api
```

---

## Lição 9 — Circular Import e Validação do Build Docker no CI

**Sprint / Story:** Story 2.3 (RefreshToken model) / Epic 2 Retrospectiva
**Severidade:** Alta (bloqueou a API em produção; não foi detectado pelos testes)

### O que aconteceu
Ao adicionar `RefreshToken` em `models.py`, a importação foi feita também em `base.py` por conveniência. Isso criou um ciclo: `models.py → base.py → models.py`. O problema só apareceu quando o container Docker tentou inicializar a API — os testes (SQLite em memória) passavam normalmente.

### Causa raiz
Duas falhas combinadas:
1. **Violação de regra de arquitetura:** a relação de dependência entre `models` e `base` deve ser **unidirecional** — models importam de base, nunca o contrário. Isso é regra fundamental do SQLAlchemy e foi violada por conveniência.
2. **CI não valida o build Docker:** o pipeline de CI executa `pytest` mas não faz `docker build` + `docker run` como gate obrigatório. Um circular import que impede o boot da API não é detectável apenas com pytest.

### Regra de ouro (para o agente)
> **Models importam de `base.py`, nunca o contrário.** A importação de models para Alembic/testes deve ser feita nos arquivos consumidores (`env.py`, `conftest.py`), nunca em `base.py`.

### Action item para Epic 3
- [ ] Adicionar step `docker build` + `docker run --rm api pytest tests/ -v` no `ci.yml` como gate obrigatório
- [ ] Incluir `docker compose up -d && docker compose exec api alembic upgrade head` no healthcheck de staging

---

## Lição 10 — Framework ESAA: Consideração para Pós-MVP

**Sprint / Story:** Epic 2 Retrospectiva (insight estratégico de Glauber Costa)
**Categoria:** Decisão estratégica de tooling — registrado para revisão pós-MVP

### Contexto
Glauber Costa possui experiência direta com o framework **ESAA (Event Sourced Agent Architecture)** e sua metodologia de geração de código. A abordagem do ESAA — com contratos de agente, fluxo `claim → complete → review` e event sourcing — oferece garantias de rastreabilidade e qualidade que o fluxo atual (BMAD direto) não provê formalmente.

### Decisão
**Não utilizar ESAA no MVP atual.** O time optou por manter o BMAD como orquestrador de desenvolvimento para garantir velocidade de entrega no MVP. O modelo atual está funcionando bem com Conventional Commits, CI/CD via GitHub Actions e TDD.

### Razão para registrar
A experiência do Glauber com o ESAA deixou-o confiante na metodologia para projetos com maior rigor de processo. Após o MVP, avaliar:
1. Introduzir ESAA para os epics de features críticas (LLM, multi-tenant avançado)
2. Usar ESAA como framework de auditoria de qualidade, em paralelo com o BMAD
3. Migrar o pipeline de dev para ESAA em uma segunda fase do produto

### Critério de reavaliação
Quando: após conclusão do Epic 5 (MVP funcional com LLM integrado) ou se o time identificar degradação de qualidade recorrente não capturada pelos testes atuais.

---

## Lição 11 — Cobertura de Testes Frontend: ACs Implícitas São ACs Ausentes

**Sprint / Story:** Epic 3 (Stories 3.2–3.5 — Frontend)
**Severidade:** Média (lacuna de qualidade detectada na revisão pós-implementação)

### O que aconteceu

As stories de frontend do Epic 3 (3.2 Dashboard, 3.3 Criação/Edição, 3.4 Detalhe, 3.5 Arquivamento) foram implementadas com qualidade visual e funcional, mas **sem testes automatizados**. A lacuna só foi identificada após a conclusão das stories, quando o usuário perguntou explicitamente se os testes tinham sido desenvolvidos.

Ao rodar `npm run test:coverage` após a correção:
- **Antes:** 65% statements / 64% branches / 55% functions (abaixo do threshold de 70%)
- **Depois (com 15 testes adicionais):** ~73%+ global, 100% em `ArchiveConfirm`, 92% em `ProjectModal`

A story de backend equivalente (3.1) tinha AC explícita: *"Testes: CRUD, isolamento, arquivamento, paginação, coverage ≥ 80%"* — o que garantiu TDD. As stories de frontend não tinham esse requisito escrito.

### Causa raiz

**ACs implícitas não existem.** Se um critério de aceitação não está escrito na story, o agente não o executa. A cobertura de testes no backend estava explicitamente nos ACs; no frontend, foi assumida como "óbvia" mas não documentada.

### Regra de ouro (para o agente)

> **Toda story que envolve componentes com lógica de negócio DEVE incluir um AC de testes:**
> - Backend: `coverage ≥ 80%` nos arquivos do módulo
> - Frontend: testes para validações, estados de loading/erro e interações críticas

### Padrão a adotar a partir do Epic 4

Incluir em TODA story de frontend o AC:

```
- Testes: [componente principal] cobre os fluxos:
  - Estado de loading/erro
  - Validação de formulário (se aplicável)
  - Interação principal (click, submit)
  - Cobertura de linha ≥ 75% no componente
```

### Action item

- [x] Criados testes retroativos para `ProjectModal` (11), `ArchiveConfirm` (7), `ProjectCard` (9), `ProtectedRoute` (4), `AuthContext` (6), `useProjects` (5)
- [ ] Template de story frontend atualizado com AC de testes como campo obrigatório
- [ ] Threshold de coverage no `vite.config.ts` ajustado para 75% e com enforcement (exit code 1)

---

## Lição 11 — Amnésia Arquitetural e Perda de Contexto na Troca de Agentes

**Sprint / Story:** Epic 4 (Backend Documents e Testes)
**Severidade:** Alta (Geração de código fora do padrão esperado, reescrita de testes, bypass acidental da regra de isolamento `TenantScope` e gasto desnecessário de iterações/tokens)

### O que aconteceu
Durante a implementação das rotas de Documentos e de seus testes, o código inicial ignorou padrões estabelecidos no Epic 3. O agente original (ou o recém instanciado) tentou usar fixtures de Pytest (`client_a`, `client_b`) que não existiam ou não eram o padrão do `conftest.py` (que exigia envio de cabeçalhos de token genéricos), e quase gerou queries de banco sem a injeção estrita da clausula de TenantScope.

### Causa raiz
**O mito da "Onisciência" do Agente.** Acreditamos erroneamente que o agente "lê" toda a base de código a cada novo prompt. Na verdade, a janela de contexto vaza. Um agente novo que entra no meio do projeto tende a escrever código "padrão genérico de framework" (boilerplate de FastAPI/SQLAlchemy) se não for forçado a ler as regras arquiteturais locais ANTES de começar a codificar. O agente não sabia, "de cor", que neste projeto a regra de testes era usar `_auth(token)` ou que a segurança dependia do `TenantScope`.

### Sugestão de evolução para o agente (genérica) / Padrão BMAD
Para contornar o desperdício financeiro e temporal:

1. **Uso de "Project Context" Condensado:** Precisamos manter um arquivo `project-context.md` ou regras estritas dentro da pasta `.cursorrules` ou `architecture.md` altamente destiladas contendo: "Padrão de Autenticação em testes: use X. Isolamento SQLAlchemy: obrigatoriamente use TenantScope".
2. **Reconhecimento de Terreno Obrigatório (Read-Before-Write):** Em toda nova *Story*, o Agente de Desenvolvimento (`quick-dev` ou `dev-story`) **deve obrigatoriamente** inspecionar o código de um domínio pré-existente (por exemplo, ler `test_projects.py` antes de criar `test_documents.py`) para injetar a *Golden Meta-Pattern* em sua memória RAM instantânea (contexto local).
3. **BMAD Check Readiness:** Antes da codificação (quando rodamos a preparação de História), a story deve ter um checklist arquitetural que aponte explicitamente quais padrões de projetos já existentes ela deve clonar/respeitar.

### Action Item
- [x] Documentar a "Amnésia Arquitetural" como fator de risco.
- [x] Criado `project-context.md` na raiz com regras de TenantScope, testes e theming.

---

## Lição 12 — Stories Órfãs: Código Entregue mas Status Abandonado

**Sprint / Story:** Epic 3 / Story 3.4 (Detalhe do Projeto com Boas-vindas Contextuais)
**Severidade:** Média (não afetou o produto, mas contaminou o rastreamento de sprint e gerou confusão sobre o estado real do projeto)

### O que aconteceu

A Story 3.4 foi implementada por completo (`ProjectDetailPage.tsx` com WelcomeScreen, checklist de progresso, estados vazio e com sessões), mas o `sprint-status.yaml` permaneceu com `3-4: in-progress` e `epic-3: in-progress`. Isso só foi detectado quando um novo agente assumiu a sessão para o Epic 5 e verificou o estado do ficheiro de rastreamento.

Ao mesmo tempo, não havia ficheiro de story criado para 3.2, 3.3, 3.4 nem 3.5 na pasta de artefatos de implementação — apenas para 3.1. Ou seja, as stories de frontend do Epic 3 foram implementadas "ao vivo" sem o rito formal de `create-story` → ficheiro `.md` na pasta de artefatos.

### Causa raiz

**A cerimónia de encerramento está desacoplada da entrega do código.** No fluxo BMAD, quem marca a story como `done` no `sprint-status.yaml` é o agente ou o humano *por fora* da implementação — é um acto manual e cerimonial. Quando múltiplas stories são implementadas em sequência rápida (especialmente num epic de frontend onde o ritmo é mais veloz), o rastreamento fica para trás. O problema agrava-se quando:

1. **Transição entre epics sem gate de verificação** — O Epic 4 iniciou sem que o agente (ou o humano) verificasse se todas as stories do Epic 3 estavam formalmente fechadas.
2. **Ausência de ficheiros de story formalizados** — Sem o rito de `create-story` a gerar os ficheiros `.md` individuais, desaparece o artefacto que serve de checklist e "contrato" entre o agente e o sprint status.
3. **Troca de agente/sessão** — O novo agente herda o `sprint-status.yaml` mas não tem contexto sobre o que foi implementado na sessão anterior, assumindo que `in-progress` significa "incompleto".

### Sugestão de evolução (genérica)

> **Regra do "Gate de Transição entre Epics":** Antes de iniciar qualquer story do Epic N+1, o agente (ou o humano) DEVE verificar se todas as stories do Epic N estão marcadas como `done` no sprint-status. Se houver alguma em `in-progress` ou `backlog`, deve-se investigar se o código já existe e formalizar o status antes de prosseguir.

> **Regra da "Story Formal":** Cada story implementada deve ter o seu ficheiro `.md` correspondente na pasta de artefatos de implementação. A ausência desse ficheiro é um sinal de que o processo foi atropelado. O ficheiro serve como contrato mínimo de rastreabilidade.

### Action Item
- [x] Story 3.4 e Epic 3 fechados formalmente no `sprint-status.yaml`.
- [ ] Considerar adicionar, no workflow `bmad-sprint-planning` ou `bmad-create-story`, um passo de validação automática que verifique se o epic anterior está completamente `done` antes de gerar novas stories.

---

*Última atualização: 2026-03-31 | Sessão: Epic 5 — Fase de Elicitação*
