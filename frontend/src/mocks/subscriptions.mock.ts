import type { Subscription } from '../types/subscription.types'

const delay = (ms: number) => new Promise((r) => setTimeout(r, ms))

export const mockSubscriptions: Subscription[] = [
  {
    id: 'sub_001',
    serviceId: 'svc_001',
    serviceName: 'Dragon Scale Pro',
    status: 'active',
    expiresAt: '2026-05-01T00:00:00Z',
    createdAt: '2026-02-01T00:00:00Z',
    autoRenewal: true,
    daysRemaining: 31,
    totalDays: 90,
  },
  {
    id: 'sub_002',
    serviceId: 'svc_002',
    serviceName: 'Shadow Serpent',
    status: 'trial',
    expiresAt: '2026-04-05T00:00:00Z',
    createdAt: '2026-03-31T00:00:00Z',
    autoRenewal: false,
    daysRemaining: 5,
    totalDays: 5,
  },
  {
    id: 'sub_003',
    serviceId: 'svc_003',
    serviceName: 'Iron Wyrm Basic',
    status: 'expired',
    expiresAt: '2026-02-15T00:00:00Z',
    createdAt: '2026-01-15T00:00:00Z',
    autoRenewal: false,
    daysRemaining: 0,
    totalDays: 30,
  },
]

export const mockSubscriptionsApi = {
  async list(): Promise<Subscription[]> {
    await delay(600)
    return mockSubscriptions
  },

  async toggleAutoRenewal(id: string, enabled: boolean): Promise<Subscription> {
    await delay(400)
    const sub = mockSubscriptions.find((s) => s.id === id)!
    return { ...sub, autoRenewal: enabled }
  },

  async renew(id: string): Promise<Subscription> {
    await delay(800)
    const sub = mockSubscriptions.find((s) => s.id === id)!
    return { ...sub, status: 'active', daysRemaining: sub.totalDays }
  },
}
