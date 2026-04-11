export type PaymentStatus = 'success' | 'pending' | 'failed'

export interface Payment {
  id: string
  amount: number
  currency: string
  status: PaymentStatus
  serviceName: string
  createdAt: string
  description: string
}
