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
}

export const useAuthStore = create<AuthState>((set) => {
  const getInitialUser = (): User | null => {
    if (typeof window === "undefined") return null
    try {
      const stored = localStorage.getItem("availo_user")
      return stored ? JSON.parse(stored) : null
    } catch {
      return null
    }
  }

  const initialUser = getInitialUser()
  const initialRoles: string[] = initialUser?.roles || (typeof window !== "undefined" ? JSON.parse(localStorage.getItem("availo_roles") || "[]") : [])
  const defaultRole: ActiveRole = initialRoles.includes("ADMIN") ? "ADMIN" : initialRoles.includes("OWNER") ? "OWNER" : "USER"

  return {
    user: initialUser,
    token: typeof window !== "undefined" ? localStorage.getItem("availo_token") : null,
    roles: initialRoles,
    activeRole: defaultRole,
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
  }
})
