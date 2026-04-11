import client from './client'
import type { Subscription } from '../types/subscription.types'

interface BackendSubscription {
  subscription_id: number
  service_id: number | null
  service_name: string | null
  start_date: string | null
  end_date: string | null
  status: string | null
  auto_renewal: boolean
  service_duration_days: number | null
}

const STATUS_MAP: Record<string, Subscription['status']> = {
  'активная': 'active',
  'active': 'active',
  'trial': 'trial',
  'пробная': 'trial',
  'истекла': 'expired',
  'expired': 'expired',
  'pending': 'pending',
}

function mapSubscription(s: BackendSubscription): Subscription {
  const now = Date.now()
  const endMs = s.end_date ? new Date(s.end_date).getTime() : 0
  const totalDays = s.service_duration_days ?? 30
  const daysRemaining = endMs > now ? Math.ceil((endMs - now) / 86_400_000) : 0
  const statusKey = (s.status ?? '').toLowerCase()

  return {
    id: String(s.subscription_id),
    serviceId: String(s.service_id ?? ''),
    serviceName: s.service_name ?? 'Подписка',
    status: STATUS_MAP[statusKey] ?? (daysRemaining > 0 ? 'active' : 'expired'),
    expiresAt: s.end_date ?? new Date(0).toISOString(),
    createdAt: s.start_date ?? new Date(0).toISOString(),
    autoRenewal: s.auto_renewal,
    daysRemaining,
    totalDays,
  }
}

export const subscriptionsApi = {
  async list(): Promise<Subscription[]> {
    const res = await client.get<{ subscriptions: BackendSubscription[] }>('/me/subscriptions')
    return (res.data.subscriptions ?? []).map(mapSubscription)
  },

  async toggleAutoRenewal(id: string, enabled: boolean): Promise<Subscription> {
    await client.patch(`/me/subscriptions/${id}/auto-renewal`, { enabled })
    const list = await subscriptionsApi.list()
    const updated = list.find((s) => s.id === id)
    if (!updated) throw new Error('Subscription not found')
    return updated
  },

  async renew(id: string): Promise<Subscription> {
    const list = await subscriptionsApi.list()
    const sub = list.find((s) => s.id === id)
    if (!sub) throw new Error('Subscription not found')
    return sub
  },
}
