import type { Payment } from '../types/payment.types'

const delay = (ms: number) => new Promise((r) => setTimeout(r, ms))

export const mockPayments: Payment[] = [
  {
    id: 'pay_001',
    amount: 9.99,
    currency: 'USD',
    status: 'success',
    serviceName: 'Dragon Scale Pro',
    createdAt: '2026-03-01T14:30:00Z',
    description: 'Monthly subscription renewal',
  },
  {
    id: 'pay_002',
    amount: 14.99,
    currency: 'USD',
    status: 'success',
    serviceName: 'Shadow Serpent',
    createdAt: '2026-02-15T09:12:00Z',
    description: '1 month subscription',
  },
  {
    id: 'pay_003',
    amount: 29.97,
    currency: 'USD',
    status: 'pending',
    serviceName: 'Dragon Scale Pro',
    createdAt: '2026-03-28T18:45:00Z',
    description: '3 month subscription',
  },
  {
    id: 'pay_004',
    amount: 4.99,
    currency: 'USD',
    status: 'failed',
    serviceName: 'Iron Wyrm Basic',
    createdAt: '2026-01-20T11:00:00Z',
    description: 'Monthly subscription',
  },
  {
    id: 'pay_005',
    amount: 9.99,
    currency: 'USD',
    status: 'success',
    serviceName: 'Dragon Scale Pro',
    createdAt: '2026-02-01T14:30:00Z',
    description: 'Monthly subscription renewal',
  },
]

export const mockPaymentsApi = {
  async list(): Promise<Payment[]> {
    await delay(600)
    return mockPayments
  },
}
