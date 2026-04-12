import { useEffect, useRef, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Button } from '../../components/ui/Button'
import { Badge } from '../../components/ui/Badge'
import { Toggle } from '../../components/ui/Toggle'
import { Modal } from '../../components/ui/Modal'
import { Skeleton, SkeletonCard } from '../../components/ui/Skeleton'
import { useAuthStore } from '../../stores/auth.store'
import { useSubscriptions, useToggleAutoRenewal } from '../../hooks/useSubscriptions'
import { usePayments } from '../../hooks/usePayments'
import { useReferralStats } from '../../hooks/useReferrals'

import { useActivateTrial, useServices } from '../../hooks/useServices'
import { ServicesContent } from '../Services/ServicesPage'
import { PaymentsContent } from '../Payments/PaymentsPage'
import { ReferralsContent } from '../Referrals/ReferralsPage'
import { useUIStore } from '../../stores/ui.store'
import type { Subscription } from '../../types/subscription.types'

type ModalSection = 'services' | 'payments' | 'referrals' | 'trial-success' | 'instructions' | null

const TELEGRAM = {
  channel: 'https://t.me/skydragonvpn',
  bot:     'https://t.me/skydragonvpn_bot',
  support: 'https://t.me/SkyDragonSupport',
}

const ease = [0.16, 1, 0.3, 1] as const

const fadeUp = {
  hidden:  { opacity: 0, y: 18, filter: 'blur(5px)' },
  visible: { opacity: 1, y:  0, filter: 'blur(0px)' },
}

const stagger = {
  hidden:  {},
  visible: { transition: { staggerChildren: 0.08 } },
}

const fadeUpTransition = { duration: 0.5, ease } as const

// ─── Animated counter ──────────────────────────────────────────────────────────
function AnimatedNumber({ value }: { value: number }) {
  const [displayed, setDisplayed] = useState(0)
  const started = useRef(false)

  useEffect(() => {
    if (started.current) return
    started.current = true
    const dur = 850
    const t0 = Date.now()
    const tick = () => {
      const p = Math.min((Date.now() - t0) / dur, 1)
      setDisplayed(Math.round((1 - Math.pow(1 - p, 3)) * value))
      if (p < 1) requestAnimationFrame(tick)
    }
    requestAnimationFrame(tick)
  }, [value])

  return <span className="tabular-nums">{displayed}</span>
}

// ─── Section header ───────────────────────────────────────────────────────────
function SectionLabel({
  label,
  badge,
}: {
  label: string
  badge?: React.ReactNode
}) {
  return (
    <div className="flex items-center gap-3 mb-4 md:mb-5">
      <h2
        className="font-display text-lg md:text-xl font-medium text-text shrink-0"
        style={{ textWrap: 'balance' } as React.CSSProperties}
      >
        {label}
      </h2>
      {badge && <span className="shrink-0">{badge}</span>}
      <div
        className="flex-1 h-px"
        style={{ background: 'linear-gradient(90deg, rgba(157,140,255,0.22) 0%, transparent 100%)' }}
      />
    </div>
  )
}

// ─── Circular progress ────────────────────────────────────────────────────────
function CircularProgress({
  value,
  total,
  color = '#9d8cff',
  compact = false,
}: {
  value: number
  total: number
  color?: string
  compact?: boolean
}) {
  const r = compact ? 22 : 34
  const stroke = compact ? 2.5 : 3.5
  const C = 2 * Math.PI * r
  const progress = total > 0 ? Math.min(value / total, 1) : 0
  const offset = C * (1 - progress)
  const size = (r + stroke) * 2

  return (
    <div className="relative shrink-0" style={{ width: size, height: size }}>
      <svg
        width={size}
        height={size}
        viewBox={`0 0 ${size} ${size}`}
        className="-rotate-90"
        style={{ position: 'absolute', inset: 0 }}
      >
        <circle
          cx={r + stroke} cy={r + stroke} r={r}
          fill="none" stroke="rgba(157,140,255,0.08)" strokeWidth={stroke}
        />
        <motion.circle
          cx={r + stroke} cy={r + stroke} r={r}
          fill="none"
          stroke={color}
          strokeWidth={stroke}
          strokeLinecap="round"
          strokeDasharray={C}
          initial={{ strokeDashoffset: C }}
          animate={{ strokeDashoffset: offset }}
          transition={{ duration: 1.2, ease: 'easeOut', delay: 0.3 }}
          style={{ filter: `drop-shadow(0 0 4px ${color}88)` }}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span
          className="font-mono font-semibold leading-none tabular-nums"
          style={{ color, fontSize: compact ? '11px' : '15px' }}
        >
          {value}
        </span>
        <span
          className="font-mono text-text-dim mt-0.5"
          style={{ fontSize: compact ? '7px' : '9px' }}
        >
          дней
        </span>
      </div>
    </div>
  )
}

// ─── Bento card ───────────────────────────────────────────────────────────────
interface BentoCardProps {
  children: React.ReactNode
  className?: string
  innerClassName?: string
  glow?: boolean
  grid?: boolean
  accent?: 'jade' | 'ember' | 'gold'
  onClick?: () => void
  href?: string
}

