# ReqStudio Project Context

This document contains critical architectural rules and patterns that **all AI agents must follow** when implementing code for the ReqStudio platform. 

## 1. Backend Architecture (FastAPI + SQLAlchemy)

### 1.1 Multi-Tenant Isolation (CRITICAL)
- **TenantMixin**: ALL database models must inherit from `TenantMixin`. This enforces a `tenant_id` column.
- **TenantScope**: ALL database queries MUST be filtered by the current user's `tenant_id`.
  - **Do NOT** write loose queries like `session.scalars(select(Project))`.
  - **MUST USE**: `session.scalars(select(Project).where(Project.tenant_id == tenant_scope.tenant_id))`
- The `tenant_scope` is injected into backend services via FastAPI Depends (`get_current_tenant_scope`).

### 1.2 Testing Conventions (Pytest)
- **Shared Client**: Do NOT use multiple `TestClient` fixtures (like `client_a` and `client_b`). We use a single shared client.
- **Authentication**: Authentication in tests must be done by passing the auth token explicitly in the headers: `headers=_auth(tenant_a_token)`.
- **Guided Recovery Errors**: All expected business errors must raise `GuidedRecoveryError` (which maps to specific HTTP status codes with `code`, `message`, `help` and `actions`) rather than basic `HTTPException`.
- **Coverage**: All backend modules must have `pytest` coverage **≥ 80%**.

## 2. Frontend Architecture (React + Vite + Tailwind)

### 2.1 State Management & API
- **TanStack Query**: Use `useQuery` for fetching and `useMutation` for writes.
- **Optimistic Invalidation**: Mutations must invalidate their respective queries on success (`queryClient.invalidateQueries({ queryKey: [...] })`).
- **File Uploads**: When using `fetch` with `FormData`, DO NOT manually set the `Content-Type` header. Let the browser generate the multipart boundary. The `request` wrapper in `apiClient.ts` handles this conditionally.

### 2.2 Styling and Theming (CRITICAL)
- **No Hardcoded Tailwind Colors**: Do NOT use static tailwind color classes like `bg-white`, `bg-slate-50`, `text-gray-800`.
- **Semantic Variables Only**: You MUST use the semantic CSS variables injected by the overarching theme:
  - Backgrounds: `bg-background`, `bg-card`, `bg-muted`
  - Text: `text-foreground`, `text-muted-foreground`
  - Borders: `border-border`
  - Feedback: `text-destructive`, `bg-destructive/10`, `text-emerald-500` (for No Hardcoded Tailwind Colors)
- **Dark Mode Support**: Using these semantic variables ensures the interface automatically adapts to Dark Mode without additional classes.

## 3. General Agent Directives
- **Read-Before-Write**: Before implementing a new module or test suite, agents MUST read an existing, working, related file (e.g., `test_projects.py` before creating `test_documents.py`) to absorb local conventions and avoid architectural amnesia.
- **Epic Gate**: Before starting Epic N+1, verify that ALL stories in Epic N are marked `done` in `sprint-status.yaml`. If any are `in-progress`, investigate whether the code is complete and close them formally first.

## 4. API Response Envelope (CRITICAL)
- **All endpoints** return data wrapped in `ApiResponse[T]`, which serializes as `{ "data": { ... } }`.
- The frontend expects this envelope universally — never return "naked" JSON from an endpoint.
- Import: `from app.schemas.response import ApiResponse`
- Usage: `return ApiResponse(data=result)`

## 5. Module Architecture (Quartet Pattern)
Every backend module follows a strict 4-file structure:
```
app/modules/<domain>/
├── models.py    # SQLAlchemy models (TenantMixin + Base)
├── schemas.py   # Pydantic v2 schemas (model_validate)
├── service.py   # Business logic (receives TenantScope)
└── router.py    # FastAPI endpoints (Depends(get_tenant_scope))
```
- Services receive `TenantScope` as first argument — never raw `AsyncSession`.
- Routers inject `scope: TenantScope = Depends(get_tenant_scope)` on every endpoint.
- New modules must be registered in `app/main.py` via `app.include_router(router, prefix="/api/v1")`.

## 6. Error Handling (GuidedRecoveryError)
- All user-visible errors MUST be `GuidedRecoveryError` instances (never raw `HTTPException`).
- Use factory functions from `app/core/exceptions.py` — e.g., `not_found_error("sessão")`, `validation_error("...")`.
- The `ErrorCode` enum in `exceptions.py` is the single source of truth for error codes. Add new codes there, not inline.
- Cross-tenant access MUST return 404 (not 403) — never reveal existence of resources across tenants.

## 7. AI-Human Interaction Protocol (Terminal Restricted Mode)

Due to IDE/Sandbox limitations in executing commands within Docker/Windows environments, agents MUST follow these rules:

### 7.1 No Assumption of Command Success
If the agent cannot verify command execution directly:
- **Do NOT** assume a command passed (especially migrations, tests, or builds).
- **Stop and Request**: Explicitly provide the EXACT command to the USER in a markdown block.
- **Intent Documentation**: Explain the expected result of the command before the user runs it.

### 7.2 Explicit Hand-off Rites
- Update the `task.md` with `[ ] Waiting for Manual Execution: [Command]`.
- Do NOT proceed with dependent code changes until the USER provides the terminal output in the conversation.
- **Verification Gate**: After the USER provides output, the agent MUST analyze it for errors before marking the task as done.

### 7.3 Scope Lock (BMAD Agent Execution)
- Every implementation cycle MUST start by selecting the BMAD workflow/agent (e.g., `bmad-dev-story`, `bmad-correct-course`) and explicitly listing target artifacts before editing.
- Planned file list first: the agent must declare which files are expected to change and keep edits restricted to this list unless the user approves expansion.
- After edits, run a scope check (`git status` or equivalent) and classify changes as: planned / benign tooling / out-of-scope.
- If out-of-scope changes appear, STOP and request user direction before continuing.
- Cache, dump, and local tooling outputs (e.g., `.mypy_cache`, `saida.txt`) must never be part of deliverables.
