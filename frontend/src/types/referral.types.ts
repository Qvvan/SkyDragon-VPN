export interface Referral {
  id: string
  maskedPhone: string
  joinedAt: string
  bonusDaysGranted: number
}

export interface ReferralStats {
  totalReferrals: number
  totalBonusDays: number
  referralLink: string
  referralCode: string
}