function BentoCard({ children, className = '', innerClassName = '', glow, grid, accent, onClick, href }: BentoCardProps) {
  const isInteractive = !!onClick || !!href
  const Tag = href ? 'a' : 'div'
  const extraProps = href ? { href, target: '_blank', rel: 'noopener noreferrer' } : {}

  const accentColor = {
    jade:  'rgba(157,140,255,0.65)',
    ember: 'rgba(248,113,113,0.65)',
    gold:  'rgba(226,185,110,0.65)',
  }

  return (
    <motion.div
      whileHover={isInteractive ? { y: -3 } : undefined}
      whileTap={isInteractive ? { scale: 0.98 } : undefined}
      transition={{ type: 'spring', duration: 0.28, bounce: 0 }}
      className={[
        'relative rounded-[24px] overflow-hidden',
        isInteractive ? 'cursor-pointer' : '',
        glow ? 'animate-pulse-jade' : 'shadow-card',
        className,
      ].filter(Boolean).join(' ')}
      style={{ background: 'rgba(13,12,31,0.9)', border: '1px solid rgba(157,140,255,0.1)' }}
    >
      {/* Grid texture */}
      {grid && (
        <div
          className="absolute inset-0 pointer-events-none"
          style={{
            backgroundImage:
              'repeating-linear-gradient(45deg,rgba(157,140,255,0.013)0px,rgba(157,140,255,0.013)1px,transparent 1px,transparent 48px),' +
              'repeating-linear-gradient(-45deg,rgba(157,140,255,0.013)0px,rgba(157,140,255,0.013)1px,transparent 1px,transparent 48px)',
          }}
        />
      )}
      {/* Top accent line */}
      {accent && (
        <div
          className="absolute top-0 left-0 right-0 h-px"
          style={{
            background: `linear-gradient(90deg, transparent, ${accentColor[accent]}, transparent)`,
          }}
        />
      )}

      {/* eslint-disable-next-line @typescript-eslint/no-explicit-any */}
      <Tag
        className={['relative h-full block', innerClassName || 'p-4 md:p-5'].join(' ')}
        onClick={onClick}
        {...(extraProps as any)}
      >
        {children}
      </Tag>
    </motion.div>
  )
}

// ─── Subscription card ────────────────────────────────────────────────────────
function SubscriptionCard({
  sub,
  onRenew,
}: {
  sub: Subscription
  onRenew: (sub: Subscription) => void
}) {
  const toggleAutoRenewal = useToggleAutoRenewal()
  const [confirmDisable, setConfirmDisable] = useState(false)
  const isHealthy = sub.daysRemaining / sub.totalDays > 0.3

  const isTrial  = sub.status === 'trial'
  const isLocked = sub.status === 'expired' || isTrial

  function handleToggle(enabled: boolean) {
    if (!enabled && sub.autoRenewal) {
      setConfirmDisable(true)
    } else if (!isLocked) {
      toggleAutoRenewal.mutate({ id: sub.id, enabled })
    }
  }

  const statusLabel: Record<Subscription['status'], string> = {
    active:  'Активна',
    trial:   'Пробная',
    expired: 'Истекла',
    pending: 'Ожидание',
  }

  const badgeVariant =
    sub.status === 'trial'   ? 'trial' :
    sub.status === 'active'  ? 'green' :
    sub.status === 'expired' ? 'ember' : 'amber'

  const progressColor = isHealthy ? '#9d8cff' : '#f87171'

  const expiresFormatted = new Date(sub.expiresAt).toLocaleDateString('ru-RU', {
    day: 'numeric', month: 'long', year: 'numeric',
  })

  return (
    <>
    <BentoCard
      grid={sub.status === 'active' || sub.status === 'trial'}
      accent={sub.status === 'expired' ? 'ember' : (isHealthy ? 'jade' : 'ember')}
      glow={sub.status === 'trial'}
      innerClassName="p-0"
    >
      {/* ── Mobile layout (compact) ── */}
      <div className="md:hidden p-4">
        {/* Row 1: plan type + badge */}
        <div className="flex items-start justify-between gap-2 mb-2.5">
          <div className="min-w-0 flex-1">
            <p className="font-mono text-[9px] text-text-faint uppercase tracking-wider mb-1">
              {sub.status === 'trial' ? 'Пробный период' : 'Тарифный план'}
            </p>
            <h3 className="font-display text-base font-medium text-text leading-snug truncate">{sub.serviceName}</h3>
          </div>
          <Badge variant={badgeVariant}>{statusLabel[sub.status]}</Badge>
        </div>

        {/* Row 2: circle + info + renew */}
        {(sub.status === 'active' || sub.status === 'trial') && (
          <div className="flex items-center gap-3 mb-2.5">
            <CircularProgress value={sub.daysRemaining} total={sub.totalDays} color={progressColor} compact />
            <div className="flex-1 min-w-0">
              <p className="font-mono text-[9px] text-text-faint uppercase tracking-wider mb-0.5">Истекает</p>
              <p className="font-mono text-xs text-text leading-snug">{expiresFormatted}</p>
            </div>
            <Button size="sm" variant="primary" onClick={() => onRenew(sub)}>Продлить</Button>
          </div>
        )}

        {sub.status === 'expired' && (
          <div className="flex items-center justify-between mb-2.5">
            <p className="font-mono text-xs text-ember">Истекла {expiresFormatted}</p>
            <Button size="sm" variant="primary" onClick={() => onRenew(sub)}>Продлить</Button>
          </div>
        )}

        {/* Row 3: auto-renewal */}
        <div
          className="flex items-center justify-between pt-2.5"
          style={{ borderTop: '1px solid rgba(157,140,255,0.07)' }}
        >
          <span className="font-mono text-[10px] text-text-dim">Автопродление</span>
          <Toggle
            checked={isTrial ? false : sub.autoRenewal}
            onChange={handleToggle}
            disabled={isLocked}
            label="Автопродление"
          />
        </div>
      </div>

      {/* ── Desktop layout (full) ── */}
      <div className="hidden md:block p-5">
        {/* Header */}
        <div className="flex items-start justify-between gap-2 mb-5">
          <div className="min-w-0">
            <p className="font-mono text-[10px] text-text-faint uppercase tracking-wider mb-1.5">
              {sub.status === 'trial' ? 'Пробный период' : 'Тарифный план'}
            </p>
            <h3 className="font-display text-xl font-medium text-text leading-snug truncate">{sub.serviceName}</h3>
          </div>
          <Badge variant={badgeVariant}>{statusLabel[sub.status]}</Badge>
        </div>

        {/* Active / Trial */}
        {(sub.status === 'active' || sub.status === 'trial') && (
          <div className="flex items-center gap-5 mb-5">
            <CircularProgress value={sub.daysRemaining} total={sub.totalDays} color={progressColor} />
            <div className="min-w-0">
              <p className="font-mono text-[10px] text-text-faint uppercase tracking-wider mb-1">Истекает</p>
              <p className="font-mono text-sm text-text leading-snug">{expiresFormatted}</p>
            </div>
          </div>
        )}

        {/* Expired */}
        {sub.status === 'expired' && (
          <p className="font-mono text-sm text-ember mb-5">
            Истекла {expiresFormatted}
          </p>
        )}

        {/* Footer */}
        <div
          className="flex items-center justify-between pt-3"
          style={{ borderTop: '1px solid rgba(157,140,255,0.07)' }}
        >
          <Button size="sm" variant="primary" onClick={() => onRenew(sub)}>Продлить</Button>
          <div className="flex items-center gap-2">
            <span className="font-mono text-xs text-text-dim">Автопродление</span>
            <Toggle
              checked={isTrial ? false : sub.autoRenewal}
              onChange={handleToggle}
              disabled={isLocked}
              label="Автопродление"
            />
          </div>
        </div>
      </div>
    </BentoCard>

    {/* Confirm disable auto-renewal */}
    <Modal open={confirmDisable} onClose={() => setConfirmDisable(false)} title="Отключить автопродление?" size="sm">
      <div className="px-6 sm:px-7 pb-7 pt-4 space-y-5">
        <p className="font-mono text-sm sm:text-base text-text-dim leading-relaxed">
          Подписка не будет продлена автоматически. Когда срок истечёт — нужно будет продлить вручную.
        </p>
        <div className="flex gap-3">
          <Button
            variant="primary"
            size="lg"
            className="flex-1"
            loading={toggleAutoRenewal.isPending}
            onClick={() => {
              toggleAutoRenewal.mutate({ id: sub.id, enabled: false })
              setConfirmDisable(false)
            }}
          >
            Отключить
          </Button>
          <Button variant="ghost" size="lg" onClick={() => setConfirmDisable(false)}>Отмена</Button>
        </div>
      </div>
    </Modal>
    </>
  )
}

