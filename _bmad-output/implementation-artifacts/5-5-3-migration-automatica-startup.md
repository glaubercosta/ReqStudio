# Story 5.5-3: Migration Automática no Startup

Status: done

## Story

As a DevOps / Dev,
I want que `alembic upgrade head` seja executado automaticamente no startup do container da API,
So that o banco de dados esteja sempre atualizado sem passos manuais — eliminando a causa raiz que gerou loss de dados no Epic 5 (tabelas `sessions`, `messages` e `workflows` ausentes em produção).

## Acceptance Criteria

1. **Given** o container `reqstudio-api` inicia (via `docker compose up`)  
   **When** a aplicação FastAPI está inicializando  
   **Then** `alembic upgrade head` é executado automaticamente antes de aceitar requisições

2. **Given** as migrations já estão aplicadas (banco atualizado)  
   **When** o container reinicia  
   **Then** a execução de `alembic upgrade head` é idempotente — sem erros, sem reprocessamento

3. **Given** uma migration falha durante o startup  
   **When** a exception do Alembic é capturada  
   **Then** a aplicação aborta com `sys.exit(1)` e o erro é logado com nível `CRITICAL`

4. **Given** o ambiente é de teste (`TESTING=true` ou `DATABASE_URL` aponta para DB de teste)  
   **When** o startup inicializa  
   **Then** a migration automática é **pulada** — testes gerenciam suas próprias tabelas via `create_all`/`drop_all`

5. **Given** um novo modelo SQLAlchemy é adicionado no futuro  
   **When** o desenvolvedor faz revision com Alembic e sobe o container  
   **Then** a migration nova é aplicada automaticamente no próximo startup sem nenhum passo manual adicional

## Tasks / Subtasks

- [x] **Task 1: Criar `app/db/migrations.py`** — função `run_migrations_on_startup()` (AC: 1, 2, 3, 4)
  - [x] Importar `alembic.config.Config` e `alembic.command.upgrade`
  - [x] Detectar se é ambiente de teste via `settings.TESTING`
  - [x] Se teste → `logger.info("Skipping migrations in test environment")` + return
  - [x] Instanciar `Config` apontando para `alembic.ini` no root do projeto (usando `pathlib.Path(__file__)` para path relativo robusto)
  - [x] Chamar `upgrade(config, "head")`
  - [x] Envolver em `try/except Exception` → `logger.critical(...)` + `sys.exit(1)`
  - [x] Logging de início/fim adicionado

- [x] **Task 2: Integrar em `app/main.py`** — lifespan context manager (AC: 1, 2, 3)
  - [x] Criado `async def lifespan(app: FastAPI)` com `contextlib.asynccontextmanager`
  - [x] `run_migrations_on_startup()` chamado no início do lifespan (startup)
  - [x] `lifespan=lifespan` passado para o construtor `FastAPI(...)`
  - [x] Não usa `@app.on_event("startup")` deprecated
  - [x] Migration roda antes de aceitar requisições (antes do `yield`)

- [x] **Task 3: Adicionar `TESTING` config em `Settings`** (AC: 4)
  - [x] Em `app/core/config.py`: adicionado `TESTING: bool = False`
  - [x] Padrão `False` — testes devem setar via `monkeypatch.setattr(settings, 'TESTING', True)`

- [x] **Task 4: Testes** (AC: 1, 2, 3, 4)
  - [x] Criado `app/db/tests/__init__.py`
  - [x] Criado `app/db/tests/test_migrations_startup.py` com 7 cenários
  - [x] Testar: `TESTING=True` → `upgrade` **não** é chamado
  - [x] Testar: `TESTING=False` → `upgrade` é chamado com `"head"`
  - [x] Testar: exception em `upgrade` → `sys.exit(1)` é chamado
  - [x] Testar: sucesso → `sys.exit` **não** é chamado
  - [x] Testar: log CRITICAL em falha e log INFO no skip
  - [x] Usando `unittest.mock.patch` + `monkeypatch` do pytest

## Dev Notes

### Causa Raiz (Retro Epic 5 — Action Item A5 / Carry-over AI-2 do Epic 2)

> "AI-2 ignorado no Epic 2 causou problema real no Epic 5. Tabelas `workflows`, `sessions`, `messages` não existiam no banco de produção — causou perda de tempo significativa no teste manual."

O `CMD` atual do `Dockerfile` apenas inicia o `uvicorn`, sem executar migrações:
```dockerfile
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

A abordagem adotada é **startup hook via lifespan** (não entrypoint shell script), por ser mais idiomática com FastAPI e mais fácil de testar isoladamente.

### Análise do Código Existente

#### `app/main.py` — Situação Atual

```python
def create_app() -> FastAPI:
    setup_telemetry()  # ← roda antes da criação do app

    app = FastAPI(
        title="ReqStudio API",
        ...
    )
    # ... configurações, routers ...
    return app

