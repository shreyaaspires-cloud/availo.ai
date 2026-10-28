import { useAuthStore } from "@/store/authStore"

export function useAuth() {
  const { user, token, roles, setUser, clearUser } = useAuthStore()

  const isUser = roles.includes("USER")
  const isOwner = roles.includes("OWNER")
  const isAdmin = roles.includes("ADMIN")

  return {
    user,
    token,
    roles,
    isAuthenticated: !!token,
    isUser,
    isOwner,
    isAdmin,
    setUser,
    clearUser,
  }
}