// ─── Management card ──────────────────────────────────────────────────────────
interface ManagementCardProps {
  accent: 'jade' | 'gold'
  icon: React.ReactNode
  title: string
  children: React.ReactNode
  onClick: () => void
}

function ManagementCard({ accent, icon, title, children, onClick }: ManagementCardProps) {
  const iconBg = accent === 'jade'
    ? 'bg-jade-dim text-jade'
    : 'bg-gold-dim text-gold'

  return (
    <BentoCard onClick={onClick} accent={accent} className="group" innerClassName="p-4 md:p-5 h-full">
      <div className="flex flex-col h-full min-h-[110px] md:min-h-[130px]">
        {/* Icon row */}
        <div className="flex items-center justify-between mb-3 md:mb-4">
          <div className={`size-9 md:size-12 rounded-xl md:rounded-2xl ${iconBg} flex items-center justify-center`}>
            {/* Mobile icon (15px) */}
            <span className="md:hidden">{icon}</span>
            {/* Desktop icon (20px) */}
            <span className="hidden md:block scale-[1.35]">{icon}</span>
          </div>
          <motion.span
            className="text-text-faint group-hover:text-text-dim"
            initial={false}
            whileHover={{ x: 2, y: -2 }}
            transition={{ type: 'spring', duration: 0.2, bounce: 0 }}
          >
            <ArrowUpRight size="md" />
          </motion.span>
        </div>
        {/* Label */}
        <p className="font-display text-base md:text-lg font-medium text-text mb-1.5">{title}</p>
        {/* Meta */}
        <div className="font-mono text-xs md:text-sm text-text-dim flex-1">{children}</div>
      </div>
    </BentoCard>
  )
}

