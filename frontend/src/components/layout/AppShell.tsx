"use client"

import React, { useState, useEffect } from "react"
import Link from "next/link"
import { usePathname, useRouter } from "next/navigation"
import { useAuth } from "@/hooks/useAuth"
import { useWebSocket } from "@/hooks/useWebSocket"
import { useNotificationStore } from "@/store/notificationStore"
import { ActiveRole } from "@/store/authStore"
import {
  Compass,
  Calendar,
  Bell,
  UserCheck,
  LayoutDashboard,
  Box,
  Inbox,
  CalendarRange,
  AlertTriangle,
  ShieldAlert,
  History,
  Menu,
  X,
  LogOut,
  ChevronRight,
  Shield,
  Layers,
} from "lucide-react"

interface NavItem {
  label: string
  href: string
  icon: React.ElementType
}

const USER_NAV: NavItem[] = [
  { label: "Discover Resources", href: "/resources", icon: Compass },
  { label: "My Bookings", href: "/bookings", icon: Calendar },
  { label: "Notifications", href: "/notifications", icon: Bell },
  { label: "Profile & Verification", href: "/dashboard", icon: UserCheck },
]

const OWNER_NAV: NavItem[] = [
  { label: "Owner Dashboard", href: "/dashboard", icon: LayoutDashboard },
  { label: "My Resources", href: "/resources", icon: Box },
  { label: "Incoming Requests", href: "/bookings", icon: Inbox },
  { label: "Booking Calendar", href: "/bookings", icon: CalendarRange },
  { label: "Incidents & Returns", href: "/dashboard", icon: AlertTriangle },
]

const ADMIN_NAV: NavItem[] = [
  { label: "Admin Overview", href: "/admin", icon: LayoutDashboard },
  { label: "User Verification", href: "/admin", icon: UserCheck },
  { label: "Disputes & Incidents", href: "/admin", icon: ShieldAlert },
  { label: "Audit History", href: "/admin", icon: History },
]

