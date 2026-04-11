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
  if (days === 180) return '180 дней'
  if (days === 360) return '360 дней'
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
      {/* Header */}
      <div className="mb-6">
        <h1 className="font-display text-2xl md:text-3xl text-text font-bold">Тарифы</h1>
        <p className="text-text-dim text-sm mt-1">Выберите подходящий план подписки</p>
      </div>

      {/* Cards grid — всегда 2 колонки */}
      <motion.div
        initial="hidden"
        animate="visible"
        variants={{ visible: { transition: { staggerChildren: 0.08 } } }}
        className="grid grid-cols-2 gap-3"
      >
        {services?.map((service) => (
          <motion.div
            key={service.id}
            variants={{ hidden: { opacity: 0, y: 16 }, visible: { opacity: 1, y: 0 } }}
            transition={{ duration: 0.35, ease: 'easeOut' }}
          >
            <div
              className={`
                relative rounded-xl p-3 md:p-5 cursor-pointer h-full
                bg-surface shadow-card border transition-all duration-200
                hover:border-jade/30 hover:shadow-lg
                ${service.popular
                  ? 'border-jade/20 bg-gradient-to-br from-surface to-[rgba(110,231,183,0.04)]'
                  : 'border-[rgba(255,255,255,0.06)]'
                }
              `}
              onClick={() => setConfirm(service)}
            >
              {/* Popular badge */}
              {service.popular && (
                <div className="absolute top-2.5 right-2.5">
                  <Badge variant="jade">Топ</Badge>
                </div>
              )}

              {/* Duration */}
              <div className="mb-2">
                <span className="font-display text-xl md:text-3xl font-bold text-text leading-none">
                  {durationLabel(service.durationDays)}
                </span>
              </div>

              {/* Price */}
              <div className="mb-3 md:mb-5">
                <span className="font-mono text-base md:text-2xl font-bold text-jade leading-none tabular-nums">
                  {service.price.toLocaleString('ru-RU')} ₽
                </span>
              </div>

              {/* CTA */}
              <Button
                variant={service.popular ? 'primary' : 'secondary'}
                size="sm"
                className="w-full text-xs md:text-sm"
                onClick={(e) => { e.stopPropagation(); setConfirm(service) }}
              >
                Выбрать
              </Button>
            </div>
          </motion.div>
        ))}
      </motion.div>

      {/* Confirm modal */}
      <AnimatePresence>
        {confirm && (
          <Modal open onClose={() => setConfirm(null)} title="Подтверждение">
            <div className="p-6 space-y-4">
              <div className="rounded-xl bg-surface-3 p-4 flex justify-between items-center">
                <span className="font-display text-base text-text">{confirm.name}</span>
                <span className="font-mono text-2xl text-jade tabular-nums font-bold">
                  {confirm.price.toLocaleString('ru-RU')} ₽
                </span>
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
