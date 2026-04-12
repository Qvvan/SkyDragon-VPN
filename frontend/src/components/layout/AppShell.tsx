import { useState, useEffect } from 'react'
import { Outlet } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { useAuthStore } from '../../stores/auth.store'
import { authApi } from '../../api/auth.api'
import { Input } from '../ui/Input'
import { Button } from '../ui/Button'
import { Modal } from '../ui/Modal'

// ─── Profile Modal ─────────────────────────────────────────────────────────
function ProfileModal({ open, onClose }: { open: boolean; onClose: () => void }) {
  const { user, updateUser } = useAuthStore()

  const [firstName, setFirstName] = useState('')
  const [lastName, setLastName]   = useState('')
  const [saving, setSaving]       = useState(false)
  const [savedOk, setSavedOk]     = useState(false)
  const [error, setError]         = useState<string | null>(null)

  useEffect(() => {
    if (open && user) {
      setFirstName(user.firstName ?? '')
      setLastName(user.lastName ?? '')
      setSavedOk(false)
      setError(null)
    }
  }, [open, user])

  async function handleSave() {
    setSaving(true)
    setError(null)
    try {
      const updated = await authApi.updateProfile({ firstName, lastName })
      updateUser(updated)
      setSavedOk(true)
      setTimeout(() => setSavedOk(false), 2500)
    } catch {
      setError('Не удалось сохранить. Попробуйте снова.')
    } finally {
      setSaving(false)
    }
  }

  const displayName = user?.firstName
    ? `${user.firstName}${user.lastName ? ' ' + user.lastName : ''}`
    : '?'

  const avatarLetter = (user?.firstName || '?').charAt(0).toUpperCase()
  const telegramLinked = (user?.telegramUserId ?? null) !== null

  return (
    <Modal open={open} onClose={onClose} title="Профиль" size="md">
      <div className="p-6 space-y-5">

        {/* ── Avatar row ── */}
        <div className="flex items-center gap-4 pb-1">
          <div className="relative shrink-0">
            <div className="size-14 rounded-2xl bg-jade-dim flex items-center justify-center shadow-[0_0_0_1px_rgba(157,140,255,0.2)]">
              <ProfileSigilIcon />
            </div>
            <div className="absolute -bottom-1.5 -right-1.5 min-w-[20px] h-5 px-1.5 rounded-full bg-gradient-to-br from-[#a899ff] to-[#7c6bff] text-white text-[10px] font-mono leading-none flex items-center justify-center shadow-[0_0_8px_rgba(157,140,255,0.5)]">
              {avatarLetter}
            </div>
          </div>
          <div className="min-w-0">
            <p className="font-display text-base text-text truncate">{displayName}</p>
            <p className="font-mono text-xs text-text-dim mt-0.5">{user?.login ?? '—'}</p>
          </div>
        </div>

        {/* ── Name row ── */}
        <div className="grid grid-cols-2 gap-3">
          <Input
            label="Имя"
            value={firstName}
            onChange={e => setFirstName(e.target.value)}
            placeholder="Иван"
          />
          <Input
            label="Фамилия"
            value={lastName}
            onChange={e => setLastName(e.target.value)}
            placeholder="Иванов"
          />
        </div>

        {/* ── Telegram status ── */}
        <div className="rounded-2xl bg-surface-3 px-4 py-3 flex items-center justify-between gap-3" style={{ border: '1px solid rgba(157,140,255,0.07)' }}>
          <div className="flex items-center gap-3">
            <div className="size-9 rounded-xl bg-[rgba(0,136,204,0.1)] flex items-center justify-center shrink-0">
              <TelegramIcon />
            </div>
            <div>
              <p className="font-mono text-[10px] text-text-dim uppercase tracking-wider">Telegram</p>
              <div className="flex items-center gap-1.5 mt-0.5">
                {telegramLinked ? (
                  <>
                    <span className="size-1.5 rounded-full bg-jade inline-block shadow-[0_0_6px_rgba(157,140,255,0.6)]" />
                    <span className="font-mono text-sm text-jade">Привязан</span>
                  </>
                ) : (
                  <>
                    <span className="size-1.5 rounded-full bg-text-faint inline-block" />
                    <span className="font-mono text-sm text-text-dim">Не привязан</span>
                  </>
                )}
              </div>
            </div>
          </div>
          {!telegramLinked && (
            <a
              href="https://t.me/SkyDragonVPNBot"
              target="_blank"
              rel="noopener noreferrer"
              className="shrink-0"
            >
              <Button size="sm" variant="primary">
                <span className="flex items-center gap-1.5">
                  <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                    <path d="M13 10V3L4 14h7v7l9-11h-7z"/>
                  </svg>
                  Привязать
                </span>
              </Button>
            </a>
          )}
        </div>

        {/* ── Error ── */}
        <AnimatePresence>
          {error && (
            <motion.p
              initial={{ opacity: 0, y: -4 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              className="font-mono text-xs text-ember text-center"
            >
              {error}
            </motion.p>
          )}
        </AnimatePresence>

        {/* ── Save ── */}
        <Button variant="primary" className="w-full" loading={saving} onClick={handleSave}>
          <AnimatePresence mode="wait" initial={false}>
            {savedOk ? (
              <motion.span
                key="ok"
                initial={{ opacity: 0, scale: 0.85 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.85 }}
                transition={{ duration: 0.18 }}
                className="flex items-center gap-1.5 justify-center"
              >
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round">
                  <path d="M20 6L9 17l-5-5"/>
                </svg>
                Сохранено
              </motion.span>
            ) : (
              <motion.span
                key="save"
                initial={{ opacity: 0, scale: 0.85 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.85 }}
                transition={{ duration: 0.18 }}
              >
                Сохранить изменения
              </motion.span>
            )}
          </AnimatePresence>
        </Button>
      </div>
    </Modal>
  )
}

function TelegramIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" aria-hidden>
      <path
        d="M21.8 4.4L18.5 19.1c-.2 1-.9 1.3-1.8.8l-5-3.7-2.4 2.3c-.3.3-.5.5-1 .5l.4-5.1 9.5-8.6c.4-.4-.1-.5-.6-.2L5.6 13.1.9 11.6c-1-.3-1-.9.2-1.4L20.5 3c.9-.3 1.6.2 1.3 1.4z"
        fill="#0088cc"
      />
    </svg>
  )
}

