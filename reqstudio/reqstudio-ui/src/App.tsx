import { lazy, Suspense } from 'react'
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { ThemeProvider } from '@/contexts/ThemeContext'
import { AuthProvider } from '@/contexts/AuthContext'
import { ProtectedRoute } from '@/components/ProtectedRoute'

// Lazy load para code-splitting automático
const Home        = lazy(() => import('@/pages/Home'))
const LoginPage   = lazy(() => import('@/pages/LoginPage'))
const ProjectsPage = lazy(() => import('@/pages/ProjectsPage'))

const PageLoader = () => (
  <div className="flex min-h-screen items-center justify-center bg-background">
    <div
      className="w-8 h-8 rounded-full border-2 animate-spin"
      style={{ borderColor: 'var(--rs-primary)', borderTopColor: 'transparent' }}
    />
  </div>
)

export default function App() {
  return (
    <ThemeProvider>
      <AuthProvider>
        <BrowserRouter>
          <Suspense fallback={<PageLoader />}>
            <Routes>
              {/* Públicas */}
              <Route path="/"        element={<Home />} />
              <Route path="/login"   element={<LoginPage />} />
              <Route path="/register" element={<LoginPage />} />

              {/* Protegidas — requer autenticação */}
              <Route element={<ProtectedRoute />}>
                <Route path="/projects" element={<ProjectsPage />} />
              </Route>

              {/* Fallback */}
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </Suspense>
        </BrowserRouter>
      </AuthProvider>
    </ThemeProvider>
  )
}
