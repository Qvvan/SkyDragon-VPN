import { motion } from 'framer-motion'
import { Badge } from '../../components/ui/Badge'
import { Skeleton } from '../../components/ui/Skeleton'
import { usePayments } from '../../hooks/usePayments'
import type { Payment } from '../../types/payment.types'

function statusVariant(status: Payment['status']): 'jade' | 'amber' | 'ember' {
  if (status === 'success') return 'jade'
  if (status === 'pending') return 'amber'
  return 'ember'
}

const statusLabel: Record<Payment['status'], string> = {
  success: 'Успешно',
  pending: 'В обработке',
  failed:  'Ошибка',
}

export function PaymentsContent() {
  const { data: payments, isLoading } = usePayments()

  if (isLoading) return (
    <div className="space-y-3">
      {[1, 2, 3, 4].map((i) => (
        <div key={i} className="flex items-center justify-between gap-4 py-3">
          <div className="space-y-2">
            <Skeleton className="h-4 w-32" />
            <Skeleton className="h-3 w-24" />
          </div>
          <div className="flex items-center gap-3">
            <Skeleton className="h-4 w-16" />
            <Skeleton className="h-5 w-20 rounded-full" />
          </div>
        </div>
      ))}
    </div>
  )

  if (!payments?.length) return (
    <div className="text-center py-16">
      <p className="font-mono text-base text-text-dim">Платежей пока нет</p>
    </div>
  )

  return (
    <motion.div
      initial="hidden"
      animate="visible"
      variants={{ visible: { transition: { staggerChildren: 0.05 } } }}
    >
      <div className="grid grid-cols-[1fr_auto_auto] gap-4 pb-3 mb-2 border-b border-[rgba(157,140,255,0.08)]">
        <span className="font-mono text-xs text-text-faint uppercase tracking-wider">Услуга</span>
        <span className="font-mono text-xs text-text-faint uppercase tracking-wider text-right">Сумма</span>
        <span className="font-mono text-xs text-text-faint uppercase tracking-wider">Статус</span>
      </div>

      {payments.map((payment) => (
        <motion.div
          key={payment.id}
          variants={{ hidden: { opacity: 0, x: -8 }, visible: { opacity: 1, x: 0 } }}
          transition={{ duration: 0.3, ease: 'easeOut' }}
          className="grid grid-cols-[1fr_auto_auto] gap-4 py-4 sm:py-5 border-b border-[rgba(157,140,255,0.06)] last:border-0 rounded-xl hover:bg-surface-3 -mx-2 px-2 transition-[background-color] duration-150"
        >
          <div className="min-w-0">
            <p className="font-mono text-sm sm:text-base text-text truncate">{payment.serviceName}</p>
            <p className="font-mono text-xs sm:text-sm text-text-dim mt-1 tabular-nums">
              {new Date(payment.createdAt).toLocaleDateString('ru-RU', {
                day: 'numeric', month: 'short', year: 'numeric',
              })}
            </p>
          </div>
          <span className="font-mono text-sm sm:text-base text-text tabular-nums self-center">
            ${payment.amount.toFixed(2)}
          </span>
          <div className="self-center">
            <Badge variant={statusVariant(payment.status)}>
              {statusLabel[payment.status]}
            </Badge>
          </div>
        </motion.div>
      ))}
    </motion.div>
  )
}

export function PaymentsPage() {
  return (
    <div className="px-4 md:px-8 py-8 max-w-3xl mx-auto">
      <PaymentsContent />
    </div>
  )
}