// ─── App Shell ─────────────────────────────────────────────────────────────
export function AppShell() {
  const { user, clearAuth } = useAuthStore()
  const [profileOpen, setProfileOpen] = useState(false)
  const [scrolled, setScrolled] = useState(false)

  useEffect(() => {
    const el = document.querySelector('main')
    if (!el) return
    const handler = () => setScrolled(el.scrollTop > 8)
    el.addEventListener('scroll', handler, { passive: true })
    return () => el.removeEventListener('scroll', handler)
  }, [])

  const displayName = user?.firstName
    ? `${user.firstName}${user.lastName ? ' ' + user.lastName : ''}`
    : '—'

  return (
    <div className="min-h-screen bg-bg flex flex-col">
      {/* Header */}
      <header
        data-sticky
        className={[
          'sticky top-0 z-20 flex items-center justify-between px-4 md:px-8 h-14 shrink-0',
          'transition-[background,box-shadow,padding] duration-300',
          scrolled
            ? 'bg-[rgba(7,7,15,0.88)] backdrop-blur-xl shadow-[0_1px_0_rgba(157,140,255,0.07)]'
            : 'bg-transparent',
        ].join(' ')}
      >
        {/* Logo */}
        <div className="flex items-center gap-2.5">
          <LogoMark />
          <div className="flex items-baseline gap-1.5">
            <span className="font-display text-[15px] font-medium text-text tracking-[0.18em] uppercase">SkyDragon</span>
            <span className="font-mono text-[10px] text-text-faint tracking-widest">VPN</span>
          </div>
        </div>

        {/* Right controls */}
        <div className="flex items-center gap-1.5">
          {/* Profile chip */}
          <motion.button
            whileTap={{ scale: 0.96 }}
            transition={{ type: 'spring', stiffness: 500, damping: 35, mass: 0.5 }}
            onClick={() => setProfileOpen(true)}
            className={[
              'group flex items-center gap-2 rounded-2xl px-2.5 py-1.5 cursor-pointer',
              'bg-surface shadow-card',
              'hover:shadow-card-hover hover:bg-surface-2',
              'transition-[box-shadow,background-color] duration-200',
            ].join(' ')}
            style={{ willChange: 'transform' }}
            title="Открыть профиль"
          >
            <div className="size-5 rounded-full bg-jade-dim flex items-center justify-center shrink-0">
              <ProfileChipIcon />
            </div>
            <span className="hidden sm:inline font-mono text-xs text-text-dim group-hover:text-text transition-colors duration-150">
              {displayName}
            </span>
            <svg
              width="9" height="9" viewBox="0 0 24 24" fill="none"
              stroke="currentColor" strokeWidth="2" strokeLinecap="round"
              className="hidden sm:block text-text-faint group-hover:text-text-dim transition-colors duration-150"
            >
              <path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7"/>
              <path d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z"/>
            </svg>
          </motion.button>

          {/* Sign out */}
          <motion.button
            whileTap={{ scale: 0.96 }}
            transition={{ type: 'spring', stiffness: 500, damping: 35, mass: 0.5 }}
            onClick={clearAuth}
            className="relative flex items-center gap-1.5 h-8 px-3 rounded-xl font-mono text-xs text-text-faint hover:text-ember transition-colors duration-150 after:absolute after:inset-[-4px]"
            style={{ willChange: 'transform' }}
            title="Выйти"
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round">
              <path d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
            </svg>
            <span className="hidden sm:inline">Выйти</span>
          </motion.button>
        </div>
      </header>

      <main className="flex-1 overflow-y-auto">
        <Outlet />
      </main>

      <ProfileModal open={profileOpen} onClose={() => setProfileOpen(false)} />
    </div>
  )
}

