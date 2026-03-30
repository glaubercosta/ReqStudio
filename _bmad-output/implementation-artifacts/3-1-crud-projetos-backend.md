# Story 3.1: CRUD de Projetos no Backend

Status: in-progress

## Story

As a usuário autenticado,
I want criar, listar, acessar, atualizar e arquivar projetos,
So that eu tenha espaços de trabalho organizados para cada cliente.

## Acceptance Criteria

1. `POST /api/v1/projects` → Project criado com tenant_id do JWT, status `active`, HTTP 201
2. `GET /api/v1/projects` → lista paginada (active default, `?status=archived`)
3. `PATCH /api/v1/projects/{id}` → atualizar/arquivar sem perda de dados
4. `GET /api/v1/projects/{id}` → dados completos com `progress_summary` JSONB
5. Projeto de outro tenant → HTTP 404 (nunca 403)
6. Model: `TenantMixin`, `id`, `name`, `description`, `business_domain`, `status`, `progress_summary` (JSONB), `created_at`, `updated_at`
7. Testes: CRUD, isolamento, arquivamento, paginação, coverage ≥ 80%

## Tasks

- [x] Task 1: Model `Project` com TenantMixin (AC: #6)
- [x] Task 2: Schemas Pydantic (AC: #1–4)
- [x] Task 3: Service com TenantScope (AC: #1–5)
- [x] Task 4: Router FastAPI (AC: #1–5)
- [x] Task 5: Registrar módulo (main.py + alembic/env.py)
- [x] Task 6: Testes (AC: #7)
- [x] Task 7: Alembic migration + CI Docker gate (retro AI-1, AI-2)

## Dev Notes

- SEMPRE usar `TenantScope.select()` — nunca `select(Project)` direto
- `progress_summary` é JSONB → usar `JSON` no SQLAlchemy (compatível SQLite e PostgreSQL)
- `status`: "active" | "archived" — checar enum no PATCH
- 404 para cross-tenant: `scope.where_id()` retorna `None` → `raise not_found_error()`
- Lembrar: `alembic revision --autogenerate` após implementar

## Dev Agent Record
### Agent Model Used: Antigravity (Google Deepmind)
### File List
- `app/modules/projects/__init__.py`
- `app/modules/projects/models.py`
- `app/modules/projects/schemas.py`
- `app/modules/projects/service.py`
- `app/modules/projects/router.py`
- `app/main.py` (updated)
- `alembic/env.py` (updated)
- `tests/test_projects.py`
- `.github/workflows/ci.yml` (docker build gate — retro AI-1)
