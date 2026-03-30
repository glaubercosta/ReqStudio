# Story 2.1: Registro de Usuário com E-mail e Senha

Status: in-progress

## Story

As a visitante do ReqStudio,
I want criar uma conta com e-mail e senha,
So that eu possa acessar a plataforma e iniciar meus projetos.

## Acceptance Criteria

1. `POST /api/v1/auth/register` disponível e retorna HTTP 201
2. User criado com senha bcrypt + tenant criado automaticamente
3. E-mail duplicado → Guided Recovery `EMAIL_ALREADY_EXISTS` (400)
4. Senha fraca (<8 chars) → Guided Recovery `WEAK_PASSWORD` (422)
5. Testes: registro sucesso, duplicado, senha fraca, isolamento multi-tenant

## Tasks / Subtasks

- [x] Task 1: Dependências (AC: base)
  - [x] 1.1 Adicionar `passlib[bcrypt]` e `email-validator` ao requirements.txt

- [x] Task 2: Models (AC: #2)
  - [x] 2.1 Model `User` — id, email, hashed_password, tenant_id
  - [x] 2.2 Model `Tenant` — id, name, created_at

- [x] Task 3: Schemas (AC: #1, #3, #4)
  - [x] 3.1 `UserCreate` com validação de email + senha ≥8 chars

- [x] Task 4: Service (AC: #2, #3, #4)
  - [x] 4.1 `AuthService.register()` — cria Tenant + User atomicamente
  - [x] 4.2 Verifica duplicidade de email → EMAIL_ALREADY_EXISTS
  - [x] 4.3 Valida senha fraca → WEAK_PASSWORD

- [x] Task 5: Router (AC: #1)
  - [x] 5.1 `POST /api/v1/auth/register` com schema Pydantic
  - [x] 5.2 Registrar router em `main.py`

- [x] Task 6: Database (AC: #2)
  - [x] 6.1 Migration Alembic: tabelas `users` e `tenants`
  - [x] 6.2 Registrar models em `db/base.py`

- [x] Task 7: Testes (AC: #5)
  - [x] 7.1 test_register_success
  - [x] 7.2 test_register_duplicate_email
  - [x] 7.3 test_register_weak_password
  - [x] 7.4 test_register_tenant_isolation

## Dev Notes

- `password` do schema → `hashed_password` com `passlib.bcrypt` antes de persistir
- Tenant criado com `name = email.split('@')[0]` como placeholder
- TenantMiddleware (Story 1.4) é placeholder — em 2.4 vai extrair do JWT
- Testes usam banco SQLite em memória (sem container Postgres necessário)

## Dev Agent Record

### Agent Model Used
Antigravity (Google Deepmind)

### File List
- `reqstudio/reqstudio-api/requirements.txt`
- `reqstudio/reqstudio-api/app/core/security.py`
- `reqstudio/reqstudio-api/app/modules/auth/__init__.py`
- `reqstudio/reqstudio-api/app/modules/auth/models.py`
- `reqstudio/reqstudio-api/app/modules/auth/schemas.py`
- `reqstudio/reqstudio-api/app/modules/auth/service.py`
- `reqstudio/reqstudio-api/app/modules/auth/router.py`
- `reqstudio/reqstudio-api/app/db/base.py`
- `reqstudio/reqstudio-api/app/db/session.py`
- `reqstudio/reqstudio-api/app/main.py`
- `reqstudio/reqstudio-api/tests/conftest.py`
- `reqstudio/reqstudio-api/tests/test_auth_register.py`