function LogoMark() {
  return (
    <svg width="26" height="26" viewBox="0 0 26 26" fill="none" aria-hidden>
      <circle cx="13" cy="13" r="12" stroke="rgba(157,140,255,0.14)" strokeWidth="1" />
      <path
        d="M13 4l8 3.2v7c0 5-2.8 8-8 10.3C7.8 22.2 5 19.2 5 14.2V7.2L13 4z"
        fill="rgba(157,140,255,0.08)"
        stroke="rgba(157,140,255,0.8)"
        strokeWidth="1.1"
      />
      <path
        d="M9.5 13l2.2 2.2L16.5 10.5"
        stroke="rgba(157,140,255,0.9)"
        strokeWidth="1.3"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  )
}

function ProfileSigilIcon() {
  return (
    <svg width="28" height="28" viewBox="0 0 24 24" fill="none" className="text-jade" aria-hidden>
      <path d="M12 2l7 3v6c0 5-2.7 8.2-7 10.3C7.7 19.2 5 16 5 11V5l7-3z" fill="currentColor" opacity="0.12" stroke="currentColor" strokeWidth="1.2" />
      <path d="M8.8 12c.7-2 2-3 3.2-3.5M15.2 12c-.7-2-2-3-3.2-3.5M9.2 14.8c.9 1.1 4.7 1.1 5.6 0" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" />
      <circle cx="10.2" cy="11.4" r="0.9" fill="currentColor" />
      <circle cx="13.8" cy="11.4" r="0.9" fill="currentColor" />
    </svg>
  )
}

function ProfileChipIcon() {
  return (
    <svg width="11" height="11" viewBox="0 0 24 24" fill="none" className="text-jade" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
      <path d="M12 2l7 3v6c0 5-2.7 8.2-7 10.3C7.7 19.2 5 16 5 11V5l7-3z" />
    </svg>
  )
}
