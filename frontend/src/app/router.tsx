import { createBrowserRouter, Navigate, useParams } from 'react-router-dom'
import { useEffect } from 'react'
import { AppShell } from '../components/layout/AppShell'
import { useAuthStore } from '../stores/auth.store'
import { WelcomePage } from '../pages/Welcome/WelcomePage'
import { LoginPage } from '../pages/Auth/LoginPage'
import { RegisterPage } from '../pages/Auth/RegisterPage'
import { DashboardPage } from '../pages/Dashboard/DashboardPage'

function RequireAuth({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuthStore()
  if (!isAuthenticated) return <Navigate to="/login" replace />
  return <>{children}</>
}

function RedirectIfAuth({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuthStore()
  if (isAuthenticated) return <Navigate to="/dashboard" replace />
  return <>{children}</>
}

function ReferralRedirect() {
  const { code } = useParams<{ code: string }>()
  useEffect(() => {
    if (code) localStorage.setItem('sdvpn_ref', code)
  }, [code])
  return <Navigate to={`/register?ref=${code ?? ''}`} replace />
}

export const router = createBrowserRouter([
  { path: '/', element: <WelcomePage /> },
  { path: '/login', element: <RedirectIfAuth><LoginPage /></RedirectIfAuth> },
  { path: '/register', element: <RedirectIfAuth><RegisterPage /></RedirectIfAuth> },
  { path: '/ref/:code', element: <ReferralRedirect /> },
  {
    element: (
      <RequireAuth>
        <AppShell />
      </RequireAuth>
    ),
    children: [
      { path: '/dashboard', element: <DashboardPage /> },
      // All sub-sections live as modals inside the dashboard
      { path: '*', element: <Navigate to="/dashboard" replace /> },
    ],
  },
])
