import client from './client'
import type { ChatMessage } from '../types/chat.types'

interface BackendChatMessage {
  id: string
  role: string
  text: string
  created_at: string
}

function mapMessage(m: BackendChatMessage): ChatMessage {
  return {
    id: m.id,
    role: m.role as ChatMessage['role'],
    text: m.text,
    createdAt: m.created_at,
  }
}

export const chatApi = {
  async list(): Promise<ChatMessage[]> {
    const res = await client.get<{ messages: BackendChatMessage[] }>('/me/chat/messages')
    return (res.data.messages ?? []).map(mapMessage)
  },

  async send(text: string): Promise<ChatMessage> {
    const res = await client.post<BackendChatMessage>('/me/chat/messages', { text })
    return mapMessage(res.data)
  },
}
