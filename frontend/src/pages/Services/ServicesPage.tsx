import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Button } from '../../components/ui/Button'
import { Badge } from '../../components/ui/Badge'
import { Modal } from '../../components/ui/Modal'
import { SkeletonCard } from '../../components/ui/Skeleton'
import { useServices, useSubscribeService } from '../../hooks/useServices'
import { useUIStore } from '../../stores/ui.store'
import type { Service } from '../../types/service.types'

function durationLabel(days: number): string {
  if (days === 30)  return '30 дней'
  if (days === 60)  return '60 дней'
  if (days === 90)  return '90 дней'
  if (days === 365) return '1 год'
  return `${days} дней`
}

export function ServicesContent() {
  const { data: services, isLoading } = useServices()
  const subscribe = useSubscribeService()
  const { addToast } = useUIStore()

  const [confirm, setConfirm] = useState<Service | null>(null)

  async function handleSubscribe() {
    if (!confirm) return
    try {
      await subscribe.mutateAsync({ serviceId: confirm.id })
      addToast(`Подписка на ${confirm.name} оформлена!`)
      setConfirm(null)
    } catch {
      addToast('Ошибка оформления. Попробуйте снова.', 'error')
    }
  }

  if (isLoading) return (
    <div className="space-y-4">
      {[1, 2, 3, 4].map((i) => <SkeletonCard key={i} />)}
    </div>
  )

  return (
    <>
      <motion.div
        initial="hidden"
        animate="visible"
        variants={{ visible: { transition: { staggerChildren: 0.07 } } }}
        className="space-y-3"
      >
        {services?.map((service) => (
          <motion.div
            key={service.id}
            variants={{ hidden: { opacity: 0, y: 10 }, visible: { opacity: 1, y: 0 } }}
            transition={{ duration: 0.35, ease: 'easeOut' }}
            className="rounded-[14px] p-1 bg-surface shadow-card"
          >
            <div className="rounded-[10px] bg-surface-2 px-3 py-2.5 flex items-center gap-3">
              {/* Left: concise info */}
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-1.5 flex-wrap mb-0.5">
                  <h3 className="font-display text-[13px] leading-none text-text truncate">{service.name}</h3>
                  {service.popular && <Badge variant="jade">Топ</Badge>}
                </div>
                <span className="inline-flex items-center gap-1 font-mono text-[10px] text-jade bg-jade-dim px-1.5 py-0.5 rounded-full">
                    <svg width="8" height="8" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                      <circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/>
                    </svg>
                    {durationLabel(service.durationDays)}
                </span>
              </div>

              {/* Right: price + action */}
              <div className="flex items-center gap-2.5 shrink-0">
                <p className="font-mono text-sm text-jade tabular-nums">${service.price.toFixed(2)}</p>
                <Button
                  size="sm"
                  variant="primary"
                  onClick={() => setConfirm(service)}
                >
                  Выбрать
                </Button>
              </div>
            </div>
          </motion.div>
        ))}
      </motion.div>

      {/* Confirm modal */}
      <AnimatePresence>
        {confirm && (
          <Modal open onClose={() => setConfirm(null)} title="Подтверждение">
            <div className="p-6 space-y-4">
              <div className="rounded-xl bg-surface-3 p-4 space-y-2.5">
                <div className="flex justify-between items-center">
                  <span className="font-mono text-xs text-text-dim">Услуга</span>
                  <span className="font-mono text-sm text-text">{confirm.name}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="font-mono text-xs text-text-dim">Срок</span>
                  <span className="font-mono text-sm text-text">{durationLabel(confirm.durationDays)}</span>
                </div>
                <div className="flex justify-between items-center pt-2 border-t border-[rgba(157,140,255,0.08)]">
                  <span className="font-mono text-xs text-text-dim">Итого</span>
                  <span className="font-mono text-lg text-jade tabular-nums">${confirm.price.toFixed(2)}</span>
                </div>
              </div>
              <div className="flex gap-3">
                <Button
                  variant="primary"
                  className="flex-1"
                  loading={subscribe.isPending}
                  onClick={handleSubscribe}
                >
                  Оформить
                </Button>
                <Button variant="ghost" onClick={() => setConfirm(null)}>Отмена</Button>
              </div>
            </div>
          </Modal>
        )}
      </AnimatePresence>
    </>
  )
}

export function ServicesPage() {
  return (
    <div className="px-4 md:px-8 py-8 max-w-4xl mx-auto">
      <ServicesContent />
    </div>
  )
}
