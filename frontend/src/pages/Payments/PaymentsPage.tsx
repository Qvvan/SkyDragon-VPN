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
  success: 'Оплачено',
  pending: 'Ожидает оплаты',
  failed:  'Ошибка',
}

const typeLabel: Record<Payment['paymentType'], string> = {
  subscription: 'Новая подписка',
  renewal:      'Продление',
  gift:         'Подарок',
}

const statusAccent: Record<Payment['status'], string> = {
  success: 'rgba(74,222,128,0.7)',
  pending: 'rgba(226,185,110,0.7)',
  failed:  'rgba(248,113,113,0.7)',
}

const rowVariants = {
  hidden:  { opacity: 0, y: 10 },
  visible: { opacity: 1, y: 0  },
}

function PaymentRow({ payment }: { payment: Payment }) {
  const isClickable = payment.status === 'pending' && !!payment.confirmationUrl
  const accent = statusAccent[payment.status]

  const inner = (
    <>
      {/* Left status bar */}
      <span
        className="absolute left-0 top-3 bottom-3 w-[2px] rounded-full transition-all duration-300"
        style={{ background: accent, opacity: isClickable ? undefined : 0.45 }}
      />

      {/* Service info */}
      <div className="min-w-0 pl-4">
        <p className="font-display text-base sm:text-lg text-text leading-tight truncate">
          {payment.serviceName}
        </p>
        <div className="flex items-center gap-2 mt-0.5 flex-wrap">
          <p className="font-mono text-[11px] text-text-dim tabular-nums">
            {new Date(payment.createdAt).toLocaleDateString('ru-RU', {
              day: 'numeric', month: 'long', year: 'numeric',
            })}
          </p>
          <span className="font-mono text-[11px] text-text-faint">·</span>
          <span className="font-mono text-[11px] text-text-faint">{typeLabel[payment.paymentType]}</span>
        </div>
      </div>

      {/* Amount */}
      <span className="font-mono text-sm sm:text-base text-text tabular-nums self-center shrink-0">
        {payment.amount > 0
          ? payment.amount.toLocaleString('ru-RU', { style: 'currency', currency: 'RUB', maximumFractionDigits: 0 })
          : '—'
        }
      </span>

      {/* Badge + arrow */}
      <div className="flex items-center gap-2 self-center shrink-0">
        <Badge variant={statusVariant(payment.status)}>
          {statusLabel[payment.status]}
        </Badge>
        {isClickable && (
          <span
            className="font-mono text-sm transition-transform duration-200 group-hover:translate-x-0.5"
            style={{ color: 'rgba(226,185,110,0.8)' }}
          >
            →
          </span>
        )}
      </div>
    </>
  )

  const baseClass = [
    'group relative flex items-center gap-4 px-4 py-4 sm:py-5',
    'rounded-xl border transition-all duration-200',
    'border-[rgba(157,140,255,0.07)]',
  ].join(' ')

  if (isClickable) {
    return (
      <a
        href={payment.confirmationUrl!}
        target="_blank"
        rel="noopener noreferrer"
        className={[
          baseClass,
          'cursor-pointer hover:border-[rgba(226,185,110,0.25)]',
          'hover:bg-[rgba(226,185,110,0.04)]',
          'hover:shadow-[0_0_0_1px_rgba(226,185,110,0.12),0_4px_24px_rgba(226,185,110,0.08)]',
        ].join(' ')}
      >
        {inner}
      </a>
    )
  }

  return (
    <div className={[baseClass, 'bg-transparent'].join(' ')}>
      {inner}
    </div>
  )
}

export function PaymentsContent() {
  const { data: payments, isLoading } = usePayments()

  if (isLoading) return (
    <div className="space-y-2">
      {[1, 2, 3, 4].map((i) => (
        <div
          key={i}
          className="flex items-center gap-4 px-4 py-4 rounded-xl border border-[rgba(157,140,255,0.07)]"
        >
          <div className="flex-1 space-y-2">
            <Skeleton className="h-4 w-36" />
            <Skeleton className="h-3 w-24" />
          </div>
          <Skeleton className="h-4 w-16 shrink-0" />
          <Skeleton className="h-5 w-28 rounded-full shrink-0" />
        </div>
      ))}
    </div>
  )

  if (!payments?.length) return (
    <div className="text-center py-20">
      <p className="font-mono text-sm text-text-faint">Платежей пока нет</p>
    </div>
  )

  return (
    <motion.div
      initial="hidden"
      animate="visible"
      variants={{ visible: { transition: { staggerChildren: 0.06 } } }}
      className="space-y-2"
    >
      {payments.map((payment) => (
        <motion.div key={payment.id} variants={rowVariants} transition={{ duration: 0.28, ease: 'easeOut' }}>
          <PaymentRow payment={payment} />
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
