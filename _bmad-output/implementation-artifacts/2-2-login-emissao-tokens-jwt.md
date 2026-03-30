# Story 2.2: Login e Emissão de Tokens JWT

Status: in-progress

## Story

As a usuário registrado,
I want fazer login e receber tokens de acesso,
So that eu possa acessar meus projetos de forma segura.

## Acceptance Criteria

1. `POST /api/v1/auth/login` com credenciais corretas retorna `access_token` (JWT 15min) no corpo
2. `refresh_token` (JWT 7d) definido como httpOnly cookie (`SameSite=Strict`, `Secure=True`)
3. JWT claims: `user_id`, `tenant_id`, `exp`, `iat`
4. Credenciais erradas → Guided Recovery `INVALID_CREDENTIALS`
5. Dependencies `get_current_user` e `get_tenant_id` extraem claims do JWT
6. Testes: login sucesso, credenciais erradas, claims corretos, dependency funcionando

## Tasks / Subtasks

- [x] Task 1: Config (AC: #1, #2)
  - [x] 1.1 Adicionar `JWT_SECRET_KEY`, `ACCESS_TOKEN_EXPIRE_MINUTES`, `REFRESH_TOKEN_EXPIRE_DAYS` ao settings

- [x] Task 2: Security — JWT (AC: #1, #2, #3)
  - [x] 2.1 `create_access_token()` — JWT com claims user_id, tenant_id, exp, iat
  - [x] 2.2 `create_refresh_token()` — JWT com sub=user_id, exp 7d
  - [x] 2.3 `decode_token()` — verifica assinatura e retorna claims

- [x] Task 3: Dependencies (AC: #5)
  - [x] 3.1 `get_current_user` — extrai user do JWT no header Authorization
  - [x] 3.2 `get_tenant_id` — extrai tenant_id do JWT

- [x] Task 4: Auth Service (AC: #4)
  - [x] 4.1 `AuthService.authenticate()` — valida email+senha, levanta INVALID_CREDENTIALS

- [x] Task 5: Router (AC: #1, #2)
  - [x] 5.1 `POST /api/v1/auth/login` — gera tokens, seta cookie

- [x] Task 6: Testes (AC: #6)
  - [x] 6.1 test_login_success (token no body, cookie presente)
  - [x] 6.2 test_login_wrong_password
  - [x] 6.3 test_login_unknown_email
  - [x] 6.4 test_access_token_claims
  - [x] 6.5 test_get_current_user_dependency

## Dev Notes

- `python-jose[cryptography]` já está no requirements.txt (Story 2.1)
- `Secure=True` no cookie só funciona em HTTPS — desabilitado em DEBUG mode para dev local
- refresh_token em cookie httpOnly: browser envia automaticamente, frontend não acessa via JS
- TenantMiddleware permanece placeholder — dependencies são a forma correta no FastAPI

## Dev Agent Record

### Agent Model Used
Antigravity (Google Deepmind)

### File List

- `reqstudio/reqstudio-api/app/core/config.py`
- `reqstudio/reqstudio-api/app/core/security.py`
- `reqstudio/reqstudio-api/app/core/dependencies.py`
- `reqstudio/reqstudio-api/app/modules/auth/schemas.py`
- `reqstudio/reqstudio-api/app/modules/auth/service.py`
- `reqstudio/reqstudio-api/app/modules/auth/router.py`
- `reqstudio/reqstudio-api/tests/test_auth_login.py`
- `reqstudio/reqstudio-api/.env.example`
