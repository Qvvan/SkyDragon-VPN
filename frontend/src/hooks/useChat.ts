import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { chatApi } from '../api/chat.api'

export function useChatMessages() {
  return useQuery({
    queryKey: ['chat'],
    queryFn: chatApi.list,
    refetchInterval: 5000, // Poll every 5s
    staleTime: 0,
    refetchOnWindowFocus: true,
  })
}

export function useSendMessage() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (text: string) => chatApi.send(text),
    onSettled: () => queryClient.invalidateQueries({ queryKey: ['chat'] }),
  })
}
