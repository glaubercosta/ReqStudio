# ReqStudio — Frontend Prototype Prompt

Build a responsive web app prototype for **ReqStudio**, an AI-powered requirements engineering platform. The app has a conversational interface where domain specialists (non-technical users) chat with an AI assistant that progressively builds a structured requirements document.

## Tech Stack

- React + TypeScript + Vite
- Tailwind CSS
- shadcn/ui components (Radix UI primitives)
- Google Fonts: Inter (UI) + JetBrains Mono (code/technical)

## Design Tokens

### Colors

```css
--primary: hsl(234, 89%, 56%);          /* Buttons, links, active tabs */
--primary-hover: hsl(234, 89%, 48%);    /* Hover states */
--primary-light: hsl(234, 89%, 96%);    /* Subtle backgrounds */
--user-message: hsl(234, 70%, 65%);     /* User chat bubbles (NOT buttons) */
--accent: hsl(38, 92%, 50%);            /* Progress, active states */
--accent-light: hsl(38, 92%, 95%);      /* Coverage bar background */
--success: hsl(152, 69%, 41%);          /* Completed sections */
--warning: hsl(38, 92%, 45%);           /* Disagreement panels */
--error: hsl(0, 72%, 58%);             /* Errors, destructive actions */
--info: hsl(234, 60%, 65%);            /* Citation badges */
--bg: hsl(220, 14%, 98%);             /* Page background */
--surface: hsl(0, 0%, 100%);          /* Cards, panels */
--border: hsl(220, 13%, 91%);         /* Borders */
--text: hsl(224, 71%, 13%);           /* Primary text */
--text-secondary: hsl(220, 9%, 46%);  /* Secondary text */
--text-muted: hsl(220, 9%, 63%);      /* Muted text */
```

CRITICAL: User chat messages use `--user-message` (softer indigo). Buttons use `--primary` (strong indigo). Never use the same color for clickable actions and passive content.

### Typography

- **UI Font:** Inter — all interface text
- **Mono Font:** JetBrains Mono — code snippets, technical identifiers
- **Base size:** 16px
- **Chat messages:** 14px, line-height 1.6
- **Small labels:** 11px, font-weight 600

### Spacing & Radius

- Base unit: 4px
- Border radius: sm=6px, md=8px, lg=12px
- Shadows: sm (1px), md (4px), lg (10px)

## Screens to Build

### Screen 1: Project Dashboard

The landing page after login. Shows all user projects as cards.

**Layout:**
- Header: "ReqStudio" logo (text, font-weight 700, primary color) + user avatar (circle)
- Title: "Meus Projetos" + subtitle showing count ("3 ativos · 1 concluído")
- Grid of project cards (3 columns desktop, 1 column mobile)
- "+ Novo Projeto" button (primary, full-width on mobile)

**Project Card:**
- Project name (16px, font-weight 600)
- Client/description (13px, muted)
- Progress bar (6px height, rounded, color by status)
- Meta row: "65% cobertura · 5 seções" left, status dot + label right
- Hover: border changes to primary, slight elevation, translateY(-2px)

**Status colors for progress bars:**
- In progress: accent (amber)
- New/contextualizing: primary (indigo)
- Completed: success (green)
- Completed cards: opacity 0.6

**Mock data — 4 projects:**
1. "Rastreamento Last-Mile" — Logística Express Ltda. — 65% — "Fase 2 — Guiada"
2. "Portal do Paciente" — ClínicaSaúde S.A. — 30% — "Contextualização"
3. "Gestão de Frota" — TransportesBR — 10% — "Novo"
4. "Sistema de Ponto" — TechCorp Brasil — 100% — "Concluído" (opacity 0.6)

---

### Screen 2: Elicitation Session (Main Screen)

The core screen. A chat interface where the user talks to the AI while a requirements document is built progressively.

**Desktop Layout (lg: and above):**
- Fixed header: logo + "Salvo há 3s" (green dot + text) + project name
- Below header: CoverageBar (amber background strip)
- Split view: chat panel (left, 40%) | artifact panel (right, 60%)
- Fixed proportion, no resizable — just a 1px border between panels

**Mobile Layout (below lg:):**
- Fixed header: logo + save indicator
- CoverageBar below header
- Tab bar: "💬 Conversa" | "📄 Artefato" (with amber notification dot on Artefato when updated)
- Only one panel visible at a time based on active tab

**CoverageBar component:**
- Amber-tinted strip background
- Label "Cobertura 65%" (11px, font-weight 500, amber)
- Track (4px height, light amber) with fill (amber, 65% width)

**Chat Panel:**
- ScrollArea with messages
- Messages stack vertically with 12px gap

**AI Message (msg-ai):**
- Aligned left, max-width 85%
- White background, 1px border, rounded (12px 12px 12px 4px)
- "ReqStudio" label above (11px, font-weight 600, primary color)
- Message text: 14px, line-height 1.6
- Contains CitationBadges: small inline pill (indigo info, white text, 10px, "📎 SLA_v2.pdf")

**User Message (msg-user):**
- Aligned right, max-width 85%
- Background: `--user-message` (NOT --primary)
- White text, rounded (12px 12px 4px 12px)

**Input Area:**
- Fixed at bottom of chat panel
- White background, top border
- Textarea (auto-resize, placeholder: "Conte mais sobre o problema...")
- Row below: 📎 button (ghost) left, "Enviar" button (primary, solid) right

**Artifact Panel (desktop) / Artifact Tab (mobile):**
- Title: "📄 Requisitos — Rastreamento Last-Mile" (18px, primary-light bottom border)
- List of ArtifactSection cards stacked vertically

