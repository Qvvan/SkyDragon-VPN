export type MessageRole = 'user' | 'support'

export interface ChatMessage {
  id: string
  role: MessageRole
  text: string
  createdAt: string
}

export interface SendMessageRequest {
  text: string
}
