import client from './client'
import type { Referral, ReferralStats } from '../types/referral.types'
import type { GiftCode } from '../types/gift.types'

interface BackendReferralStats {
  total_referrals: number
  total_bonus_days: number
  referral_code: string
  referral_link: string
}

interface BackendReferral {
  id: string
  masked_phone: string
  joined_at: string
  bonus_days_granted: number
}

interface BackendGiftCode {
  code: string
  service_id: string
  service_name: string
  duration_days: number
  created_at: string
}

export const referralsApi = {
  async getStats(): Promise<ReferralStats> {
    const res = await client.get<BackendReferralStats>('/me/referrals/stats')
    return {
      totalReferrals: res.data.total_referrals,
      totalBonusDays: res.data.total_bonus_days,
      referralCode: res.data.referral_code,
      referralLink: res.data.referral_link,
    }
  },

  async list(): Promise<Referral[]> {
    const res = await client.get<{ referrals: BackendReferral[] }>('/me/referrals')
    return (res.data.referrals ?? []).map((r) => ({
      id: r.id,
      maskedPhone: r.masked_phone,
      joinedAt: r.joined_at,
      bonusDaysGranted: r.bonus_days_granted,
    }))
  },

  async createGift(serviceId: string, durationDays: number): Promise<GiftCode> {
    const res = await client.post<BackendGiftCode>('/me/gifts', {
      service_id: serviceId,
      duration_days: durationDays,
    })
    return {
      code: res.data.code,
      serviceId: res.data.service_id,
      serviceName: res.data.service_name,
      durationDays: res.data.duration_days,
      createdAt: res.data.created_at,
    }
  },

  async activateGift(code: string): Promise<GiftCode> {
    const res = await client.post<BackendGiftCode>('/me/gifts/activate', { code })
    return {
      code: res.data.code,
      serviceId: res.data.service_id,
      serviceName: res.data.service_name,
      durationDays: res.data.duration_days,
      createdAt: res.data.created_at,
    }
  },
}
