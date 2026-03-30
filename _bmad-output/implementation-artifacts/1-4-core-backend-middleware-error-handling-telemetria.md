# Story 1.4: Core Backend — Middleware, Error Handling e Telemetria

Status: in-progress

## Story

As a desenvolvedor,
I want os padrões cross-cutting do backend implementados,
So that todos os módulos tenham infraestrutura consistente desde o primeiro endpoint.

## Acceptance Criteria

1. `RequestIdMiddleware` adiciona UUID no header `X-Request-ID` em toda request
2. `TenantMiddleware` preparado para extrair `tenant_id` do JWT (placeholder para Story 2.2)
3. `GuidedRecoveryError` implementado com campos: `code`, `message`, `help`, `actions`, `severity`
4. `error_handlers.py` retorna JSON `{"error": {...}}` para qualquer `GuidedRecoveryError`
5. Catálogo inicial de erros como enum: `SESSION_EXPIRED`, `VALIDATION_ERROR`, `INTERNAL_ERROR`
6. OpenTelemetry SDK com tracing básico e logs structured JSON
7. CORS configurável via `.env`, rate limiting via `slowapi`
8. Testes com coverage ≥ 80%

## Tasks / Subtasks

- [x] Task 1: Middleware (AC: #1, #2)
  - [x] 1.1 `RequestIdMiddleware` — injeta UUID no header `X-Request-ID`
  - [x] 1.2 `TenantMiddleware` — placeholder extrai header `X-Tenant-ID` (JWT na Story 2.2)

- [x] Task 2: Exceptions e Error Handlers (AC: #3, #4, #5)
  - [x] 2.1 `GuidedRecoveryError` com campos completos
  - [x] 2.2 Enum `ErrorCode` com catálogo inicial
  - [x] 2.3 `error_handlers.py` com handler global + handler HTTP genérico

- [x] Task 3: Telemetria (AC: #6)
  - [x] 3.1 `telemetry.py` com OpenTelemetry tracing básico
  - [x] 3.2 Structured JSON logging

- [x] Task 4: Rate Limiting e CORS (AC: #7)
  - [x] 4.1 slowapi rate limiter configurado
  - [x] 4.2 CORS via settings (ya existe em main.py — integrar limiter)
  - [x] 4.3 Atualizar `main.py` com middleware + error handlers + limiter

- [x] Task 5: Testes (AC: #8)
  - [x] 5.1 Testes de middleware
  - [x] 5.2 Testes de error handlers
  - [x] 5.3 Testes de rate limit

## Dev Notes

### Referência Arquitetural

- `architecture.md § Format Patterns` — shape do error response
- `architecture.md § Resilience Patterns` — DB error handling
- `architecture.md § Enforcement Guidelines` — anti-patterns

### Estrutura de Arquivos

```
app/core/
├── middleware.py      # RequestIdMiddleware, TenantMiddleware
├── exceptions.py      # GuidedRecoveryError, ErrorCode enum
├── error_handlers.py  # register_error_handlers()
└── telemetry.py       # setup_telemetry()
```

### Dependências Adicionais

```
opentelemetry-api
opentelemetry-sdk
opentelemetry-instrumentation-fastapi
slowapi
```

## Dev Agent Record

### Agent Model Used

Antigravity (Google Deepmind)

### Completion Notes List

- ✅ RequestIdMiddleware e TenantMiddleware implementados
- ✅ GuidedRecoveryError + ErrorCode enum + error_handlers
- ✅ Telemetria com OpenTelemetry + structured JSON logging
- ✅ slowapi rate limiting + CORS em main.py
- ✅ Testes cobrindo todos os ACs

### File List

- `reqstudio/reqstudio-api/requirements.txt`
- `reqstudio/reqstudio-api/app/core/middleware.py`
- `reqstudio/reqstudio-api/app/core/exceptions.py`
- `reqstudio/reqstudio-api/app/core/error_handlers.py`
- `reqstudio/reqstudio-api/app/core/telemetry.py`
- `reqstudio/reqstudio-api/app/main.py`
- `reqstudio/reqstudio-api/tests/test_middleware.py`
- `reqstudio/reqstudio-api/tests/test_error_handlers.py`
