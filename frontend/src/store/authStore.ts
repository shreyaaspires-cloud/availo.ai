import { create } from "zustand"

export type ActiveRole = "USER" | "OWNER" | "ADMIN"

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
  activeRole: ActiveRole
  setUser: (user: User, token: string) => void
  setActiveRole: (role: ActiveRole) => void
  clearUser: () => void
  initialize: () => void
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  token: null,
  roles: [],
  activeRole: "USER",
  initialize: () => {
    if (typeof window === "undefined") return
    try {
      const storedUser = localStorage.getItem("availo_user")
      const storedToken = localStorage.getItem("availo_token")
      const storedRoles = localStorage.getItem("availo_roles")
      const user: User | null = storedUser ? JSON.parse(storedUser) : null
      const token = storedToken || null
      const roles: string[] = user?.roles || (storedRoles ? JSON.parse(storedRoles) : [])
      const defaultRole: ActiveRole = roles.includes("ADMIN")
        ? "ADMIN"
        : roles.includes("OWNER")
        ? "OWNER"
        : "USER"
      set({ user, token, roles, activeRole: defaultRole })
    } catch {
      // ignore JSON parse errors
    }
  },
  setUser: (user, token) => {
    if (typeof window !== "undefined") {
      localStorage.setItem("availo_token", token)
      localStorage.setItem("availo_roles", JSON.stringify(user.roles))
      localStorage.setItem("availo_user", JSON.stringify(user))
    }
    const primaryRole: ActiveRole = user.roles.includes("ADMIN")
      ? "ADMIN"
      : user.roles.includes("OWNER")
      ? "OWNER"
      : "USER"
    set({ user, token, roles: user.roles, activeRole: primaryRole })
  },
  setActiveRole: (role) => set({ activeRole: role }),
  clearUser: () => {
    if (typeof window !== "undefined") {
      localStorage.removeItem("availo_token")
      localStorage.removeItem("availo_roles")
      localStorage.removeItem("availo_user")
    }
    set({ user: null, token: null, roles: [], activeRole: "USER" })
  },
}))
