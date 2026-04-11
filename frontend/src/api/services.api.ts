import client from './client'
import type { Service } from '../types/service.types'

interface BackendServicePlan {
  service_id: number
  name: string
  duration_days: number
  price: number
}

function mapService(s: BackendServicePlan): Service {
  return {
    id: String(s.service_id),
    name: s.name,
    description: `VPN на ${s.duration_days} дней`,
    price: s.price / 100,
    durationDays: s.duration_days,
    features: ['Безлимитный трафик', 'Все серверы', 'Поддержка 24/7'],
    popular: s.duration_days >= 90,
  }
}

export const servicesApi = {
  async list(): Promise<Service[]> {
    const res = await client.get<{ services: BackendServicePlan[] }>('/services')
    return (res.data.services ?? []).map(mapService)
  },

  async subscribe(serviceId: string): Promise<{ subscriptionId: string; paymentUrl?: string }> {
    const res = await client.post<{ payment_url: string }>('/me/subscriptions', {
      service_id: Number(serviceId),
    })
    if (res.data.payment_url) {
      window.location.href = res.data.payment_url
    }
    return { subscriptionId: serviceId }
  },
}
