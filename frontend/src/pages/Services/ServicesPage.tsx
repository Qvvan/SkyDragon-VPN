import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Button } from '../../components/ui/Button'
import { Badge } from '../../components/ui/Badge'
import { Modal } from '../../components/ui/Modal'
import { SkeletonCard } from '../../components/ui/Skeleton'
import { useServices, useSubscribeService, useRenewSubscription } from '../../hooks/useServices'
import { useUIStore } from '../../stores/ui.store'
import type { Service } from '../../types/service.types'

function durationLabel(days: number): string {
  if (days === 30)  return '30 дней'
  if (days === 60)  return '60 дней'
  if (days === 90)  return '90 дней'
  if (days === 180) return '180 дней'
  if (days === 360) return '360 дней'
  if (days === 365) return '1 год'
  return `${days} дней`
}

interface ServicesContentProps {
  /** Если передан — режим продления существующей подписки */
  subscriptionId?: string
}

export function ServicesContent({ subscriptionId }: ServicesContentProps = {}) {
  const isRenewal = !!subscriptionId

  const { data: services, isLoading } = useServices()
  const subscribe = useSubscribeService()
  const renew     = useRenewSubscription()
  const { addToast } = useUIStore()

  const [confirm, setConfirm] = useState<Service | null>(null)

  const isPending = isRenewal ? renew.isPending : subscribe.isPending

  async function handleConfirm() {
    if (!confirm) return
    try {
      if (isRenewal) {
        await renew.mutateAsync({ subscriptionId: subscriptionId!, serviceId: confirm.id })
      } else {
        await subscribe.mutateAsync({ serviceId: confirm.id })
      }
      addToast(isRenewal ? `Продление на ${confirm.name} оформлено!` : `Подписка на ${confirm.name} оформлена!`)
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
      {/* Header */}
      <div className="mb-6">
        <h1 className="font-display text-2xl md:text-3xl text-text font-bold">
          {isRenewal ? 'Продление подписки' : 'Тарифы'}
        </h1>
        <p className="text-text-dim text-sm mt-1">
          {isRenewal ? 'Выберите тариф для продления' : 'Выберите подходящий план подписки'}
        </p>
      </div>

      {/* Cards grid */}
      <motion.div
        initial="hidden"
        animate="visible"
        variants={{ visible: { transition: { staggerChildren: 0.08 } } }}
        className="grid grid-cols-2 gap-3 sm:gap-4"
      >
        {services?.map((service) => (
          <motion.div
            key={service.id}
            variants={{ hidden: { opacity: 0, y: 16 }, visible: { opacity: 1, y: 0 } }}
            transition={{ duration: 0.35, ease: 'easeOut' }}
          >
            <div
              className={[
                'relative rounded-2xl p-4 sm:p-5 cursor-pointer h-full flex flex-col',
                'transition-all duration-200 hover:-translate-y-0.5',
                service.popular
                  ? 'shadow-card border border-[rgba(157,140,255,0.2)]'
                  : 'shadow-card border border-[rgba(157,140,255,0.08)] hover:border-[rgba(157,140,255,0.2)]',
              ].join(' ')}
              style={{
                background: service.popular
                  ? 'linear-gradient(135deg, rgba(157,140,255,0.1) 0%, rgba(13,12,31,0.95) 60%)'
                  : 'rgba(13,12,31,0.9)',
              }}
              onClick={() => setConfirm(service)}
            >
              {service.popular && (
                <div className="absolute top-3 right-3">
                  <Badge variant="jade">Топ</Badge>
                </div>
              )}

              <div className="mb-2 sm:mb-3">
                <span className="font-display text-2xl sm:text-3xl font-medium text-text leading-none">
                  {durationLabel(service.durationDays)}
                </span>
              </div>

              <div className="mb-4 sm:mb-5 flex-1">
                <span className="font-mono text-lg sm:text-2xl font-bold text-jade leading-none tabular-nums">
                  {service.price.toLocaleString('ru-RU')} ₽
                </span>
              </div>

              <Button
                variant={service.popular ? 'primary' : 'secondary'}
                size="md"
                className="w-full"
                onClick={(e) => { e.stopPropagation(); setConfirm(service) }}
              >
                {isRenewal ? 'Продлить' : 'Выбрать'}
              </Button>
            </div>
          </motion.div>
        ))}
      </motion.div>

      {/* Confirm modal */}
      <AnimatePresence>
        {confirm && (
          <Modal
            open
            onClose={() => setConfirm(null)}
            title={isRenewal ? 'Продление подписки' : 'Оформление подписки'}
          >
            <div className="px-6 sm:px-7 pb-7 pt-5 space-y-5">
              <div
                className="rounded-2xl p-5 sm:p-6 flex items-center justify-between gap-4"
                style={{ background: 'rgba(157,140,255,0.06)', border: '1px solid rgba(157,140,255,0.12)' }}
              >
                <div>
                  <p className="font-mono text-xs text-text-faint uppercase tracking-wider mb-1">Тариф</p>
                  <p className="font-display text-xl sm:text-2xl text-text leading-tight">{confirm.name}</p>
                  <p className="font-mono text-sm text-text-dim mt-1">{durationLabel(confirm.durationDays)}</p>
                </div>
                <div className="text-right shrink-0">
                  <p className="font-mono text-xs text-text-faint uppercase tracking-wider mb-1">Сумма</p>
                  <p className="font-mono text-2xl sm:text-3xl text-jade tabular-nums font-bold leading-none">
                    {confirm.price.toLocaleString('ru-RU')} ₽
                  </p>
                </div>
              </div>
              <div className="flex gap-3">
                <Button
                  variant="primary"
                  size="lg"
                  className="flex-1"
                  loading={isPending}
                  onClick={handleConfirm}
                >
                  {isRenewal ? 'Продлить подписку' : 'Оформить подписку'}
                </Button>
                <Button variant="ghost" size="lg" onClick={() => setConfirm(null)}>Отмена</Button>
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
