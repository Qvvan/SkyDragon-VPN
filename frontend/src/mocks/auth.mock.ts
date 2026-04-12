import type { User, UpdateProfileRequest } from '../types/auth.types'

const delay = (ms: number) => new Promise((r) => setTimeout(r, ms))

export const mockUser: User = {
  id: '550e8400-e29b-41d4-a716-446655440000',
  login: 'dragonlord',
  firstName: 'Dragon',
  lastName: 'Lord',
  telegramUserId: null,
}

export const mockAuthApi = {
  async updateProfile(data: UpdateProfileRequest): Promise<User> {
    await delay(500)
    if (data.firstName !== undefined) mockUser.firstName = data.firstName
    if (data.lastName !== undefined) mockUser.lastName = data.lastName
    return { ...mockUser }
  },
}