export const AppShell: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const pathname = usePathname()
  const router = useRouter()
  const { user, roles, activeRole, setActiveRole, isAuthenticated, clearUser } = useAuth()
  const notifications = useNotificationStore((s) => s.notifications)
  const unreadCount = notifications.filter((n) => !n.is_read).length

  // Initialize real-time WebSocket connection for notifications
  useWebSocket()

  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const [mounted, setMounted] = useState(false)

  // Avoid SSR / client hydration mismatches by tracking mount state
  useEffect(() => {
    setMounted(true)
  }, [])

  // Close mobile menu on page transition
  useEffect(() => {
    setMobileMenuOpen(false)
  }, [pathname])

  const currentNav =
    activeRole === "ADMIN" ? ADMIN_NAV : activeRole === "OWNER" ? OWNER_NAV : USER_NAV

  const effectiveIsAuthenticated = mounted && isAuthenticated
  const effectiveActiveRole = mounted ? activeRole : "USER"
  const effectiveRoles = mounted ? roles : []
  const effectiveUser = mounted ? user : null

  const handleLogout = () => {
    clearUser()
    router.push("/login")
  }

  return (
    <div className="min-h-screen flex flex-col bg-slate-50 text-slate-900">
      {/* Top Header */}
      <header className="sticky top-0 z-40 bg-white/95 backdrop-blur-md border-b border-slate-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="lg:hidden p-2 rounded-lg text-slate-500 hover:text-slate-800 hover:bg-slate-100 transition"
              aria-label="Toggle navigation menu"
            >
              {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </button>

            <Link href="/" className="flex items-center gap-2.5">
              <span className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center text-white font-extrabold text-lg shadow-xs">
                A
              </span>
              <div className="flex flex-col">
                <span className="font-bold text-lg tracking-tight text-slate-900 leading-tight">
                  Availo
                </span>
                <span className="text-[10px] text-slate-400 font-medium tracking-wide uppercase">
                  Institutional Resource Network
                </span>
              </div>
            </Link>
          </div>

          {/* Center: Contextual Breadcrumb */}
          <div className="hidden md:flex items-center gap-1.5 text-xs text-slate-500">
            <span className="capitalize">{effectiveActiveRole.toLowerCase()}</span>
            <ChevronRight className="w-3.5 h-3.5 text-slate-300" />
            <span className="font-semibold text-slate-800">
              {pathname === "/"
                ? "Home"
                : pathname.startsWith("/resources")
                ? "Resource Catalog"
                : pathname.startsWith("/bookings")
                ? "Reservations"
                : pathname.startsWith("/admin")
                ? "Admin Portal"
                : pathname.startsWith("/dashboard")
                ? "Management Hub"
                : pathname.startsWith("/notifications")
                ? "Notifications"
                : "Portal"}
            </span>
          </div>

          {/* Right Header items */}
          <div className="flex items-center gap-3">
            {effectiveIsAuthenticated ? (
              <>
                {/* Role Switcher if user has multiple roles */}
                {effectiveRoles.length > 1 && (
                  <div className="hidden sm:flex items-center gap-1 bg-slate-100 p-1 rounded-lg text-xs font-semibold">
                    {effectiveRoles.includes("USER") && (
                      <button
                        onClick={() => setActiveRole("USER")}
                        className={`px-2 py-1 rounded-md transition ${
                          effectiveActiveRole === "USER"
                            ? "bg-white text-slate-900 shadow-xs"
                            : "text-slate-600 hover:text-slate-900"
                        }`}
                      >
                        User
                      </button>
                    )}
                    {effectiveRoles.includes("OWNER") && (
                      <button
                        onClick={() => setActiveRole("OWNER")}
                        className={`px-2 py-1 rounded-md transition ${
                          effectiveActiveRole === "OWNER"
                            ? "bg-white text-slate-900 shadow-xs"
                            : "text-slate-600 hover:text-slate-900"
                        }`}
                      >
                        Owner
                      </button>
                    )}
                    {effectiveRoles.includes("ADMIN") && (
                      <button
                        onClick={() => setActiveRole("ADMIN")}
                        className={`px-2 py-1 rounded-md transition ${
                          effectiveActiveRole === "ADMIN"
                            ? "bg-white text-purple-700 shadow-xs"
                            : "text-slate-600 hover:text-purple-700"
                        }`}
                      >
                        Admin
                      </button>
                    )}
                  </div>
                )}

                {/* Notifications Bell */}
                <Link
                  href="/notifications"
                  className="relative p-2 rounded-lg text-slate-500 hover:text-slate-800 hover:bg-slate-100 transition"
                  aria-label="Notifications"
                >
                  <Bell className="w-5 h-5" />
                  {unreadCount > 0 && (
                    <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-rose-500 animate-pulse" />
                  )}
                </Link>

                {/* User Pill & Sign Out */}
                <div className="flex items-center gap-2 pl-2 border-l border-slate-200">
                  <div className="hidden sm:flex flex-col text-right">
                    <span className="text-xs font-semibold text-slate-900 truncate max-w-[120px]">
                      {effectiveUser?.full_name || "User"}
                    </span>
                    <span className="text-[10px] text-slate-400 capitalize">
                      {effectiveActiveRole.toLowerCase()}
                    </span>
                  </div>
                  <button
                    onClick={handleLogout}
                    className="p-1.5 rounded-md text-slate-400 hover:text-rose-600 hover:bg-rose-50 transition"
                    title="Sign out"
                    aria-label="Sign out"
                  >
                    <LogOut className="w-4 h-4" />
                  </button>
                </div>
              </>
            ) : mounted ? (
              <div className="flex items-center gap-2">
                <Link
                  href="/login"
                  className="px-3 py-1.5 text-xs font-semibold text-slate-700 hover:text-slate-900 transition"
                >
                  Sign In
                </Link>
                <Link
                  href="/register"
                  className="px-3.5 py-1.5 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold rounded-lg shadow-xs transition"
                >
                  Register
                </Link>
              </div>
            ) : null}
          </div>
        </div>
      </header>

      {/* Main Body Layout with Sidebar for Authenticated Users */}
      <div className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6 flex gap-8">
        {/* Desktop Sidebar */}
        {effectiveIsAuthenticated && (
          <aside className="hidden lg:block w-64 shrink-0">
            <div className="sticky top-24 bg-white border border-slate-200 rounded-2xl p-4 shadow-xs space-y-6">
              {/* Role Indicator Banner */}
              <div className="px-3 py-2.5 rounded-xl bg-slate-50 border border-slate-200/60 flex items-center justify-between">
                <div>
                  <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block">
                    Active Workspace
                  </span>
                  <span className="text-xs font-bold text-slate-800">
                    {effectiveActiveRole} Mode
                  </span>
                </div>
                <span className="w-2 h-2 rounded-full bg-emerald-500" />
              </div>

              {/* Navigation Items */}
              <nav className="space-y-1">
                {currentNav.map((item) => {
                  const Icon = item.icon
                  const isActive =
                    pathname === item.href ||
                    (item.href !== "/" && pathname.startsWith(item.href) && item.href !== "/dashboard")

                  return (
                    <Link
                      key={item.label}
                      href={item.href}
                      className={`flex items-center gap-3 px-3 py-2.5 rounded-xl text-xs font-medium transition ${
                        isActive
                          ? "bg-blue-50 text-blue-700 font-semibold"
                          : "text-slate-600 hover:bg-slate-50 hover:text-slate-900"
                      }`}
                    >
                      <Icon className={`w-4 h-4 ${isActive ? "text-blue-600" : "text-slate-400"}`} />
                      <span>{item.label}</span>
                    </Link>
                  )
                })}
              </nav>

              {/* Trust Score & Verification Card */}
              <div className="pt-4 border-t border-slate-100 px-2 space-y-2">
                <div className="flex items-center justify-between text-[11px]">
                  <span className="text-slate-500">Platform Trust Score</span>
                  <span className="font-bold text-slate-900">{effectiveUser?.trust_score ?? 100} / 100</span>
                </div>
                <div className="w-full bg-slate-100 rounded-full h-1.5 overflow-hidden">
                  <div
                    className="bg-emerald-500 h-full rounded-full transition-all"
                    style={{ width: `${Math.min(100, effectiveUser?.trust_score ?? 100)}%` }}
                  />
                </div>
              </div>
            </div>
          </aside>
        )}

        {/* Mobile Navigation Drawer */}
        {mounted && mobileMenuOpen && (
          <div className="lg:hidden fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-xs flex">
            <div className="bg-white w-72 h-full p-6 shadow-xl flex flex-col justify-between">
              <div className="space-y-6">
                <div className="flex justify-between items-center pb-4 border-b border-slate-100">
                  <div className="flex items-center gap-2">
                    <span className="w-7 h-7 rounded-lg bg-blue-600 text-white flex items-center justify-center font-bold text-sm">
                      A
                    </span>
                    <span className="font-bold text-base text-slate-900">Availo</span>
                  </div>
                  <button
                    onClick={() => setMobileMenuOpen(false)}
                    className="p-1 rounded-md text-slate-400 hover:text-slate-700"
                  >
                    <X className="w-5 h-5" />
                  </button>
                </div>

                {effectiveRoles.length > 1 && (
                  <div className="space-y-1.5">
                    <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                      Switch Role Mode
                    </span>
                    <div className="grid grid-cols-3 gap-1 bg-slate-100 p-1 rounded-lg text-xs font-semibold">
                      {effectiveRoles.includes("USER") && (
                        <button
                          onClick={() => {
                            setActiveRole("USER")
                            setMobileMenuOpen(false)
                          }}
                          className={`py-1 rounded text-center ${
                            effectiveActiveRole === "USER" ? "bg-white shadow-xs" : "text-slate-600"
                          }`}
                        >
                          User
                        </button>
                      )}
                      {effectiveRoles.includes("OWNER") && (
                        <button
                          onClick={() => {
                            setActiveRole("OWNER")
                            setMobileMenuOpen(false)
                          }}
                          className={`py-1 rounded text-center ${
                            effectiveActiveRole === "OWNER" ? "bg-white shadow-xs" : "text-slate-600"
                          }`}
                        >
                          Owner
                        </button>
                      )}
                      {effectiveRoles.includes("ADMIN") && (
                        <button
                          onClick={() => {
                            setActiveRole("ADMIN")
                            setMobileMenuOpen(false)
                          }}
                          className={`py-1 rounded text-center ${
                            effectiveActiveRole === "ADMIN" ? "bg-white shadow-xs" : "text-slate-600"
                          }`}
                        >
                          Admin
                        </button>
                      )}
                    </div>
                  </div>
                )}

                <nav className="space-y-1">
                  {currentNav.map((item) => {
                    const Icon = item.icon
                    const isActive = pathname === item.href
                    return (
                      <Link
                        key={item.label}
                        href={item.href}
                        onClick={() => setMobileMenuOpen(false)}
                        className={`flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium ${
                          isActive
                            ? "bg-blue-50 text-blue-700 font-semibold"
                            : "text-slate-700 hover:bg-slate-50"
                        }`}
                      >
                        <Icon className="w-4 h-4 text-slate-500" />
                        <span>{item.label}</span>
                      </Link>
                    )
                  })}
                </nav>
              </div>

              {effectiveIsAuthenticated && (
                <div className="pt-4 border-t border-slate-100">
                  <button
                    onClick={handleLogout}
                    className="w-full flex items-center justify-center gap-2 py-2 text-xs font-semibold text-rose-600 hover:bg-rose-50 rounded-lg transition"
                  >
                    <LogOut className="w-4 h-4" />
                    Sign Out
                  </button>
                </div>
              )}
            </div>
            <div className="flex-1" onClick={() => setMobileMenuOpen(false)} />
          </div>
        )}

        {/* Main Content Area */}
        <main className="flex-1 min-w-0">{children}</main>
      </div>

      {/* Footer */}
      <footer className="border-t border-slate-200 bg-white py-6 mt-auto">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center text-xs text-slate-400">
          Availo &copy; 2026 — Institutional Resource Sharing with Cryptographic Agreements & Visual AI Inspection
        </div>
      </footer>
    </div>
  )
}
