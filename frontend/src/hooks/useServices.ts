import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { servicesApi } from '../api/services.api'

export function useServices() {
  return useQuery({
    queryKey: ['services'],
    queryFn: servicesApi.list,
    staleTime: 30_000,
    refetchOnWindowFocus: false,
  })
}

export function useSubscribeService() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ serviceId }: { serviceId: string }) =>
      servicesApi.subscribe(serviceId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['subscriptions'] }),
  })
}