// ─── Dashboard ────────────────────────────────────────────────────────────────
export function DashboardPage() {
  const { user } = useAuthStore()
  const { data: subscriptions, isLoading: loadingSubs }      = useSubscriptions()
  const { data: payments, isLoading: loadingPayments }       = usePayments()
  const { data: referralStats, isLoading: loadingReferrals } = useReferralStats()
  const { data: services } = useServices()
  const activateTrial = useActivateTrial()
  const { addToast }     = useUIStore()

  const [activeModal, setActiveModal] = useState<ModalSection>(null)
  const [renewTarget, setRenewTarget] = useState<Subscription | null>(null)
  const [trialEndDate, setTrialEndDate] = useState('')

  const lastPayment      = payments?.[0]
  const hasNoSubs        = !loadingSubs && (!subscriptions || subscriptions.length === 0)
  const hasUnusedTrial   = hasNoSubs
  const trialAlreadyUsed = !loadingSubs && !!subscriptions && subscriptions.length > 0
  const activeSubs       = subscriptions?.filter(s => s.status === 'active' || s.status === 'trial') ?? []

  function openRenewModal(sub: Subscription) {
    setRenewTarget(sub)
  }

  async function handleActivateTrial() {
    try {
      const result = await activateTrial.mutateAsync()
      setTrialEndDate(result.endDate)
      setActiveModal('trial-success')
    } catch {
      addToast('Не удалось активировать пробный период. Попробуйте снова.', 'error')
    }
  }

  return (
    <div className="px-4 md:px-8 py-8 md:py-10 max-w-5xl mx-auto">
      <motion.div
        initial="hidden"
        animate="visible"
        variants={stagger}
        className="space-y-8 md:space-y-10"
      >
        {/* ── Greeting ── */}
        <motion.div variants={fadeUp} transition={fadeUpTransition}>
          <h1 className="font-display text-3xl md:text-5xl font-light text-text text-balance leading-tight">
            С возвращением,{' '}
            <span
              style={{
                background: 'linear-gradient(135deg, #c4b5fd 0%, #9d8cff 60%, #818cf8 100%)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                backgroundClip: 'text',
              }}
            >
              {user ? `${user.firstName} ${user.lastName}`.trim() || 'Пользователь' : 'Пользователь'}
            </span>
          </h1>
          <p className="font-mono text-[11px] md:text-xs text-text-faint mt-2 uppercase tracking-[0.14em]">
            Командный центр
          </p>
        </motion.div>

        {/* ── Telegram quick links ── */}
        <motion.div variants={fadeUp} transition={fadeUpTransition}>
          <div className="flex items-center gap-2 flex-wrap">
            <span className="font-mono text-[10px] text-text-faint uppercase tracking-wider">Telegram:</span>
            <a
              href={TELEGRAM.channel}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1.5 h-7 px-3 rounded-full font-mono text-[11px] md:text-xs text-jade transition-colors duration-150 hover:text-[#c4b5fd] active:scale-[0.96] transition-transform"
              style={{ background: 'rgba(157,140,255,0.07)', border: '1px solid rgba(157,140,255,0.14)' }}
            >
              <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                <path d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"/>
              </svg>
              Новости
            </a>
            <a
              href={TELEGRAM.bot}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1.5 h-7 px-3 rounded-full font-mono text-[11px] md:text-xs text-gold transition-colors duration-150 hover:brightness-110 active:scale-[0.96] transition-transform"
              style={{ background: 'rgba(226,185,110,0.07)', border: '1px solid rgba(226,185,110,0.16)' }}
            >
              <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                <rect x="3" y="11" width="18" height="10" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/><circle cx="12" cy="16" r="1" fill="currentColor"/>
              </svg>
              Бот
            </a>
            <a
              href={TELEGRAM.support}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1.5 h-7 px-3 rounded-full font-mono text-[11px] md:text-xs text-ember transition-colors duration-150 hover:brightness-110 active:scale-[0.96] transition-transform"
              style={{ background: 'rgba(248,113,113,0.07)', border: '1px solid rgba(248,113,113,0.16)' }}
            >
              <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                <path d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"/>
              </svg>
              Поддержка
            </a>
          </div>
        </motion.div>

        {/* ── Trial banner ── */}
        <AnimatePresence initial={false}>
          {hasUnusedTrial && (
            <motion.div
              key="trial-available"
              variants={fadeUp}
              transition={fadeUpTransition}
              exit={{ opacity: 0, y: -10, filter: 'blur(4px)', transition: { duration: 0.15, ease: 'easeIn' } }}
            >
              <BentoCard glow onClick={handleActivateTrial} innerClassName="p-0">
                <div className="flex items-center justify-between gap-4 p-4 md:p-5">
                  <div className="flex items-center gap-3">
                    <TrialSparkIcon />
                    <div>
                      <p className="font-display text-base md:text-lg font-medium text-jade text-balance">
                        Пробный период доступен
                      </p>
                      <p className="font-mono text-xs md:text-sm text-jade opacity-65 mt-0.5 text-pretty">
                        5 дней бесплатно — без карты
                      </p>
                    </div>
                  </div>
                  <Button size="sm" variant="primary" staticPress loading={activateTrial.isPending}>
                    Активировать
                  </Button>
                </div>
              </BentoCard>
            </motion.div>
          )}
          {trialAlreadyUsed && (
            <motion.div
              key="trial-used"
              variants={fadeUp}
              transition={fadeUpTransition}
            >
              <BentoCard innerClassName="p-0">
                <div className="flex items-center gap-4 p-4 md:p-5 opacity-40 select-none">
                  <div className="flex items-center gap-3 flex-1 min-w-0">
                    <span className="size-10 md:size-12 rounded-xl flex items-center justify-center shrink-0"
                      style={{ background: 'rgba(157,140,255,0.07)', border: '1px solid rgba(157,140,255,0.1)' }}>
                      <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M13 2L5 14h6l-1 8 9-13h-6l0-7z" />
                      </svg>
                    </span>
                    <div className="min-w-0">
                      <p className="font-display text-base md:text-lg font-medium text-text-dim text-balance">
                        Пробный период использован
                      </p>
                      <p className="font-mono text-xs md:text-sm text-text-faint mt-0.5 text-pretty">
                        5 дней уже были активированы
                      </p>
                    </div>
                  </div>
                  <span className="font-mono text-xs text-text-faint shrink-0 whitespace-nowrap">Недоступно</span>
                </div>
              </BentoCard>
            </motion.div>
          )}
        </AnimatePresence>

        {/* ── Подписки ── */}
        <motion.div variants={fadeUp} transition={fadeUpTransition}>
          <SectionLabel
            label="Подписки"
            badge={
              !loadingSubs && activeSubs.length > 0 ? (
                <span
                  className="font-mono text-[11px] text-jade tabular-nums px-2 py-0.5 rounded-full"
                  style={{ background: 'rgba(157,140,255,0.1)', border: '1px solid rgba(157,140,255,0.2)' }}
                >
                  {activeSubs.length} активных
                </span>
              ) : undefined
            }
          />

          {loadingSubs ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 md:gap-4">
              <SkeletonCard /><SkeletonCard />
            </div>
          ) : hasNoSubs ? (
            <BentoCard onClick={() => setActiveModal('services')} className="group">
              <div className="flex flex-col items-center justify-center py-8 md:py-12 text-center">
                <div className="mb-3 opacity-40"><DragonShieldIcon /></div>
                <p className="font-display text-lg md:text-xl font-medium text-text mb-2 text-balance">Нет подписок</p>
                <p className="font-mono text-sm md:text-base text-text-dim mb-5 text-pretty">
                  Начните с бесплатного пробного периода на 5 дней
                </p>
                <Button size="sm" variant="primary" staticPress>Смотреть услуги →</Button>
              </div>
            </BentoCard>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 md:gap-4">
              {subscriptions!.map((sub, i) => (
                <motion.div
                  key={sub.id}
                  variants={{ hidden: { opacity: 0, y: 14 }, visible: { opacity: 1, y: 0 } }}
                  transition={{ duration: 0.42, ease: 'easeOut', delay: i * 0.06 }}
                >
                  <SubscriptionCard sub={sub} onRenew={openRenewModal} />
                </motion.div>
              ))}
            </div>
          )}
        </motion.div>

        {/* ── Instructions banner (only when has subscriptions) ── */}
        {!hasNoSubs && !loadingSubs && (
          <motion.div variants={fadeUp} transition={fadeUpTransition}>
            <button
              onClick={() => setActiveModal('instructions')}
              className="w-full text-left group"
            >
              <div
                className="relative rounded-[24px] overflow-hidden transition-all duration-300 hover:-translate-y-0.5"
                style={{
                  background: 'linear-gradient(135deg, rgba(168,153,255,0.07) 0%, rgba(99,102,241,0.05) 50%, rgba(34,211,238,0.06) 100%)',
                  border: '1px solid rgba(157,140,255,0.14)',
                }}
              >
                <div
                  className="absolute top-0 left-0 right-0 h-px"
                  style={{ background: 'linear-gradient(90deg, transparent, rgba(157,140,255,0.5), rgba(34,211,238,0.3), transparent)' }}
                />
                <div className="flex items-center justify-between gap-4 px-4 md:px-6 py-4 md:py-5">
                  <div className="flex items-center gap-3 md:gap-4">
                    <div
                      className="size-10 md:size-12 rounded-xl md:rounded-2xl flex items-center justify-center shrink-0"
                      style={{
                        background: 'linear-gradient(135deg, rgba(157,140,255,0.15) 0%, rgba(34,211,238,0.1) 100%)',
                        border: '1px solid rgba(157,140,255,0.2)',
                      }}
                    >
                      <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className="text-jade">
                        <path d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
                      </svg>
                    </div>
                    <div>
                      <p className="font-display text-base md:text-lg font-medium text-text group-hover:text-jade transition-colors duration-200">
                        Инструкция по подключению
                      </p>
                      <p className="font-mono text-[10px] md:text-xs text-text-faint mt-0.5">
                        Настройка VPN на всех устройствах
                      </p>
                    </div>
                  </div>
                  <motion.div
                    className="text-text-faint group-hover:text-jade transition-colors duration-200 shrink-0"
                    whileHover={{ x: 2, y: -2 }}
                    transition={{ type: 'spring', duration: 0.2, bounce: 0 }}
                  >
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round">
                      <path d="M7 17L17 7M17 7H7M17 7v10"/>
                    </svg>
                  </motion.div>
                </div>
              </div>
            </button>
          </motion.div>
        )}

        {/* ── Управление ── */}
        <motion.div variants={fadeUp} transition={fadeUpTransition}>
          <SectionLabel label="Управление" />
          <div className="grid grid-cols-2 gap-3 md:gap-4">
            {/* Services */}
            <ManagementCard
              accent="jade"
              onClick={() => setActiveModal('services')}
              icon={
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round">
                  <path d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
                </svg>
              }
              title="Услуги"
            >
              {services?.length ?? 0} тарифов
            </ManagementCard>

            {/* Payments */}
            <ManagementCard
              accent="gold"
              onClick={() => setActiveModal('payments')}
              icon={
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round">
                  <rect x="2" y="5" width="20" height="14" rx="2"/><path d="M2 10h20"/>
                </svg>
              }
              title="Платежи"
            >
              {loadingPayments ? (
                <Skeleton className="h-3 w-20 mt-1" />
              ) : lastPayment
                ? `Последний: ${lastPayment.amount.toLocaleString('ru-RU', { style: 'currency', currency: 'RUB', maximumFractionDigits: 0 })}`
                : 'История платежей'
              }
            </ManagementCard>

            {/* Referrals */}
            <ManagementCard
              accent="jade"
              onClick={() => setActiveModal('referrals')}
              icon={
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round">
                  <path d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z"/>
                </svg>
              }
              title="Рефералы"
            >
              {loadingReferrals ? (
                <Skeleton className="h-3 w-20 mt-1" />
              ) : (
                <div className="flex gap-4 mt-1">
                  <div>
                    <p className="font-mono text-lg md:text-xl text-jade tabular-nums leading-none">
                      <AnimatedNumber value={referralStats?.totalReferrals ?? 0} />
                    </p>
                    <p className="font-mono text-[10px] text-text-faint mt-0.5">друзей</p>
                  </div>
                  <div>
                    <p className="font-mono text-lg md:text-xl text-jade tabular-nums leading-none">
                      <AnimatedNumber value={referralStats?.totalBonusDays ?? 0} />
                    </p>
                    <p className="font-mono text-[10px] text-text-faint mt-0.5">бонус. дней</p>
                  </div>
                </div>
              )}
            </ManagementCard>

          </div>
        </motion.div>


      </motion.div>

      {/* ── Renewal modal ── */}
      <Modal open={!!renewTarget} onClose={() => setRenewTarget(null)} title="Продление" size="xl">
        <div className="px-6 sm:px-7 py-6">
          <ServicesContent subscriptionId={renewTarget?.id} />
        </div>
      </Modal>

      {/* ── Services modal ── */}
      <Modal open={activeModal === 'services'} onClose={() => setActiveModal(null)} title="Услуги" size="xl">
        <div className="px-6 sm:px-7 py-6"><ServicesContent /></div>
      </Modal>

      {/* ── Payments modal ── */}
      <Modal open={activeModal === 'payments'} onClose={() => setActiveModal(null)} title="История платежей" size="lg">
        <div className="px-6 sm:px-7 py-6"><PaymentsContent /></div>
      </Modal>

      {/* ── Referrals modal ── */}
      <Modal open={activeModal === 'referrals'} onClose={() => setActiveModal(null)} title="Реферальная программа" size="lg">
        <div className="px-6 sm:px-7 py-6"><ReferralsContent /></div>
      </Modal>

      {/* ── Trial success modal ── */}
      <TrialSuccessModal
        open={activeModal === 'trial-success'}
        endDate={trialEndDate}
        onClose={() => setActiveModal(null)}
      />

      {/* ── Instructions modal ── */}
      <InstructionsModal
        open={activeModal === 'instructions'}
        onClose={() => setActiveModal(null)}
        importUrl={activeSubs[0]?.importUrl ?? null}
      />

    </div>
  )
}

