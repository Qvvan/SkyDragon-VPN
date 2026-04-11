import type { Service } from '../types/service.types'

const delay = (ms: number) => new Promise((r) => setTimeout(r, ms))

export const mockServices: Service[] = [
  {
    id: 'svc_001',
    name: 'Iron Wyrm Basic',
    description: 'Надёжная защита на месяц. Идеально для ежедневного использования.',
    price: 4.99,
    durationDays: 30,
    features: ['10 локаций', '100 ГБ трафика', '2 устройства', 'Стандартная поддержка'],
    popular: false,
  },
  {
    id: 'svc_003',
    name: 'Shadow Serpent',
    description: 'Стелс-протокол для ограниченных регионов. Обходит DPI.',
    price: 8.99,
    durationDays: 60,
    features: ['DPI обход', 'Маскировка трафика', 'Без логов', '5 устройств', 'Приоритетная маршрутизация'],
    popular: false,
  },
  {
    id: 'svc_002',
    name: 'Dragon Scale Pro',
    description: 'Максимальная скорость, безлимит, 50+ серверов на 6 континентах.',
    price: 12.99,
    durationDays: 90,
    features: ['50+ локаций', 'Безлимитный трафик', 'Kill switch', 'Split tunneling', '5 устройств'],
    popular: true,
  },
  {
    id: 'svc_004',
    name: 'Celestial Dragon',
    description: 'Корпоративный уровень. Выделенные IP, кастомные протоколы, поддержка 24/7.',
    price: 39.99,
    durationDays: 365,
    features: ['Выделенный IP', 'Кастомные протоколы', '100 устройств', 'Поддержка 24/7', 'SLA 99.9%'],
    popular: false,
  },
]

export const mockServicesApi = {
  async list(): Promise<Service[]> {
    await delay(500)
    return mockServices
  },

  async subscribe(_serviceId: string): Promise<{ subscriptionId: string }> {
    await delay(1000)
    return { subscriptionId: 'sub_new_' + Date.now() }
  },
}
