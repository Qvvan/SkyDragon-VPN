import client from './client'
import type { LoginRequest, LoginResponse, RegisterRequest, UpdateProfileRequest, User } from '../types/auth.types'

function mapUser(data: Record<string, unknown>): User {
  return {
    id: String(data['id']),
    login: (data['login'] as string) ?? '',
    firstName: (data['first_name'] as string) ?? '',
    lastName: (data['last_name'] as string) ?? '',
    telegramUserId: (data['telegram_user_id'] as number | null) ?? null,
  }
}

export const authApi = {
  async login(data: LoginRequest): Promise<{ token: string; user: User }> {
    const res = await client.post<LoginResponse>('/auth/login', data)
    const token = res.data.access_token
    const meRes = await client.get<Record<string, unknown>>('/me', {
      headers: { Authorization: `Bearer ${token}` },
    })
    return { token, user: mapUser(meRes.data) }
  },

  async register(data: RegisterRequest): Promise<{ token: string; user: User }> {
    const res = await client.post<LoginResponse>('/auth/register', data)
    const token = res.data.access_token
    const meRes = await client.get<Record<string, unknown>>('/me', {
      headers: { Authorization: `Bearer ${token}` },
    })
    return { token, user: mapUser(meRes.data) }
  },

  async getMe(): Promise<User> {
    const res = await client.get<Record<string, unknown>>('/me')
    return mapUser(res.data)
  },

  async updateProfile(data: UpdateProfileRequest): Promise<User> {
    const payload: Record<string, string | undefined> = {}
    if (data.firstName !== undefined) payload['first_name'] = data.firstName
    if (data.lastName !== undefined) payload['last_name'] = data.lastName
    const res = await client.patch<Record<string, unknown>>('/me', payload)
    return mapUser(res.data)
  },

  async getTelegramLinkToken(): Promise<string> {
    const res = await client.post<{ token: string }>('/me/telegram/link-token')
    return res.data.token
  },
}