// ─── Trial Success Modal ───────────────────────────────────────────────────────

function TrialSuccessModal({ open, endDate, onClose }: { open: boolean; endDate: string; onClose: () => void }) {
  const formatted = endDate
    ? new Intl.DateTimeFormat('ru-RU', { day: 'numeric', month: 'long' }).format(new Date(endDate))
    : ''

  return (
    <Modal open={open} onClose={onClose} size="sm">
      <div className="flex flex-col items-center text-center px-6 sm:px-8 pt-8 sm:pt-10 pb-7 sm:pb-8 gap-6 sm:gap-7">

        {/* Glow orb + animated checkmark */}
        <div className="relative flex items-center justify-center">
          <div
            className="absolute rounded-full"
            style={{
              width: 110,
              height: 110,
              background: 'radial-gradient(circle, rgba(74,222,128,0.18) 0%, transparent 70%)',
              filter: 'blur(8px)',
            }}
          />
          <div
            className="absolute rounded-full"
            style={{ width: 80, height: 80, border: '1px solid rgba(74,222,128,0.16)' }}
          />
          <motion.div
            initial={{ scale: 0.5, opacity: 0, rotate: -15 }}
            animate={{ scale: 1, opacity: 1, rotate: 0 }}
            transition={{ type: 'spring', stiffness: 380, damping: 20, delay: 0.05 }}
            className="relative z-10 flex items-center justify-center rounded-full"
            style={{
              width: 64,
              height: 64,
              background: 'linear-gradient(135deg, rgba(74,222,128,0.15) 0%, rgba(34,211,238,0.1) 100%)',
              border: '1px solid rgba(74,222,128,0.3)',
              boxShadow: '0 0 24px rgba(74,222,128,0.18)',
            }}
          >
            <svg width="26" height="26" viewBox="0 0 24 24" fill="none">
              <motion.path
                d="M5 13l4 4L19 7"
                stroke="#4ade80"
                strokeWidth="2.2"
                strokeLinecap="round"
                strokeLinejoin="round"
                initial={{ pathLength: 0 }}
                animate={{ pathLength: 1 }}
                transition={{ duration: 0.4, delay: 0.18, ease: 'easeOut' }}
              />
            </svg>
          </motion.div>
        </div>

        {/* Copy */}
        <div className="space-y-2">
          <motion.p
            className="font-mono text-xs uppercase tracking-[0.18em]"
            style={{ color: '#4ade80' }}
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.35, delay: 0.2 }}
          >
            Пробный период активирован
          </motion.p>
          <motion.p
            className="font-display font-light"
            style={{
              fontSize: 'clamp(52px, 14vw, 64px)',
              lineHeight: 1,
              background: 'linear-gradient(135deg, #f0fdf4 0%, #bbf7d0 50%, #86efac 100%)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              backgroundClip: 'text',
            }}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: 0.25 }}
          >
            5 дней
          </motion.p>
          {formatted && (
            <motion.p
              className="font-mono text-sm"
              style={{ color: 'rgba(255,255,255,0.35)' }}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.3, delay: 0.35 }}
            >
              до {formatted}
            </motion.p>
          )}
        </div>

        {/* Info strip */}
        <motion.div
          className="w-full rounded-2xl px-5 py-4 font-mono text-sm text-left leading-relaxed"
          style={{
            background: 'rgba(74,222,128,0.04)',
            border: '1px solid rgba(74,222,128,0.1)',
            color: 'rgba(255,255,255,0.38)',
          }}
          initial={{ opacity: 0, y: 6 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, delay: 0.4 }}
        >
          Карта не нужна · Автопродление не подключено · По истечении срока подписка завершится сама
        </motion.div>

        {/* CTA */}
        <motion.div
          className="w-full"
          initial={{ opacity: 0, y: 4 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, delay: 0.48 }}
        >
          <Button onClick={onClose} variant="primary" className="w-full" size="lg">
            Отлично!
          </Button>
        </motion.div>

      </div>
    </Modal>
  )
}

