import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { referralsApi } from '../api/referrals.api'

export function useReferralStats() {
  return useQuery({
    queryKey: ['referrals', 'stats'],
    queryFn: referralsApi.getStats,
    staleTime: 30_000,
    refetchOnWindowFocus: false,
  })
}

export function useReferralList() {
  return useQuery({
    queryKey: ['referrals', 'list'],
    queryFn: referralsApi.list,
    staleTime: 30_000,
    refetchOnWindowFocus: false,
  })
}

export function useCreateGift() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ serviceId, durationDays }: { serviceId: string; durationDays: number }) =>
      referralsApi.createGift(serviceId, durationDays),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['referrals'] }),
  })
}

export function useActivateGift() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ code }: { code: string }) => referralsApi.activateGift(code),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['subscriptions'] })
      queryClient.invalidateQueries({ queryKey: ['referrals'] })
    },
  })
}