**ArtifactSection card:**
- Padding 12px, rounded md, left border 3px
- Complete state: green left border, light green bg, "✓ Completo" badge (green)
- Active state: amber left border, amber-light bg, "◐ 65%" badge (amber), "Construindo..."
- Pending state: gray left border, gray bg, "○ Pendente" badge (muted), opacity reduced

**Mock data — 5 sections:**
1. "Contexto do Problema" — Complete — "3 fontes"
2. "Visibilidade e Rastreamento" — Active 65% — "Construindo..."
3. "SLA e Compromissos" — Pending
4. "Integrações" — Pending
5. "Requisitos Não-Funcionais" — Pending

**Mock conversation (pre-filled):**
1. AI: "Li os documentos que você trouxe. Entendi que se trata de um sistema de rastreamento de entregas last-mile com desafios de visibilidade em tempo real. [📎 SLA_v2.pdf] Me conta: qual a maior dor que seu time enfrenta hoje com esse processo?"
2. User: "O maior problema é que quando o entregador sai do centro de distribuição, perdemos visibilidade. O cliente liga perguntando e ninguém sabe dizer onde está."
3. AI: "Entendi — visibilidade post-despacho é o gap. Notei que no SLA_v2 [📎 p.12] vocês prometem 'atualização a cada 30 min'. Esse compromisso poderia mudar pra tempo real, ou o SLA é contratual?"
4. User: "Sim, é contratual. Mas queremos oferecer tempo real como diferencial."
5. AI: "Ótimo. Vou documentar como requisito aspiracional com nota sobre implicação contratual."

---

### Screen 3: Welcome Back (Contextual Welcome)

Shown when user returns to a project they previously worked on.

**Centered layout, single column:**
- 👋 emoji (48px)
- "Bem-vinda de volta, Ana!" (20px, bold)
- "Rastreamento Last-Mile · Última sessão há 2 dias" (14px, secondary)
- Progress summary card (primary-light bg, rounded):
  - "Onde paramos:" label (12px, bold, primary)
  - Checklist items: ✅ done / ⏳ next / ○ pending
- "Próximo passo sugerido" card (gray bg):
  - Suggestion text (13px, secondary)
- "Continuar sessão" button (primary, full-width, 14px padding)

---

### Screen 4: Disagreement Pattern

A special UI pattern inside the chat when the AI challenges user input with evidence.

**Inside the chat, after a user message and AI response, show:**

**DisagreementPanel component:**
- Card with amber border, rounded lg, 16px padding
- Header row: ⚠️ icon + "Decisão de Domínio" (13px, bold, amber)
- Body text: explanation of disagreement (13px, secondary)
- Reference quote: italic, gray bg, rounded sm, 8px padding
- Action buttons row: "Manter 48h" (primary solid) + "Aceitar 24h" (outline)
- Footer text: "Se mantiver, será documentado como Ponto de Discussão para validar com o time." (11px, muted)

---

## Component Library (shadcn/ui)

Use these shadcn/ui components:
- `ScrollArea` — chat scroll
- `Tabs` — mobile chat/artifact toggle
- `Card` — project cards, artifact sections
- `Badge` — coverage, citation, status
- `Progress` — coverage bar
- `Textarea` — chat input (auto-resize)
- `Button` — primary/secondary/ghost/destructive hierarchy
- `Dialog` — export confirmation
- `Avatar` — AI identity, user avatar
- `Tooltip` — micro-helpers
- `DropdownMenu` — project actions
- `Skeleton` — loading states

## Button Hierarchy

| Level | Style | Use |
|-------|-------|-----|
| Primary | Solid indigo | Main action per area (max 1 visible) |
| Secondary | Outline | Alternative action |
| Tertiary | Ghost/link | Subtle action |
| Destructive | Solid coral | Irreversible actions (with confirmation) |

## Key UX Rules

1. **Anti-modal rule:** Errors and warnings NEVER use modals. Always inline with auto-recovery.
2. **Single textarea:** Never multi-field forms. Always expandable textarea.
3. **Submit:** Enter key on desktop, explicit button on mobile.
4. **Placeholder:** Contextual to conversation state, never generic.
5. **Loading AI:** Typing indicator (3 animated dots) + "Refletindo..."
6. **Page loading:** Skeleton with pulse animation matching real layout.
7. **Save indicator:** Green dot + "Salvo há Xs", appears 3s after save.
8. **Empty states:** Welcoming illustration + clear CTA, never blank screens.

## Responsive Behavior

- **Mobile-first** design approach
- Mobile (< 768px): single column, tabbed chat/artifact
- Tablet (768-1023px): optional soft split view
- Desktop (1024px+): fixed split view 40/60
- Touch targets: minimum 44x44px on mobile
- Breakpoints follow Tailwind: sm(640) md(768) lg(1024) xl(1280)

## Accessibility

- WCAG 2.1 AA compliance
- Contrast: 4.5:1 text, 3:1 interactive UI
- Full keyboard navigation (Tab, Enter, Escape)
- Focus ring: 2px indigo
- Skip links for main content
- Colors never sole indicator — always icon + text
- ARIA labels on custom components
- `prefers-reduced-motion` support

## Navigation Structure

Use React Router with these routes:
- `/` — Dashboard (project list)
- `/project/:id` — Elicitation session
- `/project/:id/welcome` — Welcome back screen

All screens should feel polished, professional, and warm — not clinical. The app should communicate "I'm a serious tool that treats you like a person."