// ─── Icons ─────────────────────────────────────────────────────────────────────

function ArrowUpRight({ size = 'sm' }: { size?: 'sm' | 'md' }) {
  const s = size === 'md' ? 14 : 12
  return (
    <svg
      width={s} height={s} viewBox="0 0 24 24" fill="none"
      stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"
    >
      <path d="M7 17L17 7M17 7H7M17 7v10"/>
    </svg>
  )
}

function TrialSparkIcon() {
  return (
    <span className="size-10 md:size-12 rounded-xl bg-jade-dim text-jade flex items-center justify-center shadow-[0_0_0_1px_rgba(157,140,255,0.2)]">
      <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
        <path d="M13 2L5 14h6l-1 8 9-13h-6l0-7z" />
      </svg>
    </span>
  )
}

function DragonShieldIcon() {
  return (
    <svg width="44" height="44" viewBox="0 0 36 36" fill="none" className="text-jade" aria-hidden>
      <path d="M18 4l10 4v8.6c0 7-4.1 11.6-10 14.4C12.1 28.2 8 23.6 8 16.6V8l10-4z" stroke="currentColor" strokeWidth="1.4" opacity="0.7" />
      <path d="M18 11.2c-2.8 0-5.1 2.2-5.1 5 0 2 1.1 3.7 2.8 4.6l-0.9 2.8 3.2-1.3 3.2 1.3-0.9-2.8c1.7-0.9 2.8-2.6 2.8-4.6 0-2.8-2.3-5-5.1-5z" fill="currentColor" opacity="0.2" />
      <circle cx="16.4" cy="15.8" r="0.9" fill="currentColor" />
      <circle cx="19.6" cy="15.8" r="0.9" fill="currentColor" />
      <path d="M16.2 18.4c0.6 0.7 3 0.7 3.6 0" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" />
    </svg>
  )
}

