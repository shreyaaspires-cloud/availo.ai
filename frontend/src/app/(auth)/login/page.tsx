"use client"

import React, { useState } from "react"
import { useRouter } from "next/navigation"
import { api } from "@/lib/api"
import { useAuthStore } from "@/store/authStore"
import { Button } from "@/components/ui/Button"
import toast from "react-hot-toast"
import Link from "next/link"

export default function LoginPage() {
  const router = useRouter()
  const setUser = useAuthStore((s) => s.setUser)
  const [email, setEmail] = useState("demo_user@availo.app")
  const [password, setPassword] = useState("DemoUser@Availo")
  const [loading, setLoading] = useState(false)

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    try {
      const data: any = await api.post("/auth/login", { email, password })
      localStorage.setItem("availo_token", data.access_token)
      // Fetch me with explicit Authorization header so it cannot race
      const me: any = await api.get("/auth/me", undefined)
      setUser(me, data.access_token)
      toast.success(`Welcome back, ${me.full_name}!`)
      router.push("/resources")
    } catch (err: any) {
      toast.error(err.message || "Invalid credentials")
    } finally {
      setLoading(false)
    }
  }

  const setDemoRole = (roleEmail: string, pass: string) => {
    setEmail(roleEmail)
    setPassword(pass)
  }

  return (
    <div className="max-w-md mx-auto py-12">
      <div className="bg-white border border-gray-200 rounded-2xl p-8 shadow-sm space-y-6">
        <div className="text-center space-y-1">
          <h2 className="text-2xl font-bold text-gray-900">Sign in to Availo</h2>
          <p className="text-xs text-gray-500">Access equipment sharing, reservations & contracts</p>
        </div>

        {/* Demo Fast-Login Helpers */}
        <div className="bg-blue-50/60 border border-blue-100 rounded-xl p-3 space-y-2">
          <span className="text-[11px] font-bold text-blue-900 block">Quick Demo Roles:</span>
          <div className="grid grid-cols-3 gap-1.5 text-xs">
            <button
              type="button"
              onClick={() => setDemoRole("demo_user@availo.app", "DemoUser@Availo")}
              className="py-1 px-2 bg-white rounded border border-blue-200 font-medium hover:bg-blue-100 text-blue-800 text-[11px]"
            >
              Researcher
            </button>
            <button
              type="button"
              onClick={() => setDemoRole("demo_owner@availo.app", "DemoOwner@Availo")}
              className="py-1 px-2 bg-white rounded border border-blue-200 font-medium hover:bg-blue-100 text-blue-800 text-[11px]"
            >
              Owner
            </button>
            <button
              type="button"
              onClick={() => setDemoRole("demo_admin@availo.app", "DemoAdmin@Availo")}
              className="py-1 px-2 bg-white rounded border border-blue-200 font-medium hover:bg-blue-100 text-blue-800 text-[11px]"
            >
              Admin
            </button>
          </div>
        </div>

        <form onSubmit={handleLogin} className="space-y-4">
          <div>
            <label className="text-xs font-semibold text-gray-700 block mb-1">Email Address</label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full bg-white border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="text-xs font-semibold text-gray-700 block mb-1">Password</label>
            <input
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full bg-white border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <Button type="submit" loading={loading} className="w-full">
            Sign In
          </Button>
        </form>

        <div className="text-center text-xs text-gray-500">
          Need an account?{" "}
          <Link href="/register" className="text-blue-600 font-semibold hover:underline">
            Register here
          </Link>
        </div>
      </div>
    </div>
  )
}
