import { useState } from 'react'
import { ThemeToggle } from '@/components/ThemeToggle'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { authApi, ReqStudioApiError, type UserData } from '@/services/apiClient'

type Mode = 'login' | 'register'

interface FormState {
  email: string
  password: string
}

interface FeedbackState {
  type: 'error' | 'success'
  message: string
  help?: string
}

export default function LoginPage() {
  const [mode, setMode] = useState<Mode>('login')
  const [form, setForm] = useState<FormState>({ email: '', password: '' })
  const [loading, setLoading] = useState(false)
  const [feedback, setFeedback] = useState<FeedbackState | null>(null)
  const [user, setUser] = useState<UserData | null>(null)
  const [token, setToken] = useState<string | null>(null)

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setForm(prev => ({ ...prev, [e.target.name]: e.target.value }))
    setFeedback(null)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setFeedback(null)

    try {
      if (mode === 'register') {
        await authApi.register(form)
        setFeedback({ type: 'success', message: 'Conta criada com sucesso! Faça login.' })
        setMode('login')
      } else {
        const res = await authApi.login(form)
        const accessToken = res.data.access_token
        setToken(accessToken)
        const me = await authApi.me(accessToken)
        setUser(me.data)
      }
    } catch (err) {
      if (err instanceof ReqStudioApiError) {
        setFeedback({ type: 'error', message: err.error.message, help: err.error.help })
      } else {
        setFeedback({ type: 'error', message: 'Erro inesperado. Tente novamente.' })
      }
    } finally {
      setLoading(false)
    }
  }

  // ── Autenticado ──────────────────────────────────────────────────────────────
  if (user && token) {
    return (
      <div className="min-h-screen bg-background flex flex-col">
        <header className="border-b border-border px-[var(--space-4)] py-[var(--space-3)] flex items-center justify-between">
          <span className="text-h3 font-semibold" style={{ color: 'var(--rs-primary)' }}>ReqStudio</span>
          <ThemeToggle />
        </header>
        <main className="flex-1 flex items-center justify-center p-[var(--space-4)]">
          <div className="w-full max-w-md bg-card border border-border rounded-[var(--radius-lg)] p-[var(--space-6)] shadow-md space-y-[var(--space-4)]">
            <div className="flex items-center gap-[var(--space-2)]">
              <div className="w-10 h-10 rounded-full flex items-center justify-center text-white font-semibold"
                style={{ backgroundColor: 'var(--rs-success)' }}>
                ✓
              </div>
              <div>
                <p className="text-h3 font-semibold">Bem-vindo!</p>
                <p className="text-body-sm text-muted-foreground">Login realizado com sucesso</p>
              </div>
            </div>

            <div className="bg-muted rounded-[var(--radius-md)] p-[var(--space-3)] space-y-[var(--space-2)]">
              <p className="text-caption text-muted-foreground uppercase tracking-wide">Dados do usuário</p>
              <p className="text-body-sm"><span className="font-medium">E-mail:</span> {user.email}</p>
              <p className="text-body-sm"><span className="font-medium">ID:</span> <code className="text-mono">{user.id}</code></p>
              <p className="text-body-sm"><span className="font-medium">Tenant:</span> <code className="text-mono">{user.tenant_id}</code></p>
            </div>

            <div className="space-y-[var(--space-2)]">
              <p className="text-caption text-muted-foreground uppercase tracking-wide">Access Token (JWT)</p>
              <div className="bg-muted rounded-[var(--radius-md)] p-[var(--space-2)] overflow-auto">
                <code className="text-mono break-all" style={{ fontSize: '11px' }}>{token}</code>
              </div>
            </div>

            <Button
              variant="outline"
              className="w-full"
              onClick={() => { setUser(null); setToken(null); setForm({ email: '', password: '' }) }}
            >
              Sair
            </Button>
          </div>
        </main>
      </div>
    )
  }

  // ── Form ─────────────────────────────────────────────────────────────────────
  return (
    <div className="min-h-screen bg-background flex flex-col">
      <header className="border-b border-border px-[var(--space-4)] py-[var(--space-3)] flex items-center justify-between">
        <span className="text-h3 font-semibold" style={{ color: 'var(--rs-primary)' }}>ReqStudio</span>
        <ThemeToggle />
      </header>

      <main className="flex-1 flex items-center justify-center p-[var(--space-4)]">
        <div className="w-full max-w-sm space-y-[var(--space-5)]">

          {/* Header do card */}
          <div className="text-center space-y-[var(--space-2)]">
            <h1 className="text-h1">{mode === 'login' ? 'Entrar na conta' : 'Criar conta'}</h1>
            <p className="text-body-sm text-muted-foreground">
              {mode === 'login'
                ? 'Acesse o ReqStudio com seu e-mail e senha'
                : 'Crie sua conta gratuitamente'}
            </p>
          </div>

          {/* Card do formulário */}
          <div className="bg-card border border-border rounded-[var(--radius-lg)] p-[var(--space-5)] shadow-sm">
            <form onSubmit={handleSubmit} className="space-y-[var(--space-4)]">

              {/* Feedback */}
              {feedback && (
                <div
                  className="rounded-[var(--radius-md)] p-[var(--space-3)] text-body-sm"
                  style={{
                    backgroundColor: feedback.type === 'error' ? 'var(--rs-primary-light)' : 'rgba(var(--rs-success), 0.1)',
                    borderLeft: `3px solid ${feedback.type === 'error' ? 'var(--rs-error)' : 'var(--rs-success)'}`,
                    color: feedback.type === 'error' ? 'var(--rs-error)' : 'var(--rs-success)',
                  }}
                >
                  <p className="font-medium">{feedback.message}</p>
                  {feedback.help && <p className="mt-1 text-muted-foreground" style={{ color: 'inherit', opacity: 0.8 }}>{feedback.help}</p>}
                </div>
              )}

              <div className="space-y-[var(--space-2)]">
                <Label htmlFor="email">E-mail</Label>
                <Input
                  id="email"
                  name="email"
                  type="email"
                  placeholder="ana@empresa.com"
                  value={form.email}
                  onChange={handleChange}
                  required
                  autoComplete="email"
                />
              </div>

              <div className="space-y-[var(--space-2)]">
                <Label htmlFor="password">Senha</Label>
                <Input
                  id="password"
                  name="password"
                  type="password"
                  placeholder={mode === 'register' ? 'Mínimo 8 caracteres' : '••••••••'}
                  value={form.password}
                  onChange={handleChange}
                  required
                  autoComplete={mode === 'login' ? 'current-password' : 'new-password'}
                />
              </div>

              <Button
                type="submit"
                className="w-full"
                disabled={loading}
                id={mode === 'login' ? 'btn-login' : 'btn-register'}
              >
                {loading ? 'Aguarde...' : mode === 'login' ? 'Entrar' : 'Criar conta'}
              </Button>
            </form>
          </div>

          {/* Toggle de modo */}
          <p className="text-center text-body-sm text-muted-foreground">
            {mode === 'login' ? 'Não tem conta?' : 'Já tem conta?'}{' '}
            <button
              type="button"
              onClick={() => { setMode(mode === 'login' ? 'register' : 'login'); setFeedback(null) }}
              className="font-medium underline underline-offset-2"
              style={{ color: 'var(--rs-primary)' }}
            >
              {mode === 'login' ? 'Criar conta' : 'Entrar'}
            </button>
          </p>
        </div>
      </main>
    </div>
  )
}