// ─── Instructions Modal ────────────────────────────────────────────────────────

type PlatformKey = 'iphone' | 'android' | 'windows' | 'macos' | 'other'

interface PlatformApp {
  label: string
  url: string
}

interface PlatformConfig {
  label: string
  apps: PlatformApp[]
}

const PLATFORMS: Record<PlatformKey, PlatformConfig> = {
  iphone: {
    label: 'iPhone / iPad',
    apps: [
      { label: 'App Store (RU)',    url: 'https://apps.apple.com/ru/app/happ-proxy-utility-plus/id6746188973' },
      { label: 'App Store (EU/US)', url: 'https://apps.apple.com/us/app/happ-proxy-utility/id6504287215' },
    ],
  },
  android: {
    label: 'Android',
    apps: [
      { label: 'Google Play', url: 'https://play.google.com/store/apps/details?id=com.happproxy' },
    ],
  },
  windows: {
    label: 'Windows',
    apps: [
      { label: 'Скачать .exe', url: 'https://github.com/Happ-proxy/happ-desktop/releases/latest/download/setup-Happ.x64.exe' },
    ],
  },
  macos: {
    label: 'macOS',
    apps: [
      { label: 'App Store (RU)',    url: 'https://apps.apple.com/ru/app/happ-proxy-utility-plus/id6746188973' },
      { label: 'App Store (EU/US)', url: 'https://apps.apple.com/us/app/happ-proxy-utility/id6504287215' },
    ],
  },
  other: {
    label: 'Другое',
    apps: [
      { label: 'iOS / macOS (RU)',  url: 'https://apps.apple.com/ru/app/happ-proxy-utility-plus/id6746188973' },
      { label: 'iOS / macOS (EU)',  url: 'https://apps.apple.com/us/app/happ-proxy-utility/id6504287215' },
      { label: 'Android',           url: 'https://play.google.com/store/apps/details?id=com.happproxy' },
      { label: 'Windows .exe',      url: 'https://github.com/Happ-proxy/happ-desktop/releases/latest/download/setup-Happ.x64.exe' },
    ],
  },
}

const PLATFORM_ORDER: PlatformKey[] = ['iphone', 'android', 'windows', 'macos']

function detectPlatform(): PlatformKey {
  const ua = navigator.userAgent.toLowerCase()
  if (/iphone|ipad|ipod/.test(ua)) return 'iphone'
  if (/android/.test(ua)) return 'android'
  if (/windows/.test(ua)) return 'windows'
  if (/mac os x|macintosh/.test(ua)) return 'macos'
  return 'other'
}

