# Story 2.4: TenantMixin e Isolamento de Dados no Banco

Status: in-progress

## Story

As a desenvolvedor do ReqStudio,
I want um mecanismo que garanta que toda query de negócio filtre por tenant_id,
So that dados de um tenant jamais sejam acessíveis por outro.

## Acceptance Criteria

1. `TenantScope` — utilitário que encapsula queries com `where(Model.tenant_id == tenant_id)`
2. `get_tenant_scope` — dependency FastAPI que combina `get_db` + `get_tenant_id` + `TenantScope`
3. Conftest atualizado com fixture `tenant_a` e `tenant_b` (dois usuários, dois tenants)
4. CRUD com `tenant_a` não retorna dados de `tenant_b` (isolamento completo)
5. Modelo sem `tenant_id` → NOT NULL constraint
6. Testes: isolamento completo, anti-leakage, coverage ≥ 80%

## Tasks

- [x] Task 1: TenantScope (AC: #1, #2)
  - [x] 1.1 `app/db/tenant.py` com classe `TenantScope` e método `select()`
  - [x] 1.2 `get_tenant_scope` dependency

- [x] Task 2: Conftest (AC: #3)
  - [x] 2.1 Adicionar fixtures `tenant_a_token` e `tenant_b_token`

- [x] Task 3: Testes de Isolamento (AC: #4, #5, #6)
  - [x] 3.1 `tests/test_tenant_isolation.py`

## Dev Notes

- `TenantScope` `é um registry + query builder: não é middleware
- Toda model de negócio DEVE usar `TenantMixin` (verificado em test_tenant_isolation)
- Padrão para futuros módulos: injetar `TenantScope` via `Depends(get_tenant_scope)`
- NOT NULL do tenant_id é garantido pelo SQLAlchemy ORM, não precisa de teste de integração extra

## Dev Agent Record

### Agent Model Used
Antigravity (Google Deepmind)

### File List
- `reqstudio/reqstudio-api/app/db/tenant.py`
- `reqstudio/reqstudio-api/tests/conftest.py` (fixtures tenant_a/b)
- `reqstudio/reqstudio-api/tests/test_tenant_isolation.py`
