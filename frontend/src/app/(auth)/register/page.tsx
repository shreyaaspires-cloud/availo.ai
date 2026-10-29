"use client"

import React, { useState } from "react"
import { useRouter } from "next/navigation"
import { api } from "@/lib/api"
import { Button } from "@/components/ui/Button"
import toast from "react-hot-toast"
import Link from "next/link"

export default function RegisterPage() {
  const router = useRouter()
  const [email, setEmail] = useState("")
  const [fullName, setFullName] = useState("")
  const [password, setPassword] = useState("")
  const [loading, setLoading] = useState(false)

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    try {
      await api.post("/auth/register", { email, full_name: fullName, password })
      toast.success("Account created successfully! Please sign in.")
      router.push("/login")
    } catch (err: any) {
      toast.error(err.message || "Registration failed")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-md mx-auto py-12">
      <div className="bg-white border border-gray-200 rounded-2xl p-8 shadow-sm space-y-6">
        <div className="text-center space-y-1">
          <h2 className="text-2xl font-bold text-gray-900">Create an Account</h2>
          <p className="text-xs text-gray-500">Join the verified institutional resource pool</p>
        </div>

        <form onSubmit={handleRegister} className="space-y-4">
          <div>
            <label className="text-xs font-semibold text-gray-700 block mb-1">Full Name</label>
            <input
              type="text"
              required
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              className="w-full bg-white border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

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
              minLength={6}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full bg-white border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <Button type="submit" loading={loading} className="w-full">
            Register
          </Button>
        </form>

        <div className="text-center text-xs text-gray-500">
          Already have an account?{" "}
          <Link href="/login" className="text-blue-600 font-semibold hover:underline">
            Sign in
          </Link>
        </div>
      </div>
    </div>
  )
}
