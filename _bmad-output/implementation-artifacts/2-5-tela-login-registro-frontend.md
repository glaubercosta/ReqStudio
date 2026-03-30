# Story 2.5: Tela de Login e Registro no Frontend

Status: in-progress

## Story

As a Ana (especialista de domínio),
I want uma tela de login limpa e acolhedora,
So that eu me sinta segura para criar minha conta ou fazer login.

## Acceptance Criteria

1. Rota `/login` com campos e-mail/senha, botão "Entrar", link "Criar conta"
2. Modo registro: e-mail + senha + confirmação, validação inline
3. Sucesso → token em memória (`AuthContext`) → redirect `/projects`
4. Erros Guided Recovery inline (UX-DR16)
5. `apiClient` intercepta 401 → refresh → retry → redirect login
6. Responsivo 360px+, design tokens do Story 1.3
7. `AuthContext` expõe `user`, `login()`, `logout()`, `register()`, `isAuthenticated`
8. `ProtectedRoute` redireciona para `/login` se não autenticado

## Tasks

- [x] Task 1: AuthContext (AC: #3, #7)
  - [x] Token em memória (não localStorage)
  - [x] Silent refresh ao montar app
  - [x] login(), logout(), register()

- [x] Task 2: apiClient com interceptor 401 (AC: #5)
  - [x] 401 → POST /refresh → retry → redirect login

- [x] Task 3: LoginPage polida (AC: #1, #2, #4, #6)
  - [x] Senha com confirmação no modo registro
  - [x] Validação inline antes do submit
  - [x] Erros Guided Recovery com actions clicáveis

- [x] Task 4: ProtectedRoute + ProjectsPage (AC: #3, #8)
  - [x] ProtectedRoute: redirect /login se não autenticado
  - [x] ProjectsPage: placeholder aguardando Epic 3

- [x] Task 5: App.tsx atualizado (AC: #3, #8)
  - [x] AuthProvider wrapping todas as rotas
  - [x] Rotas protegidas

## Dev Notes

- Token em memória: mais seguro que localStorage (não persiste XSS)
- Silent refresh: tenta POST /refresh ao montar — se falhar, vai para /login
- Interceptor de 401: evita que o usuário veja erro — tenta refresh transparente
- Redirect para /projects (placeholder) — Epic 3 implementa o conteúdo real

## Dev Agent Record
### Agent Model Used: Antigravity (Google Deepmind)
### File List
- `src/contexts/AuthContext.tsx`
- `src/services/apiClient.ts`
- `src/pages/LoginPage.tsx`
- `src/pages/ProjectsPage.tsx`
- `src/components/ProtectedRoute.tsx`
- `src/App.tsx`
