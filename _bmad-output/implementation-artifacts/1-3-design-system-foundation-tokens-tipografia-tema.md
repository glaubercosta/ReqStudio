# Story 1.3: Design System Foundation — Tokens, Tipografia e Tema

Status: in-progress

## Story

As a desenvolvedor,
I want os design tokens, tipografia e sistema de tema implementados,
So that todos os componentes usem uma base visual consistente conforme a UX Spec.

## Acceptance Criteria

1. **Given** o frontend inicializado **When** inspeciono `index.css` **Then** CSS variables definidas: paleta indigo (primary, hover, light, user-message), âmbar (accent, light), semânticas (success, warning, error, info), neutros (background, surface, border, text-primary/secondary/muted)
2. **Given** o frontend **When** carrega no browser **Then** Inter via Google Fonts + JetBrains Mono estão ativos
3. **Given** o CSS **When** inspeciono as variables **Then** type scale definido (display 30px a caption 12px) com peso e line-height
4. **Given** o CSS **When** inspeciono as variables **Then** espaçamento base 4px (space-1 a space-8), border-radius (sm a full), sombras (sm a lg)
5. **Given** o usuário toggle dark mode **When** a classe `.dark` é aplicada ao body **Then** variáveis de cor ajustam para modo escuro
6. **Given** o sistema de cores **When** verifico contraste **Then** texto primário sobre background atinge ≥4.5:1 (NFR17)

## Tasks / Subtasks

- [x] Task 1: Tokens de cor (AC: #1)
  - [x] 1.1 Definir paleta primária indigo com CSS variables
  - [x] 1.2 Definir paleta de acentos (âmbar)
  - [x] 1.3 Definir paleta semântica (success, warning, error, info)
  - [x] 1.4 Definir paleta de neutros (warm grays)
  - [x] 1.5 Definir tokens dark mode

- [x] Task 2: Tipografia (AC: #2, #3)
  - [x] 2.1 Importar Inter + JetBrains Mono via Google Fonts
  - [x] 2.2 Definir type scale como CSS variables

- [x] Task 3: Espaçamento, radius e sombras (AC: #4)
  - [x] 3.1 Definir tokens de espaçamento (space-1 a space-8)
  - [x] 3.2 Definir tokens de border-radius
  - [x] 3.3 Definir tokens de sombra

- [x] Task 4: Dark mode toggle (AC: #5)
  - [x] 4.1 Criar ThemeProvider context
  - [x] 4.2 Criar ThemeToggle component
  - [x] 4.3 Integrar ao App

## Dev Notes

### Referência: UX-Design-Specification.md § Visual Design Foundation

Todos os valores de cor, tipografia e espaçamento vêm diretamente desta seção.

### Anti-Patterns
- ❌ NÃO usar cores hardcoded nos componentes — sempre via CSS variable
- ❌ NÃO sobrescrever tokens gerados pelo shadcn sem intenção explícita
- ❌ NÃO usar px diretamente para espaçamento — usar os tokens space-*

## Dev Agent Record

### Agent Model Used

Antigravity (Google Deepmind)

### Completion Notes List

- ✅ Todos os tokens da UX Spec implementados em index.css
- ✅ Inter + JetBrains Mono via Google Fonts no index.html
- ✅ ThemeProvider + ThemeToggle implementados
- ✅ Dark mode funcional via classe .dark no html element
- ✅ Página Home atualizada para demonstrar os tokens

### File List

- `reqstudio/reqstudio-ui/index.html`
- `reqstudio/reqstudio-ui/src/index.css`
- `reqstudio/reqstudio-ui/src/contexts/ThemeContext.tsx`
- `reqstudio/reqstudio-ui/src/components/ThemeToggle.tsx`
- `reqstudio/reqstudio-ui/src/App.tsx`
- `reqstudio/reqstudio-ui/src/pages/Home.tsx`
