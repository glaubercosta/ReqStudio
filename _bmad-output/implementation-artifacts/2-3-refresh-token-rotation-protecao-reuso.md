# Story 2.3: Refresh Token com Rotation e Proteção contra Reuso

Status: in-progress

## Story

As a usuário autenticado,
I want que minha sessão seja renovada automaticamente,
So that eu não perca meu trabalho durante sessão longa.

## Acceptance Criteria

1. `POST /api/v1/auth/refresh` aceita refresh_token do cookie httpOnly
2. Retorna novo `access_token` (corpo) + novo `refresh_token` (cookie) — token anterior invalidado (rotation)
3. Token já usado (reuse) → revoga TODOS os tokens do user → `TOKEN_REUSE_DETECTED` blocking
4. Token expirado → `SESSION_EXPIRED`
5. Modelo `RefreshToken` com: `id`, `user_id`, `token_hash`, `expires_at`, `used_at`, `revoked_at`
6. Testes: refresh sucesso, rotation, reuse detection + revogação em cascata, token expirado

## Tasks

- [x] Task 1: Model RefreshToken (AC: #5)
  - [x] model com campos necessários + relacionamento com User

- [x] Task 2: Atualização do Login (AC: #1)
  - [x] `authenticate()` passa a persistir RefreshToken no banco ao fazer login

- [x] Task 3: Service — refresh() (AC: #2, #3, #4)
  - [x] Lookup por hash do token recebido
  - [x] Detecção de reuse com revogação em cascata
  - [x] Rotation: marca usado, cria novo RefreshToken, emite novos tokens

- [x] Task 4: Router (AC: #1)
  - [x] `POST /api/v1/auth/refresh` lê cookie e retorna novos tokens

- [x] Task 5: Testes (AC: #6)

## Dev Notes

- `token_hash` = SHA-256 do JWT em hex — nunca armazena o token bruto
- Reuse detection: se token com `used_at` preenchido for apresentado → segurança comprometida
- `add TOKEN_REUSE_DETECTED` já existe no `ErrorCode` como `SESSION_EXPIRED` — usar o existente

## Dev Agent Record

### Agent Model Used
Antigravity (Google Deepmind)

### File List
- `reqstudio/reqstudio-api/app/modules/auth/models.py`
- `reqstudio/reqstudio-api/app/modules/auth/service.py`
- `reqstudio/reqstudio-api/app/modules/auth/router.py`
- `reqstudio/reqstudio-api/app/core/exceptions.py`
- `reqstudio/reqstudio-api/app/core/security.py`
- `reqstudio/reqstudio-api/tests/test_auth_refresh.py`
