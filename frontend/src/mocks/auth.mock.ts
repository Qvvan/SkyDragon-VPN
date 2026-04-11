import type { User, UpdateProfileRequest } from '../types/auth.types'

const delay = (ms: number) => new Promise((r) => setTimeout(r, ms))

export const mockUser: User = {
  id: 1,
  email: 'test@example.com',
  phone: null,
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
