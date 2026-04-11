import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { subscriptionsApi } from '../api/subscriptions.api'

export function useSubscriptions() {
  return useQuery({
    queryKey: ['subscriptions'],
    queryFn: subscriptionsApi.list,
    staleTime: 30_000,
    refetchOnWindowFocus: false,
  })
}

export function useToggleAutoRenewal() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, enabled }: { id: string; enabled: boolean }) =>
      subscriptionsApi.toggleAutoRenewal(id, enabled),
    onMutate: async ({ id, enabled }) => {
      await queryClient.cancelQueries({ queryKey: ['subscriptions'] })
      const prev = queryClient.getQueryData(['subscriptions'])
      queryClient.setQueryData(['subscriptions'], (old: ReturnType<typeof subscriptionsApi.list> extends Promise<infer T> ? T : never) =>
        old?.map((s) => (s.id === id ? { ...s, autoRenewal: enabled } : s)),
      )
      return { prev }
    },
    onError: (_err, _vars, ctx) => {
      if (ctx?.prev) queryClient.setQueryData(['subscriptions'], ctx.prev)
    },
    onSettled: () => queryClient.invalidateQueries({ queryKey: ['subscriptions'] }),
  })
}

export function useRenewSubscription() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => subscriptionsApi.renew(id),
    onSettled: () => queryClient.invalidateQueries({ queryKey: ['subscriptions'] }),
  })
}
