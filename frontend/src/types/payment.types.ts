export type PaymentStatus = 'success' | 'pending' | 'failed'
export type PaymentType   = 'subscription' | 'renewal' | 'gift'

export interface Payment {
  id: string
  amount: number
  currency: string
  status: PaymentStatus
  paymentType: PaymentType
  serviceName: string
  createdAt: string
  confirmationUrl: string | null
}
