import client from './client'
import type { Payment, PaymentType } from '../types/payment.types'

interface BackendPayment {
  id: string
  payment_id: string
  service_id: number | null
  service_name: string | null
  payment_type: string
  status: string
  amount: number | string
  receipt_link: string | null
  confirmation_url: string | null
  created_at: string | null
}

const STATUS_MAP: Record<string, Payment['status']> = {
  succeeded: 'success',
  success:   'success',
  pending:   'pending',
  canceled:  'failed',
  failed:    'failed',
  refunded:  'failed',
}

const TYPE_MAP: Record<string, PaymentType> = {
  subscription: 'subscription',
  renewal:      'renewal',
  gift:         'gift',
}

function mapPayment(p: BackendPayment): Payment {
  return {
    id:             p.id,
    amount:         Number(p.amount),
    currency:       'RUB',
    status:         STATUS_MAP[p.status] ?? 'pending',
    paymentType:    TYPE_MAP[p.payment_type] ?? 'subscription',
    serviceName:    p.service_name ?? `Услуга #${p.service_id ?? '—'}`,
    createdAt:      p.created_at ?? new Date(0).toISOString(),
    confirmationUrl: p.confirmation_url ?? null,
  }
}

export const paymentsApi = {
  async list(): Promise<Payment[]> {
    const res = await client.get<{ payments: BackendPayment[] }>('/me/payments')
    return (res.data.payments ?? []).map(mapPayment)
  },
}
