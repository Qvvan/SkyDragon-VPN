import type { Referral, ReferralStats } from '../types/referral.types'
import type { GiftCode } from '../types/gift.types'

const delay = (ms: number) => new Promise((r) => setTimeout(r, ms))

const mockReferrals: Referral[] = [
  { id: 'ref_001', maskedPhone: '+7 9** *** **42', joinedAt: '2026-02-10T00:00:00Z', bonusDaysGranted: 15 },
  { id: 'ref_002', maskedPhone: '+7 9** *** **17', joinedAt: '2026-03-02T00:00:00Z', bonusDaysGranted: 15 },
  { id: 'ref_003', maskedPhone: '+4 9** *** **88', joinedAt: '2026-03-18T00:00:00Z', bonusDaysGranted: 15 },
]

export const mockReferralsApi = {
  async getStats(): Promise<ReferralStats> {
    await delay(500)
    return {
      totalReferrals: 3,
      totalBonusDays: 45,
      referralLink: `${window.location.origin}/ref/DRAGON7`,
      referralCode: 'DRAGON7',
    }
  },

  async list(): Promise<Referral[]> {
    await delay(500)
    return mockReferrals
  },

  async createGift(serviceId: string, durationDays: number): Promise<GiftCode> {
    await delay(800)
    return {
      code: 'GIFT-' + Math.random().toString(36).substring(2, 10).toUpperCase(),
      serviceId,
      serviceName: 'Dragon Scale Pro',
      durationDays,
      createdAt: new Date().toISOString(),
    }
  },

  async activateGift(code: string): Promise<GiftCode> {
    await delay(700)
    return {
      code,
      serviceId: 'svc_001',
      serviceName: 'Dragon Scale Pro',
      durationDays: 90,
      createdAt: new Date().toISOString(),
    }
  },
}
