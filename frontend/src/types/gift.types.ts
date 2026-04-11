export interface GiftCode {
  code: string
  serviceId: string
  serviceName: string
  durationDays: number
  createdAt: string
}

export interface CreateGiftRequest {
  serviceId: string
  durationDays: number
}
