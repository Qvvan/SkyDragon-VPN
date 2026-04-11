import { useQuery } from '@tanstack/react-query'
import { paymentsApi } from '../api/payments.api'

export function usePayments() {
  return useQuery({
    queryKey: ['payments'],
    queryFn: paymentsApi.list,
    staleTime: 30_000,
    refetchOnWindowFocus: false,
  })
}
