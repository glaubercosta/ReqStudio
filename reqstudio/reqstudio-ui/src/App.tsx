import { lazy, Suspense } from 'react'
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ThemeProvider } from '@/contexts/ThemeContext'
import { AuthProvider } from '@/contexts/AuthContext'
import { ProtectedRoute } from '@/components/ProtectedRoute'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: true,
    },
  },
})

// Lazy load para code-splitting automático
const Home              = lazy(() => import('@/pages/Home'))
const LoginPage         = lazy(() => import('@/pages/LoginPage'))
const ProjectsPage      = lazy(() => import('@/pages/ProjectsPage'))
const ProjectDetailPage = lazy(() => import('@/pages/ProjectDetailPage'))
const SessionPage       = lazy(() => import('@/pages/SessionPage'))

const PageLoader = () => (
  <div className="flex min-h-screen flex-col items-center justify-center gap-3 bg-background" aria-label="Carregando">
    <div
      className="w-8 h-8 rounded-full border-2 animate-spin"
      style={{ borderColor: 'var(--rs-primary)', borderTopColor: 'transparent' }}
    />
    <span className="text-body-sm text-muted-foreground">Carregando...</span>
  </div>
)

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <AuthProvider>
          <BrowserRouter>
            <Suspense fallback={<PageLoader />}>
              <Routes>
                {/* Públicas */}
                <Route path="/"         element={<Home />} />
                <Route path="/login"    element={<LoginPage />} />
                <Route path="/register" element={<LoginPage />} />

                {/* Protegidas — requer autenticação */}
                <Route element={<ProtectedRoute />}>
                  <Route path="/projects"     element={<ProjectsPage />} />
                  <Route path="/projects/new" element={<ProjectsPage />} />
                  <Route path="/projects/:id" element={<ProjectDetailPage />} />
                  <Route path="/sessions/:id" element={<SessionPage />} />
                </Route>

                {/* Fallback */}
                <Route path="*" element={<Navigate to="/" replace />} />
              </Routes>
            </Suspense>
          </BrowserRouter>
        </AuthProvider>
      </ThemeProvider>
    </QueryClientProvider>
  )
}
