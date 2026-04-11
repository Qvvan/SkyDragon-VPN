import type { ChatMessage } from '../types/chat.types'

const delay = (ms: number) => new Promise((r) => setTimeout(r, ms))

const seedMessages: ChatMessage[] = [
  {
    id: 'msg_001',
    role: 'support',
    text: 'Welcome to SkyDragon Support! How can I help you today?',
    createdAt: new Date(Date.now() - 1000 * 60 * 10).toISOString(),
  },
  {
    id: 'msg_002',
    role: 'user',
    text: 'Hi, I need help connecting to the Shadow Serpent server.',
    createdAt: new Date(Date.now() - 1000 * 60 * 8).toISOString(),
  },
  {
    id: 'msg_003',
    role: 'support',
    text: 'Of course! Could you tell me which device and OS you\'re using? Also, which region were you trying to connect to?',
    createdAt: new Date(Date.now() - 1000 * 60 * 7).toISOString(),
  },
]

let messageStore: ChatMessage[] = [...seedMessages]

export const mockChatApi = {
  async list(): Promise<ChatMessage[]> {
    await delay(400)
    return [...messageStore]
  },

  async send(text: string): Promise<ChatMessage> {
    await delay(300)
    const msg: ChatMessage = {
      id: 'msg_' + Date.now(),
      role: 'user',
      text,
      createdAt: new Date().toISOString(),
    }
    messageStore.push(msg)

    // Simulate support reply after short delay
    setTimeout(() => {
      messageStore.push({
        id: 'msg_sup_' + Date.now(),
        role: 'support',
        text: 'Thanks for reaching out! Our team is reviewing your request and will respond shortly.',
        createdAt: new Date().toISOString(),
      })
    }, 2000)

    return msg
  },
}
