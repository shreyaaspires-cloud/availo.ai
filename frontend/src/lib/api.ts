import { useAuthStore } from "@/store/authStore"

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1"

interface RequestOptions extends RequestInit {
  params?: Record<string, string | number | boolean | undefined>
}

async function request<T>(endpoint: string, options: RequestOptions = {}): Promise<T> {
  const { params, headers, ...rest } = options
  const token =
    useAuthStore.getState().token ||
    (typeof window !== "undefined" ? localStorage.getItem("availo_token") : null)

  let url = `${BASE_URL}${endpoint}`
  if (params) {
    const searchParams = new URLSearchParams()
    Object.entries(params).forEach(([key, val]) => {
      if (val !== undefined && val !== null && val !== "") {
        searchParams.append(key, String(val))
      }
    })
    const query = searchParams.toString()
    if (query) {
      url += `?${query}`
    }
  }

  const reqHeaders: Record<string, string> = {
    "Content-Type": "application/json",
    ...(headers as Record<string, string>),
  }

  if (token) {
    reqHeaders["Authorization"] = `Bearer ${token}`
  }

  const response = await fetch(url, {
    ...rest,
    headers: reqHeaders,
  })

  // Token expired / unauthorized handling
  if (response.status === 401) {
    try {
      const refreshRes = await fetch(`${BASE_URL}/auth/refresh`, {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
      })
      if (refreshRes.ok) {
        const data = await refreshRes.json()
        const user = useAuthStore.getState().user
        if (user && data.access_token) {
          useAuthStore.getState().setUser(user, data.access_token)
          reqHeaders["Authorization"] = `Bearer ${data.access_token}`
          const retryRes = await fetch(url, { ...rest, headers: reqHeaders })
          if (!retryRes.ok) {
            const err = await retryRes.json().catch(() => ({ detail: "Request failed" }))
            throw new Error(err.detail || "Request failed")
          }
          return retryRes.json()
        }
      }
    } catch {
      useAuthStore.getState().clearUser()
      if (typeof window !== "undefined") {
        window.location.href = "/login"
      }
    }
  }

  if (!response.ok) {
    let errorMsg = `Request failed (${response.status})`
    try {
      const err = await response.json()
      if (err.detail) {
        errorMsg = typeof err.detail === "string" ? err.detail : JSON.stringify(err.detail)
      } else if (err.error) {
        errorMsg = err.error
      }
    } catch {
      const text = await response.text().catch(() => "")
      if (text) errorMsg = text
    }
    throw new Error(errorMsg)
  }

  return response.json()
}

export const api = {
  get: <T>(endpoint: string, params?: Record<string, any>) =>
    request<T>(endpoint, { method: "GET", params }),
  post: <T>(endpoint: string, body?: any) =>
    request<T>(endpoint, {
      method: "POST",
      body: body instanceof FormData ? body : JSON.stringify(body),
      headers: body instanceof FormData ? {} : undefined,
    }),
  patch: <T>(endpoint: string, body?: any) =>
    request<T>(endpoint, {
      method: "PATCH",
      body: body instanceof FormData ? body : JSON.stringify(body),
      headers: body instanceof FormData ? {} : undefined,
    }),
  del: <T>(endpoint: string) => request<T>(endpoint, { method: "DELETE" }),
}
