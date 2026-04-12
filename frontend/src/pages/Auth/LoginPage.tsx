import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Input } from '../../components/ui/Input'
import { Button } from '../../components/ui/Button'
import { useAuthStore } from '../../stores/auth.store'
import { authApi } from '../../api/auth.api'

const ease = [0.16, 1, 0.3, 1] as const

export function LoginPage() {
  const navigate = useNavigate()
  const { setAuth } = useAuthStore()

  const [login, setLogin]       = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading]   = useState(false)
  const [error, setError]       = useState('')

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const { token, user } = await authApi.login({ login, password })
      setAuth(token, user)
      navigate('/dashboard')
    } catch {
      setError('Неверные данные. Проверьте логин и пароль.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-bg flex items-center justify-center px-4 relative overflow-hidden">
      <div
        className="absolute pointer-events-none"
        style={{
          width: '60vw', height: '40vw',
          top: '10%', left: '20%',
          background: 'radial-gradient(ellipse at center, rgba(157,140,255,0.08) 0%, transparent 65%)',
          filter: 'blur(40px)',
        }}
        aria-hidden
      />

      <div className="relative w-full max-w-sm">
        <motion.div
          initial={{ opacity: 0, y: -16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, ease }}
          className="text-center mb-8"
        >
          <div className="inline-flex items-center justify-center mb-3">
            <AuthLogoMark />
          </div>
          <p className="font-display text-xl font-light text-text tracking-[0.16em] uppercase">SkyDragon</p>
          <p className="font-mono text-[11px] text-text-faint mt-1 tracking-widest uppercase">VPN</p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 24, scale: 0.97 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          transition={{ duration: 0.5, delay: 0.08, ease }}
          className="rounded-[28px]"
          style={{
            background: 'rgba(13,12,31,0.85)',
            border: '1px solid rgba(157,140,255,0.12)',
            backdropFilter: 'blur(20px)',
          }}
        >
          <div className="p-7">
            <h2 className="font-display text-2xl font-light text-text mb-1 text-balance">С возвращением</h2>
            <p className="font-mono text-[13px] text-text-dim mb-7 leading-relaxed">
              Введите логин и пароль
            </p>
            <form onSubmit={handleSubmit} className="space-y-4">
              <Input
                label="Логин"
                type="text"
                placeholder="ivan_ivanov"
                value={login}
                onChange={(e) => setLogin(e.target.value)}
                required
                autoFocus
              />
              <Input
                label="Пароль"
                type="password"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                error={error}
              />
              <Button type="submit" size="lg" className="w-full" loading={loading}>
                Войти
              </Button>
            </form>
          </div>
        </motion.div>

        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.4, duration: 0.4 }}
          className="text-center font-mono text-[13px] text-text-dim mt-6"
        >
          Нет аккаунта?{' '}
          <Link to="/register" className="text-jade hover:text-[#c4b5fd] transition-colors duration-200">
            Зарегистрироваться
          </Link>
        </motion.p>
      </div>
    </div>
  )
}

function AuthLogoMark() {
  return (
    <svg width="36" height="36" viewBox="0 0 36 36" fill="none" aria-hidden>
      <circle cx="18" cy="18" r="17" stroke="rgba(157,140,255,0.18)" strokeWidth="1" />
      <path
        d="M18 6l10 4v9c0 6.5-3.5 10.2-10 13.2C11.5 29.2 8 25.5 8 19V10L18 6z"
        fill="rgba(157,140,255,0.1)"
        stroke="rgba(157,140,255,0.75)"
        strokeWidth="1.2"
      />
      <path d="M13 18.5l3.5 3.5 7-8" stroke="rgba(157,140,255,0.95)" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}
