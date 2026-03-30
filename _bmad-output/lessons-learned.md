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





1. **Compatibilidade com BMAD original:** Como adicionar verificações de infraestrutura sem quebrar o contrato do workflow upstream?
2. **Scripts de setup como entregável:** Tornar scripts de setup um entregável obrigatório para stories de inicialização de serviços?
3. **Instruções para o usuário:** O agente deve agrupar todos os comandos do usuário em uma única mensagem no início da story?
4. **Ambientes de desenvolvimento compartilhados:** Como o agente deve lidar com máquinas que rodam múltiplos projetos simultaneamente?

---

*Última atualização: 2026-03-30 | Sessão: Sprint 1 / Stories 1.1–1.2*
