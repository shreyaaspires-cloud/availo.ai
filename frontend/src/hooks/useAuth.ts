import { useEffect } from "react"
import { useAuthStore, ActiveRole } from "@/store/authStore"

export function useAuth() {
  const { user, token, roles, activeRole, setUser, setActiveRole, clearUser, initialize } =
    useAuthStore()

  useEffect(() => {
    initialize()
  }, [initialize])

  const isUser = roles.includes("USER")
  const isOwner = roles.includes("OWNER")
  const isAdmin = roles.includes("ADMIN")

  return {
    user,
    token,
    roles,
    activeRole,
    isAuthenticated: !!token,
    isUser,
    isOwner,
    isAdmin,
    setUser,
    setActiveRole,
    clearUser,
  }
}
