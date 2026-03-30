/**
 * ProjectsPage — placeholder para Epic 3.
 *
 * Exibe dashboard básico com dados do usuário autenticado.
 * O conteúdo real (CRUD de projetos) é implementado na Story 3.1.
 */

import { useNavigate } from 'react-router-dom'
import { ThemeToggle } from '@/components/ThemeToggle'
import { Button } from '@/components/ui/button'
import { useAuth } from '@/contexts/AuthContext'

export default function ProjectsPage() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = async () => {
    await logout()
    navigate('/login', { replace: true })
  }

  return (
    <div className="min-h-screen bg-background flex flex-col">
      {/* Header */}
      <header className="border-b border-border px-[var(--space-4)] py-[var(--space-3)] flex items-center justify-between">
        <div className="flex items-center gap-[var(--space-3)]">
          <span className="text-h3 font-semibold" style={{ color: 'var(--rs-primary)' }}>
            ReqStudio
          </span>
          <span
            className="text-caption px-[var(--space-2)] py-1 rounded-full font-medium"
            style={{ backgroundColor: 'var(--rs-primary-light)', color: 'var(--rs-primary)' }}
          >
            Beta
          </span>
        </div>
        <div className="flex items-center gap-[var(--space-3)]">
          <ThemeToggle />
          <Button variant="outline" size="sm" onClick={handleLogout}>
            Sair
          </Button>
        </div>
      </header>

      {/* Main */}
      <main className="flex-1 p-[var(--space-6)] max-w-5xl mx-auto w-full">
        {/* Boas-vindas */}
        <div className="mb-[var(--space-6)]">
          <h1 className="text-h1 mb-[var(--space-1)]">
            Olá, {user?.email.split('@')[0]} 👋
          </h1>
          <p className="text-body-sm text-muted-foreground">
            Bem-vindo ao ReqStudio. Seus projetos de requisitos estão aqui.
          </p>
        </div>

        {/* Placeholder card */}
        <div
          className="rounded-[var(--radius-lg)] border border-dashed border-border p-[var(--space-8)] flex flex-col items-center justify-center text-center gap-[var(--space-3)]"
          style={{ backgroundColor: 'var(--rs-surface)' }}
        >
          <div
            className="w-16 h-16 rounded-2xl flex items-center justify-center text-2xl"
            style={{ backgroundColor: 'var(--rs-primary-light)' }}
          >
            📋
          </div>
          <div>
            <p className="text-h3 font-semibold">Seus projetos aparecem aqui</p>
            <p className="text-body-sm text-muted-foreground mt-[var(--space-1)]">
              O Epic 3 implementa o CRUD completo de projetos.
            </p>
          </div>
          <Button disabled id="btn-new-project">
            + Novo Projeto
          </Button>
        </div>

        {/* Debug info — visível apenas em DEBUG */}
        {import.meta.env.DEV && (
          <details className="mt-[var(--space-6)]">
            <summary className="text-caption text-muted-foreground cursor-pointer">
              Dados do usuário (dev only)
            </summary>
            <div className="mt-[var(--space-2)] bg-muted rounded-[var(--radius-md)] p-[var(--space-3)]">
              <code className="text-mono text-body-sm">
                {JSON.stringify(user, null, 2)}
              </code>
            </div>
          </details>
        )}
      </main>
    </div>
  )
}