app = create_app()
```

O `create_app` **não tem lifespan**. A Task 2 introduz o `lifespan` context manager, que é o padrão recomendado pelo FastAPI ≥ 0.90+ (substitui `@app.on_event("startup")`).

#### `alembic/env.py` — Já Corretamente Configurado

O `env.py` já importa **todos** os models:
```python
from app.modules.auth.models import RefreshToken, Tenant, User
from app.modules.documents.models import Document, DocumentChunk
from app.modules.projects.models import Project
from app.modules.sessions.models import Session, Message
from app.modules.workflows.models import Workflow, WorkflowStep, Agent
```
✅ Autogenerate funcionará corretamente.

#### Configuração de Path do `alembic.ini`

O `alembic.ini` está na raiz de `reqstudio-api/`. O container tem `WORKDIR /app` apontando para essa raiz. Portanto, o path deve ser resolvido assim:

```python
# app/db/migrations.py
from pathlib import Path

def _get_alembic_config() -> Config:
    # __file__ = /app/app/db/migrations.py
    # root = /app (raiz do projeto onde fica alembic.ini)
    root = Path(__file__).parent.parent.parent
    cfg = Config(str(root / "alembic.ini"))
    return cfg
```

#### Detecção de Ambiente de Teste

O `conftest.py` dos testes deve setar `TESTING=true` via env var. Verificar se já existe essa convenção:

```python
# conftest.py (hipotético)
os.environ["TESTING"] = "true"
```

Se não existir, a Task 3 adiciona `TESTING: bool = False` ao `Settings` e o `conftest.py` deve ser atualizado (ou o test pode mockar a função diretamente).

### Padrão de Lifespan FastAPI (Task 2)

```python
# app/main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.db.migrations import run_migrations_on_startup

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: runs startup and shutdown logic."""
    run_migrations_on_startup()  # sync — alembic é síncrono
    yield
    # shutdown logic aqui se necessário

def create_app() -> FastAPI:
    setup_telemetry()

    app = FastAPI(
        title="ReqStudio API",
        lifespan=lifespan,  # ← novo
        ...
    )
    ...
    return app
```

### Implementação de `run_migrations_on_startup()` (Task 1)

```python
# app/db/migrations.py
import logging
import sys
from pathlib import Path

from alembic import command
from alembic.config import Config

from app.core.config import settings

logger = logging.getLogger(__name__)


def run_migrations_on_startup() -> None:
    """Run Alembic migrations at app startup.

    Skipped in test environments (TESTING=True).
    On failure, logs CRITICAL and calls sys.exit(1).
    """
    if settings.TESTING:
        logger.info("Skipping Alembic migrations in test environment")
        return

    logger.info("Running Alembic migrations...")
    try:
        cfg = _get_alembic_config()
        command.upgrade(cfg, "head")
        logger.info("Alembic migrations complete")
    except Exception as exc:
        logger.critical("Alembic migration failed: %s", exc, exc_info=True)
        sys.exit(1)


def _get_alembic_config() -> Config:
    root = Path(__file__).parent.parent.parent  # /app/ (projeto root)
    return Config(str(root / "alembic.ini"))
```

### Padrão de Testes (Task 4)

```python
# app/db/tests/test_migrations_startup.py
from unittest.mock import patch, MagicMock

def test_skips_when_testing(monkeypatch):
    monkeypatch.setattr("app.db.migrations.settings.TESTING", True)
    with patch("app.db.migrations.command.upgrade") as mock_upgrade:
        from app.db.migrations import run_migrations_on_startup
        run_migrations_on_startup()
        mock_upgrade.assert_not_called()

def test_runs_upgrade_head(monkeypatch):
    monkeypatch.setattr("app.db.migrations.settings.TESTING", False)
    with patch("app.db.migrations.command.upgrade") as mock_upgrade:
        from app.db.migrations import run_migrations_on_startup
        run_migrations_on_startup()
        mock_upgrade.assert_called_once()
        args = mock_upgrade.call_args
        assert args[0][1] == "head"

def test_exits_on_migration_failure(monkeypatch):
    monkeypatch.setattr("app.db.migrations.settings.TESTING", False)
    with patch("app.db.migrations.command.upgrade", side_effect=Exception("DB error")):
        with patch("app.db.migrations.sys.exit") as mock_exit:
            from app.db.migrations import run_migrations_on_startup
            run_migrations_on_startup()
            mock_exit.assert_called_once_with(1)
```

> **Nota:** Usar `importlib.reload` ou fixtures de isolamento se o módulo já estiver importado em outros testes da sessão.

### Convenções de Código

- Alembic é **síncrono** internamente — `run_migrations_on_startup()` é `def`, não `async def`
- Chamá-la dentro de `lifespan` (que é `async`) está correto; bloquear o event loop no startup é aceitável (raramente é o gargalo)
- Se futuro desejar async, usar `asyncio.to_thread(run_migrations_on_startup)` no lifespan
- Logging: padrão `logger.info(...)` / `logger.critical(...)` — sem `print()`

### Project Structure

- **Novo:** `reqstudio/reqstudio-api/app/db/migrations.py`
- **Novo:** `reqstudio/reqstudio-api/app/db/tests/__init__.py`
- **Novo:** `reqstudio/reqstudio-api/app/db/tests/test_migrations_startup.py`
- **Modificado:** `reqstudio/reqstudio-api/app/main.py` (adicionar `lifespan`)
- **Modificado:** `reqstudio/reqstudio-api/app/core/config.py` (adicionar `TESTING`)

### Learnings das Stories Anteriores

- Diretório de testes pode não existir — criar `__init__.py` primeiro (aprendido na 5.5-2)
- `pyproject.toml` já inclui `testpaths = ["tests", "app"]` → novos testes descobertos automaticamente
- Logging padrão: `logger.info()`, não `print()`

### References

- [Source: epic-5-retro-2026-03-31.md — Action Item A5 / Carry-over AI-2]
- [Source: reqstudio-api/Dockerfile — CMD atual sem migrations]
- [Source: reqstudio-api/alembic/env.py — env configurado com todos os models]
- [Source: reqstudio-api/app/main.py — create_app sem lifespan]
- [Source: reqstudio-api/app/core/config.py — Settings sem TESTING flag]
- [FastAPI Lifespan docs: https://fastapi.tiangolo.com/advanced/events/#lifespan]

## Dev Agent Record

### Agent Model Used

Claude Sonnet 4.6 (Thinking) via Antigravity — 2026-04-02

### Debug Log References

- `alembic` é síncrono — `run_migrations_on_startup()` é `def`, não `async def`. Chamá-la em `lifespan` (async) bloqueia o event loop por instantes durante startup — aceitável.
- O path de `alembic.ini` é resolvido com `Path(__file__).resolve().parent.parent.parent` para ser robusto em qualquer `WORKDIR` do container.
- `TESTING` flag adicionada ao `Settings` — testes usam `monkeypatch.setattr` em vez de env var para evitar side-effects entre testes.
- `importlib.reload(mod)` nos testes garante que mudanças de `monkeypatch` são refletidas no módulo.

### Completion Notes List

- **Task 1:** `app/db/migrations.py` criado com `run_migrations_on_startup()` (skip em TESTING, upgrade head, exit(1) em falha, logging completo) e `_get_alembic_config()` (path robusto via pathlib).
- **Task 2:** `app/main.py` atualizado com `lifespan` context manager usando `@asynccontextmanager`. `FastAPI(lifespan=lifespan, ...)`. Nenhum `@app.on_event` foi usado.
- **Task 3:** `TESTING: bool = False` adicionado ao `Settings` em `config.py`. Compatível com Pydantic Settings v2.
- **Task 4:** 7 testes unitários criados em `app/db/tests/test_migrations_startup.py`. Cobrem: skip, upgrade chamado com 'head', exit(1) em falha, no-exit em sucesso, revision=head, log CRITICAL em falha, log INFO no skip.

### Change Log

- 2026-04-02: Criado `app/db/migrations.py` com `run_migrations_on_startup()` e `_get_alembic_config()`
- 2026-04-02: `app/main.py` — adicionado `lifespan` context manager com migration hook; `FastAPI(lifespan=lifespan)`
- 2026-04-02: `app/core/config.py` — adicionado `TESTING: bool = False` ao `Settings`
- 2026-04-02: Criados testes: `app/db/tests/__init__.py` e `app/db/tests/test_migrations_startup.py` (7 cenários)

### File List

- `reqstudio/reqstudio-api/app/db/migrations.py` (CREATE)
- `reqstudio/reqstudio-api/app/db/tests/__init__.py` (CREATE)
- `reqstudio/reqstudio-api/app/db/tests/test_migrations_startup.py` (CREATE)
- `reqstudio/reqstudio-api/app/main.py` (MODIFY)
- `reqstudio/reqstudio-api/app/core/config.py` (MODIFY)
