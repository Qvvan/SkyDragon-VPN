export type SubscriptionStatus = 'active' | 'expired' | 'trial' | 'pending'

export interface Subscription {
  id: string
  serviceId: string
  serviceName: string
  status: SubscriptionStatus
  expiresAt: string
  createdAt: string
  autoRenewal: boolean
  daysRemaining: number
  totalDays: number
  importUrl: string | null
}
