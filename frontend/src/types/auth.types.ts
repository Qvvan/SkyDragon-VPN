export interface User {
  id: number
  email: string | null
  phone: string | null
  firstName: string
  lastName: string
  telegramUserId: number | null
}

export interface UpdateProfileRequest {
  firstName?: string
  lastName?: string
}

export interface AuthState {
  user: User | null
  token: string | null
  isAuthenticated: boolean
}

export interface LoginRequest {
  login: string
  password: string
}

export interface LoginResponse {
  access_token: string
  token_type: string
}

export interface RegisterRequest {
  email?: string
  phone?: string
  password: string
  first_name: string
  last_name: string
}
