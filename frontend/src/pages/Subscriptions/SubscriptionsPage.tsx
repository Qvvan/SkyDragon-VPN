import { motion } from 'framer-motion'
import { Badge } from '../../components/ui/Badge'
import { SkeletonCard } from '../../components/ui/Skeleton'
import { useSubscriptions } from '../../hooks/useSubscriptions'
import type { Subscription } from '../../types/subscription.types'

function statusVariant(status: Subscription['status']): 'jade' | 'trial' | 'muted' | 'amber' {
  if (status === 'active')  return 'jade'
  if (status === 'trial')   return 'trial'
  if (status === 'pending') return 'amber'
  return 'muted'
}

const statusLabel: Record<Subscription['status'], string> = {
  active:  'Активна',
  trial:   'Пробная',
  expired: 'Истекла',
  pending: 'Ожидание',
}

export function SubscriptionsContent() {
  const { data: subscriptions, isLoading } = useSubscriptions()

  if (isLoading) return (
    <div className="space-y-4">
      {[1, 2, 3].map((i) => <SkeletonCard key={i} />)}
    </div>
  )

  if (!subscriptions?.length) return (
    <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4 }}
      className="text-center py-16">
      <div className="mb-4 flex justify-center"><NoSubscriptionsIcon /></div>
      <p className="font-display text-xl text-text mb-2 text-balance">Нет подписок</p>
      <p className="font-mono text-sm text-text-dim text-pretty">Начните с бесплатного пробного периода на 5 дней</p>
    </motion.div>
  )

  return (
    <motion.div
      initial="hidden"
      animate="visible"
      variants={{ visible: { transition: { staggerChildren: 0.07 } } }}
      className="space-y-4"
    >
      {subscriptions.map((sub) => (
        <motion.div
          key={sub.id}
          variants={{ hidden: { opacity: 0, y: 12 }, visible: { opacity: 1, y: 0 } }}
          transition={{ duration: 0.35, ease: 'easeOut' }}
          className="rounded-[20px] p-2 bg-surface shadow-card"
        >
          <div className="rounded-[12px] bg-surface-2 p-4">
            <div className="flex items-start justify-between gap-4 mb-3">
              <div className="min-w-0">
                <h3 className="font-display text-base text-text truncate">{sub.serviceName}</h3>
                <p className="font-mono text-xs text-text-dim mt-0.5">
                  {sub.status === 'expired'
                    ? `Истекла ${new Date(sub.expiresAt).toLocaleDateString('ru-RU', { day: 'numeric', month: 'long', year: 'numeric' })}`
                    : `До ${new Date(sub.expiresAt).toLocaleDateString('ru-RU', { day: 'numeric', month: 'long', year: 'numeric' })}`}
                </p>
              </div>
              <Badge variant={statusVariant(sub.status)}>{statusLabel[sub.status]}</Badge>
            </div>

            {(sub.status === 'active' || sub.status === 'trial') && (
              <div className="mb-2">
                <div className="flex justify-between items-center mb-1.5">
                  <span className="font-mono text-xs text-text-dim">Осталось</span>
                  <span className="font-mono text-xs text-jade tabular-nums">{sub.daysRemaining} / {sub.totalDays} дней</span>
                </div>
                <div className="h-1.5 rounded-full bg-surface-3 overflow-hidden">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${(sub.daysRemaining / sub.totalDays) * 100}%` }}
                    transition={{ duration: 0.7, ease: 'easeOut', delay: 0.1 }}
                    className="h-full rounded-full bg-jade"
                  />
                </div>
              </div>
            )}
          </div>
        </motion.div>
      ))}
    </motion.div>
  )
}

export function SubscriptionsPage() {
  return (
    <div className="px-4 md:px-8 py-8 max-w-3xl mx-auto">
      <SubscriptionsContent />
    </div>
  )
}

function NoSubscriptionsIcon() {
  return (
    <svg width="44" height="44" viewBox="0 0 24 24" fill="none" className="text-jade opacity-70" aria-hidden>
      <path d="M12 2l7 3v6c0 5-2.7 8.2-7 10.3C7.7 19.2 5 16 5 11V5l7-3z" stroke="currentColor" strokeWidth="1.4" />
      <path d="M9.6 11.7l1.7 1.7 3.4-3.4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}
