# Story 1.2: Inicialização do Frontend React/Vite com shadcn/ui

Status: review

## Story

As a desenvolvedor,
I want um frontend React + TypeScript + Vite com shadcn/ui configurado,
So that eu tenha a fundação de UI para implementar as telas do ReqStudio.

## Acceptance Criteria

1. **Given** o repositório com backend funcional (Story 1.1) **When** eu acesso `http://localhost:{FRONTEND_PORT}` no browser **Then** uma página placeholder do ReqStudio é exibida
2. **Given** o frontend inicializado **When** eu inspeciono o código **Then** React 18+ com TypeScript strict, shadcn/ui inicializado, Tailwind CSS com CSS variables
3. **Given** o frontend **When** eu inspeciono a estrutura **Then** diretórios conforme arquitetura: `components/`, `pages/`, `hooks/`, `services/`, `contexts/`, `types/`, `lib/`
4. **Given** o frontend **When** eu verifico o roteamento **Then** React Router v6 com lazy loading configurado
5. **Given** o frontend **When** eu executo testes e lint **Then** Vitest + ESLint configurados e rodando sem erros
6. **Given** o docker-compose.yml **When** eu verifico os serviços **Then** serviço `frontend` adicionado

## Tasks / Subtasks

- [x] Task 1: Scaffold do projeto Vite (AC: #2)
  - [x] 1.1 Criar `reqstudio-ui/` via `npm create vite@latest` com template `react-ts`
  - [x] 1.2 Instalar dependências: Tailwind CSS v4, @tailwindcss/vite
  - [x] 1.3 Configurar `vite.config.ts` com plugin Tailwind + alias `@/`
  - [x] 1.4 Configurar `tsconfig.json` e `tsconfig.app.json` com paths `@/*`

- [x] Task 2: shadcn/ui + Estrutura (AC: #2, #3)
  - [x] 2.1 Inicializar shadcn/ui (`npx shadcn@latest init`)
  - [x] 2.2 Criar estrutura: `src/components/`, `src/pages/`, `src/hooks/`, `src/services/`, `src/contexts/`, `src/types/`, `src/lib/`
  - [x] 2.3 Adicionar componente Button como smoke test

- [x] Task 3: Roteamento (AC: #4)
  - [x] 3.1 Instalar react-router-dom v6
  - [x] 3.2 Configurar lazy loading com React.lazy + Suspense
  - [x] 3.3 Criar página placeholder Home

- [x] Task 4: Testes e Lint (AC: #5)
  - [x] 4.1 Configurar Vitest
  - [x] 4.2 Configurar ESLint
  - [x] 4.3 Criar teste smoke do App component

- [x] Task 5: Docker Compose Integration (AC: #6)
  - [x] 5.1 Criar Dockerfile para frontend
  - [x] 5.2 Adicionar serviço `frontend` ao docker-compose.yml

## Dev Notes

### Tecnologias e Versões

- **Vite** — latest via `npm create vite@latest`
- **React 18+** com TypeScript strict
- **Tailwind CSS v4** — via `@tailwindcss/vite` plugin (NÃO v3)
- **shadcn/ui** — via `npx shadcn@latest init`
- **React Router v6** — com lazy loading
- **Vitest** — test runner integrado ao Vite

### Estrutura de Diretórios

```
reqstudio-ui/
├── Dockerfile
├── package.json
├── vite.config.ts
├── tsconfig.json
├── tsconfig.app.json
├── components.json         # shadcn config
├── src/
│   ├── main.tsx
│   ├── App.tsx
│   ├── index.css
│   ├── components/
│   │   └── ui/             # shadcn components
│   ├── pages/
│   │   └── Home.tsx
│   ├── hooks/
│   ├── services/
│   ├── contexts/
│   ├── types/
│   └── lib/
│       └── utils.ts        # shadcn cn() helper
└── tests/
```

### Anti-Patterns

- ❌ NÃO usar Tailwind v3 — usar v4 com `@tailwindcss/vite`
- ❌ NÃO usar `tailwind.config.js` — v4 usa CSS-first config
- ❌ NÃO criar componentes UI do zero — usar shadcn/ui
- ❌ NÃO esquecer alias `@/` no tsconfig

### References

- [Source: architecture.md#Starter Template] — Vite + React + shadcn/ui
- [Source: epics.md#Story 1.2] — Acceptance Criteria
- [Source: ux-design-specification.md] — Design system será implementado na Story 1.3

## Dev Agent Record

### Agent Model Used

Antigravity (Google Deepmind)

### Completion Notes List

- ✅ Estrutura React Vite criada e configurada com TypeScript strict
- ✅ Tailwind v4 ativado no Vite via plugin `@tailwindcss/vite`
- ✅ Bibliotecas core e dependências instaladas (React Router, vite config adjustments)
- ✅ shadcn/ui configurado com preset Nova/Radix/Zinc e CSS variáveis ativadas.
- ✅ Componente Button adicionado corretamente no scaffold do shadcn
- ✅ Roteamento React Router v6 com React.lazy() implementado em `App.tsx`
- ✅ Vitest configurado em `vitest.config.ts` e testes smoke executados com jsdom
- ✅ Novo container frontend adicionado no docker-compose e servido por um Nginx builder container.
- ⚠️ Necessário executar `docker-compose up --build -d` para reconstruir ambiente contendo os novos containers backend e frontend juntos.

### File List

- `reqstudio/docker-compose.yml`
- `reqstudio/reqstudio-ui/package.json`
- `reqstudio/reqstudio-ui/tsconfig.json`
- `reqstudio/reqstudio-ui/tsconfig.app.json`
- `reqstudio/reqstudio-ui/vite.config.ts`
- `reqstudio/reqstudio-ui/vitest.config.ts`
- `reqstudio/reqstudio-ui/Dockerfile`
- `reqstudio/reqstudio-ui/src/App.tsx`
- `reqstudio/reqstudio-ui/src/tests/setup.ts`
- `reqstudio/reqstudio-ui/src/tests/App.test.tsx`
- `reqstudio/reqstudio-ui/src/pages/Home.tsx`
