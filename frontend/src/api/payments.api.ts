import client from './client'
import type { Payment } from '../types/payment.types'

interface BackendPayment {
  id: number
  payment_id: string
  service_id: number | null
  status: string
  payment_type: string | null
  created_at: string | null
}

const STATUS_MAP: Record<string, Payment['status']> = {
  succeeded: 'success',
  success: 'success',
  pending: 'pending',
  canceled: 'failed',
  failed: 'failed',
}

function mapPayment(p: BackendPayment): Payment {
  return {
    id: String(p.id),
    amount: 0,
    currency: 'RUB',
    status: STATUS_MAP[p.status] ?? 'pending',
    serviceName: `Услуга #${p.service_id ?? '—'}`,
    createdAt: p.created_at ?? new Date(0).toISOString(),
    description: p.payment_type ?? '',
  }
}

export const paymentsApi = {
  async list(): Promise<Payment[]> {
    const res = await client.get<{ payments: BackendPayment[] }>('/me/payments')
    return (res.data.payments ?? []).map(mapPayment)
  },
}
