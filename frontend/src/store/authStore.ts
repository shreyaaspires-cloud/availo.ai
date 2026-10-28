import { create } from "zustand"

export interface User {
  id: string
  email: string
  full_name: string
  roles: string[]
  trust_score: number
  is_active: boolean
}

interface AuthState {
  user: User | null
  token: string | null
  roles: string[]
  setUser: (user: User, token: string) => void
  clearUser: () => void
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  token: typeof window !== "undefined" ? localStorage.getItem("availo_token") : null,
  roles: typeof window !== "undefined" ? JSON.parse(localStorage.getItem("availo_roles") || "[]") : [],
  setUser: (user, token) => {
    if (typeof window !== "undefined") {
      localStorage.setItem("availo_token", token)
      localStorage.setItem("availo_roles", JSON.stringify(user.roles))
      localStorage.setItem("availo_user", JSON.stringify(user))
    }
    set({ user, token, roles: user.roles })
  },
  clearUser: () => {
    if (typeof window !== "undefined") {
      localStorage.removeItem("availo_token")
      localStorage.removeItem("availo_roles")
      localStorage.removeItem("availo_user")
    }
    set({ user: null, token: null, roles: [] })
  },
}))
