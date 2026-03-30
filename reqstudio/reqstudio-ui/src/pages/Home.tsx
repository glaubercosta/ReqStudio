import { ThemeToggle } from '@/components/ThemeToggle'
import { Button } from '@/components/ui/button'

export default function Home() {
  return (
    <div className="min-h-screen bg-background text-foreground">
      {/* Header */}
      <header className="border-b border-border bg-card px-[var(--space-4)] py-[var(--space-3)] flex items-center justify-between">
        <div className="flex items-center gap-[var(--space-2)]">
          <span className="text-h3 font-semibold" style={{ color: 'var(--rs-primary)' }}>
            ReqStudio
          </span>
          <span className="text-caption text-muted-foreground">v0.1.0</span>
        </div>
        <ThemeToggle />
      </header>

      {/* Hero */}
      <main className="flex flex-col items-center justify-center px-[var(--space-4)] py-[var(--space-8)] gap-[var(--space-5)]">
        <div className="text-center max-w-2xl">
          <h1 className="text-display mb-[var(--space-3)]">
            Elicitação de Requisitos<br />com Inteligência Artificial
          </h1>
          <p className="text-body text-muted-foreground max-w-lg mx-auto">
            Traduza seu conhecimento de domínio em artefatos estruturados através de uma
            conversa guiada com IA.
          </p>
        </div>

        <div className="flex gap-[var(--space-3)]">
          <Button>Novo Projeto</Button>
          <Button variant="outline">Ver Documetação</Button>
        </div>

        {/* Design Tokens Showcase */}
        <section className="w-full max-w-3xl mt-[var(--space-6)]">
          <h2 className="text-h2 mb-[var(--space-4)]">Design System — Tokens</h2>

          {/* Colors */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-[var(--space-3)] mb-[var(--space-5)]">
            {[
              { label: 'Primary', bg: 'var(--rs-primary)', text: '#fff' },
              { label: 'Primary Hover', bg: 'var(--rs-primary-hover)', text: '#fff' },
              { label: 'Primary Light', bg: 'var(--rs-primary-light)', text: 'var(--rs-text-primary)' },
              { label: 'User Message', bg: 'var(--rs-user-message)', text: '#fff' },
              { label: 'Amber', bg: 'var(--rs-amber)', text: '#fff' },
              { label: 'Amber Light', bg: 'var(--rs-amber-light)', text: 'var(--rs-text-primary)' },
              { label: 'Success', bg: 'var(--rs-success)', text: '#fff' },
              { label: 'Error', bg: 'var(--rs-error)', text: '#fff' },
            ].map(swatch => (
              <div
                key={swatch.label}
                className="rounded-[var(--radius-md)] p-[var(--space-3)] shadow-sm"
                style={{ backgroundColor: swatch.bg, color: swatch.text }}
              >
                <span className="text-caption font-medium">{swatch.label}</span>
              </div>
            ))}
          </div>

          {/* Type Scale */}
          <div className="bg-card border border-border rounded-[var(--radius-lg)] p-[var(--space-4)] space-y-[var(--space-3)] shadow-sm">
            <p className="text-caption text-muted-foreground uppercase tracking-wide">Escala Tipográfica</p>
            <p className="text-display">Display — 30px / Bold</p>
            <h1>H1 — 24px / Semibold</h1>
            <h2>H2 — 20px / Semibold</h2>
            <h3>H3 — 16px / Semibold</h3>
            <p className="text-body">Body — 15px / Regular — texto corrido e mensagens de chat</p>
            <p className="text-body-sm text-muted-foreground">Body SM — 13px / Regular — timestamps e labels</p>
            <p className="text-caption">Caption — 12px / Medium — badges e indicadores</p>
            <code className="text-mono">Mono — 14px / JetBrains Mono — visão técnica</code>
          </div>
        </section>
      </main>
    </div>
  )
}
