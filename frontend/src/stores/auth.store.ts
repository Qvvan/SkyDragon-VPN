import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { User } from '../types/auth.types'

interface AuthStore {
  user: User | null
  token: string | null
  isAuthenticated: boolean
  setAuth: (token: string, user: User) => void
  clearAuth: () => void
  updateUser: (user: User) => void
}

export const useAuthStore = create<AuthStore>()(
  persist(
    (set) => ({
      user: null,
      token: null,
      isAuthenticated: false,
      setAuth: (token, user) => {
        localStorage.setItem('sdvpn_token', token)
        set({ token, user, isAuthenticated: true })
      },
      clearAuth: () => {
        localStorage.removeItem('sdvpn_token')
        set({ token: null, user: null, isAuthenticated: false })
      },
      updateUser: (user) => set({ user }),
    }),
    {
      name: 'sdvpn_auth',
      partialize: (state) => ({ token: state.token, user: state.user, isAuthenticated: state.isAuthenticated }),
    },
  ),
)

if (typeof window !== 'undefined') {
  window.addEventListener('sdvpn:logout', () => {
    useAuthStore.getState().clearAuth()
    window.location.href = '/login'
  })
}
