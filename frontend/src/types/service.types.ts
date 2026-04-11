export interface Service {
  id: string
  name: string
  description: string
  price: number
  durationDays: number
  features: string[]
  popular: boolean
}

export interface CreateSubscriptionRequest {
  serviceId: string
}
