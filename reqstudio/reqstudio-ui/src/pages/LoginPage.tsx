/**
 * LoginPage — tela de login e registro (Story 2.5).
 *
 * Modo login: email + senha
 * Modo registro: email + senha + confirmação de senha
 * Feedback: Guided Recovery inline com actions clicáveis
 */

import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { ThemeToggle } from '@/components/ThemeToggle'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { useAuth } from '@/contexts/AuthContext'
import { ReqStudioApiError } from '@/services/apiClient'

type Mode = 'login' | 'register'

interface FeedbackState {
  type: 'error' | 'success'
  message: string
  help?: string
  actions?: { label: string; route?: string }[]
}

interface ValidationErrors {
  email?: string
  password?: string
  confirmPassword?: string
}

function validate(
  mode: Mode,
  email: string,
  password: string,
  confirmPassword: string,
): ValidationErrors {
  const errors: ValidationErrors = {}
  if (!email.includes('@')) errors.email = 'E-mail inválido.'
  if (password.length < 8) errors.password = 'Mínimo 8 caracteres.'
  if (mode === 'register' && password !== confirmPassword) {
    errors.confirmPassword = 'As senhas não coincidem.'
  }
  return errors
}

export default function LoginPage() {
  const navigate = useNavigate()
  const { login, register } = useAuth()

  const [mode, setMode] = useState<Mode>('login')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [feedback, setFeedback] = useState<FeedbackState | null>(null)
  const [fieldErrors, setFieldErrors] = useState<ValidationErrors>({})

  const switchMode = (next: Mode) => {
    setMode(next)
    setFeedback(null)
    setFieldErrors({})
    setPassword('')
    setConfirmPassword('')
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setFeedback(null)

    // Validação inline
    const errors = validate(mode, email, password, confirmPassword)
    if (Object.keys(errors).length > 0) {
      setFieldErrors(errors)
      return
    }
    setFieldErrors({})
    setLoading(true)

    try {
      if (mode === 'register') {
        await register(email, password)
      } else {
        await login(email, password)
      }
      navigate('/projects', { replace: true })
    } catch (err) {
      if (err instanceof ReqStudioApiError) {
        setFeedback({
          type: 'error',
          message: err.error.message,
          help: err.error.help,
          actions: err.error.actions?.filter(a => a.route),
        })
      } else {
        setFeedback({ type: 'error', message: 'Erro inesperado. Tente novamente.' })
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-background flex flex-col">
      {/* Header */}
      <header className="border-b border-border px-[var(--space-4)] py-[var(--space-3)] flex items-center justify-between">
        <Link to="/" className="text-h3 font-semibold" style={{ color: 'var(--rs-primary)' }}>
          ReqStudio
        </Link>
        <ThemeToggle />
      </header>

      {/* Main */}
      <main className="flex-1 flex items-center justify-center p-[var(--space-4)]">
        <div className="w-full max-w-sm space-y-[var(--space-5)]">

          {/* Header do form */}
          <div className="text-center space-y-[var(--space-2)]">
            <h1 className="text-h1">
              {mode === 'login' ? 'Entrar na conta' : 'Criar conta'}
            </h1>
            <p className="text-body-sm text-muted-foreground">
              {mode === 'login'
                ? 'Acesse o ReqStudio com seu e-mail e senha'
                : 'Crie sua conta gratuitamente para começar'}
            </p>
          </div>

          {/* Card com formulário */}
          <div className="bg-card border border-border rounded-[var(--radius-lg)] p-[var(--space-5)] shadow-sm">
            <form onSubmit={handleSubmit} noValidate className="space-y-[var(--space-4)]">

              {/* Feedback de erro/sucesso */}
              {feedback && (
                <div
                  className="rounded-[var(--radius-md)] p-[var(--space-3)] text-body-sm space-y-[var(--space-1)]"
                  role="alert"
                  style={{
                    backgroundColor: feedback.type === 'error'
                      ? 'color-mix(in srgb, var(--rs-error) 10%, transparent)'
                      : 'color-mix(in srgb, var(--rs-success) 10%, transparent)',
                    borderLeft: `3px solid ${feedback.type === 'error' ? 'var(--rs-error)' : 'var(--rs-success)'}`,
                    color: feedback.type === 'error' ? 'var(--rs-error)' : 'var(--rs-success)',
                  }}
                >
                  <p className="font-medium">{feedback.message}</p>
                  {feedback.help && (
                    <p style={{ opacity: 0.85 }}>{feedback.help}</p>
                  )}
                  {feedback.actions && feedback.actions.length > 0 && (
                    <div className="flex gap-[var(--space-2)] mt-[var(--space-1)]">
                      {feedback.actions.map((action) => (
                        <Link
                          key={action.label}
                          to={action.route!}
                          className="text-caption font-medium underline underline-offset-2"
                        >
                          {action.label}
                        </Link>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {/* E-mail */}
              <div className="space-y-[var(--space-1)]">
                <Label htmlFor="email">E-mail</Label>
                <Input
                  id="email"
                  type="email"
                  placeholder="ana@empresa.com"
                  value={email}
                  onChange={e => { setEmail(e.target.value); setFieldErrors(p => ({ ...p, email: undefined })) }}
                  required
                  autoComplete="email"
                  aria-invalid={!!fieldErrors.email}
                />
                {fieldErrors.email && (
                  <p className="text-caption" style={{ color: 'var(--rs-error)' }}>
                    {fieldErrors.email}
                  </p>
                )}
              </div>

              {/* Senha */}
              <div className="space-y-[var(--space-1)]">
                <Label htmlFor="password">Senha</Label>
                <Input
                  id="password"
                  type="password"
                  placeholder={mode === 'register' ? 'Mínimo 8 caracteres' : '••••••••'}
                  value={password}
                  onChange={e => { setPassword(e.target.value); setFieldErrors(p => ({ ...p, password: undefined })) }}
                  required
                  autoComplete={mode === 'login' ? 'current-password' : 'new-password'}
                  aria-invalid={!!fieldErrors.password}
                />
                {fieldErrors.password && (
                  <p className="text-caption" style={{ color: 'var(--rs-error)' }}>
                    {fieldErrors.password}
                  </p>
                )}
              </div>

              {/* Confirmação de senha (só no registro) */}
              {mode === 'register' && (
                <div className="space-y-[var(--space-1)]">
                  <Label htmlFor="confirmPassword">Confirmar senha</Label>
                  <Input
                    id="confirmPassword"
                    type="password"
                    placeholder="Repita a senha"
                    value={confirmPassword}
                    onChange={e => { setConfirmPassword(e.target.value); setFieldErrors(p => ({ ...p, confirmPassword: undefined })) }}
                    required
                    autoComplete="new-password"
                    aria-invalid={!!fieldErrors.confirmPassword}
                  />
                  {fieldErrors.confirmPassword && (
                    <p className="text-caption" style={{ color: 'var(--rs-error)' }}>
                      {fieldErrors.confirmPassword}
                    </p>
                  )}
                </div>
              )}

              <Button
                type="submit"
                className="w-full"
                disabled={loading}
                id={mode === 'login' ? 'btn-login' : 'btn-register'}
              >
                {loading
                  ? (mode === 'login' ? 'Entrando...' : 'Criando conta...')
                  : (mode === 'login' ? 'Entrar' : 'Criar conta')}
              </Button>
            </form>
          </div>

          {/* Toggle de modo */}
          <p className="text-center text-body-sm text-muted-foreground">
            {mode === 'login' ? 'Não tem conta?' : 'Já tem conta?'}{' '}
            <button
              type="button"
              onClick={() => switchMode(mode === 'login' ? 'register' : 'login')}
              className="font-medium underline underline-offset-2"
              style={{ color: 'var(--rs-primary)' }}
              id="btn-switch-mode"
            >
              {mode === 'login' ? 'Criar conta' : 'Entrar'}
            </button>
          </p>
        </div>
      </main>
    </div>
  )
}