function InstructionsModal({ open, onClose, importUrl }: { open: boolean; onClose: () => void; importUrl: string | null }) {
  const [platform, setPlatform] = useState<PlatformKey>('other')

  useEffect(() => {
    if (open) setPlatform(detectPlatform())
  }, [open])

  const cfg = PLATFORMS[platform]

  return (
    <Modal open={open} onClose={onClose} title="Подключение VPN" size="md">
      <div className="px-6 sm:px-7 pb-7 pt-4 space-y-5">

        {/* Platform tabs */}
        <div className="flex gap-2 flex-wrap">
          {PLATFORM_ORDER.map((key) => (
            <button
              key={key}
              onClick={() => setPlatform(key)}
              className="font-mono text-xs sm:text-sm px-3.5 py-2 rounded-full transition-all duration-150"
              style={platform === key ? {
                background: 'rgba(157,140,255,0.15)',
                border: '1px solid rgba(157,140,255,0.32)',
                color: '#c4b5fd',
              } : {
                background: 'rgba(157,140,255,0.04)',
                border: '1px solid rgba(157,140,255,0.1)',
                color: 'rgba(255,255,255,0.4)',
              }}
            >
              {PLATFORMS[key].label}
            </button>
          ))}
        </div>

        <AnimatePresence mode="wait">
          <motion.div
            key={platform}
            initial={{ opacity: 0, y: 5 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -5 }}
            transition={{ duration: 0.15, ease: 'easeOut' }}
            className="rounded-2xl overflow-hidden"
            style={{ border: '1px solid rgba(157,140,255,0.12)' }}
          >
            {/* Step 1 — download */}
            <div className="px-5 sm:px-6 py-5" style={{ borderBottom: '1px solid rgba(157,140,255,0.08)' }}>
              <div className="flex items-center gap-3 mb-4">
                <span
                  className="flex items-center justify-center size-6 rounded-full font-mono text-xs font-bold shrink-0"
                  style={{ background: 'rgba(157,140,255,0.15)', border: '1px solid rgba(157,140,255,0.28)', color: '#9d8cff' }}
                >
                  1
                </span>
                <span className="font-display text-base sm:text-lg text-text">Скачайте Happ</span>
              </div>
              <div className="flex flex-col gap-2.5">
                {cfg.apps.map((app) => (
                  <a
                    key={app.url}
                    href={app.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center justify-between w-full rounded-xl px-4 py-3.5 transition-all duration-150 active:scale-[0.98] hover:brightness-110"
                    style={{
                      background: 'linear-gradient(135deg, rgba(157,140,255,0.1) 0%, rgba(124,107,255,0.05) 100%)',
                      border: '1px solid rgba(157,140,255,0.18)',
                    }}
                  >
                    <div className="flex items-center gap-3">
                      <span
                        className="flex items-center justify-center size-9 rounded-xl shrink-0"
                        style={{ background: 'rgba(157,140,255,0.1)', border: '1px solid rgba(157,140,255,0.18)' }}
                      >
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#9d8cff" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                          <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4M7 10l5 5 5-5M12 15V3"/>
                        </svg>
                      </span>
                      <span className="font-mono text-sm sm:text-base text-text">{app.label}</span>
                    </div>
                    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="rgba(157,140,255,0.45)" strokeWidth="2" strokeLinecap="round">
                      <path d="M7 17L17 7M17 7H7M17 7v10"/>
                    </svg>
                  </a>
                ))}
              </div>
            </div>

            {/* Step 2 — import deeplink */}
            <div className="px-5 sm:px-6 py-5">
              <div className="flex items-center gap-3 mb-4">
                <span
                  className="flex items-center justify-center size-6 rounded-full font-mono text-xs font-bold shrink-0"
                  style={{ background: 'rgba(74,222,128,0.12)', border: '1px solid rgba(74,222,128,0.25)', color: '#4ade80' }}
                >
                  2
                </span>
                <span className="font-display text-base sm:text-lg text-text">Добавьте подписку</span>
              </div>
              {importUrl ? (
                <a
                  href={importUrl}
                  className="flex items-center justify-between w-full rounded-xl px-4 py-3.5 transition-all duration-150 active:scale-[0.98] hover:brightness-110"
                  style={{
                    background: 'linear-gradient(135deg, rgba(74,222,128,0.1) 0%, rgba(52,211,153,0.05) 100%)',
                    border: '1px solid rgba(74,222,128,0.2)',
                  }}
                >
                  <div className="flex items-center gap-3">
                    <span
                      className="flex items-center justify-center size-9 rounded-xl shrink-0"
                      style={{ background: 'rgba(74,222,128,0.1)', border: '1px solid rgba(74,222,128,0.2)' }}
                    >
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#4ade80" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M8 17l4 4 4-4M12 12v9M20.88 18.09A5 5 0 0018 9h-1.26A8 8 0 103 16.29"/>
                      </svg>
                    </span>
                    <span className="font-mono text-sm sm:text-base text-text">Импортировать в Happ</span>
                  </div>
                  <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="rgba(74,222,128,0.45)" strokeWidth="2" strokeLinecap="round">
                    <path d="M7 17L17 7M17 7H7M17 7v10"/>
                  </svg>
                </a>
              ) : (
                <p className="font-mono text-sm sm:text-base text-text-faint leading-relaxed">
                  Ссылка недоступна. Убедитесь, что у вас есть активная подписка.
                </p>
              )}
            </div>
          </motion.div>
        </AnimatePresence>

      </div>
    </Modal>
  )
}
