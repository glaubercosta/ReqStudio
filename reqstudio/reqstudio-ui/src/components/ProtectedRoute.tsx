/**
 * ProtectedRoute — redireciona para /login se não autenticado.
 *
 * Durante o silent refresh (isLoading=true), exibe spinner
 * para evitar flash de redirect desnecessário.
 */

import { Navigate, Outlet } from 'react-router-dom'
import { useAuth } from '@/contexts/AuthContext'

export function ProtectedRoute() {
  const { isAuthenticated, isLoading } = useAuth()

  if (isLoading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div
          className="w-8 h-8 rounded-full border-2 border-t-transparent animate-spin"
          style={{ borderColor: 'var(--rs-primary)', borderTopColor: 'transparent' }}
        />
      </div>
    )
  }

  return isAuthenticated ? <Outlet /> : <Navigate to="/login" replace />
}
