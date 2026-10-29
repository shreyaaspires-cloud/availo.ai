"use client"

import React from "react"
import { useAuth } from "@/hooks/useAuth"
import { useBookings } from "@/hooks/useBooking"
import { useResources } from "@/hooks/useResource"
import { StateBadge } from "@/components/booking/StateBadge"
import { Button } from "@/components/ui/Button"
import { EmptyState } from "@/components/ui/EmptyState"
import { formatCurrency, formatDate } from "@/lib/utils"
import Link from "next/link"
import {
  ShieldCheck,
  Plus,
  Compass,
  ArrowRight,
  User,
  Clock,
  CheckCircle,
  AlertTriangle,
  Box,
} from "lucide-react"

export default function DashboardPage() {
  const [mounted, setMounted] = React.useState(false)
  React.useEffect(() => {
    setMounted(true)
  }, [])

  const { user, isOwner, isAdmin, activeRole, setActiveRole } = useAuth()
  const { data: bookings = [], isLoading: bookingsLoading } = useBookings()
  const { data: resources = [], isLoading: resourcesLoading } = useResources()

  // Strict ownership matching: resources owned by current user
  const myOwnedResources = resources.filter((r) => r.owner_id === user?.id)

  // Bookings made by current user
  const myBorrowedBookings = bookings.filter((b) => b.user_id === user?.id)

  // Incoming bookings for equipment owned by user (Owner view)
  const incomingOwnerRequests = bookings.filter((b) =>
    myOwnedResources.some((r) => r.id === b.resource_id)
  )

  const activeInUseBookings = myBorrowedBookings.filter((b) => b.status === "CHECKED_IN")
  const pendingRequests = myBorrowedBookings.filter((b) => b.status === "PENDING_APPROVAL")
  const returnsNeedingAction = myBorrowedBookings.filter((b) =>
    ["CHECKED_IN", "DAMAGE_REVIEW"].includes(b.status)
  )

  const ownerPendingApprovals = incomingOwnerRequests.filter(
    (b) => b.status === "PENDING_APPROVAL"
  )
  const ownerActiveHandovers = incomingOwnerRequests.filter((b) =>
    ["CONFIRMED", "CHECKED_IN"].includes(b.status)
  )

  return (
    <div className="space-y-8">
      {/* Profile & Trust Score Header */}
      <div className="bg-white border border-slate-200/90 rounded-2xl p-6 shadow-xs flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div className="flex items-center gap-3.5">
          <div className="w-12 h-12 rounded-xl bg-blue-50 border border-blue-200 text-blue-700 flex items-center justify-center font-bold text-lg">
            {user?.full_name?.charAt(0) || "U"}
          </div>
          <div>
            <h1 className="text-xl font-bold text-slate-900">
              {user?.full_name || "Availo Member"}
            </h1>
            <p className="text-xs text-slate-500">{user?.email}</p>
          </div>
        </div>

        <div className="flex items-center gap-2 flex-wrap">
          <span className="bg-emerald-50 text-emerald-800 border border-emerald-200 text-xs px-3 py-1 rounded-full font-semibold flex items-center gap-1.5 shadow-xs">
            <ShieldCheck className="w-4 h-4 text-emerald-600" />
            Trust Score: {user?.trust_score ?? 100} / 100
          </span>
          {user?.roles?.map((role) => (
            <span
              key={role}
              className="bg-slate-100 text-slate-700 border border-slate-200 text-xs px-2.5 py-1 rounded-full font-semibold"
            >
              {role}
            </span>
          ))}
        </div>
      </div>

      {/* Role Navigation View Switcher (for users with multiple roles) */}
      {user?.roles && user.roles.length > 1 && (
        <div className="flex items-center gap-2 bg-slate-100/80 p-1.5 rounded-xl text-xs font-semibold w-fit">
          <span className="text-slate-400 px-2 uppercase text-[10px] tracking-wider">
            Viewing Mode:
          </span>
          {user.roles.includes("USER") && (
            <button
              onClick={() => setActiveRole("USER")}
              className={`px-3 py-1.5 rounded-lg transition ${
                activeRole === "USER"
                  ? "bg-white text-slate-900 shadow-xs"
                  : "text-slate-600 hover:text-slate-900"
              }`}
            >
              Borrower Dashboard
            </button>
          )}
          {user.roles.includes("OWNER") && (
            <button
              onClick={() => setActiveRole("OWNER")}
              className={`px-3 py-1.5 rounded-lg transition ${
                activeRole === "OWNER"
                  ? "bg-white text-slate-900 shadow-xs"
                  : "text-slate-600 hover:text-slate-900"
              }`}
            >
              Equipment Owner Dashboard
            </button>
          )}
          {user.roles.includes("ADMIN") && (
            <Link
              href="/admin"
              className="px-3 py-1.5 rounded-lg text-purple-700 hover:bg-white transition"
            >
              Admin Portal →
            </Link>
          )}
        </div>
      )}

      {/* USER / BORROWER DASHBOARD VIEW */}
      {mounted && activeRole === "USER" && (
        <div className="space-y-6">
          {/* Metrics */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-white border border-slate-200/90 rounded-2xl p-5 shadow-xs">
              <span className="text-xs text-slate-500 font-medium block">Resources In Use</span>
              <span className="text-2xl font-black text-blue-600 mt-1 block">
                {activeInUseBookings.length}
              </span>
            </div>
            <div className="bg-white border border-slate-200/90 rounded-2xl p-5 shadow-xs">
              <span className="text-xs text-slate-500 font-medium block">Pending Requests</span>
              <span className="text-2xl font-black text-amber-600 mt-1 block">
                {pendingRequests.length}
              </span>
            </div>
            <div className="bg-white border border-slate-200/90 rounded-2xl p-5 shadow-xs">
              <span className="text-xs text-slate-500 font-medium block">Returns Due</span>
              <span className="text-2xl font-black text-slate-900 mt-1 block">
                {returnsNeedingAction.length}
              </span>
            </div>
            <div className="bg-white border border-slate-200/90 rounded-2xl p-5 shadow-xs">
              <span className="text-xs text-slate-500 font-medium block">Total Reservations</span>
              <span className="text-2xl font-black text-slate-900 mt-1 block">
                {myBorrowedBookings.length}
              </span>
            </div>
          </div>

          {/* Quick Actions & Recent Activity */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
            <div className="lg:col-span-8 bg-white border border-slate-200/90 rounded-2xl p-6 shadow-xs space-y-4">
              <div className="flex justify-between items-center pb-2 border-b border-slate-100">
                <h3 className="font-bold text-slate-900 text-sm">Recent Reservations</h3>
                <Link
                  href="/bookings"
                  className="text-xs text-blue-600 font-semibold hover:underline"
                >
                  View All ({myBorrowedBookings.length})
                </Link>
              </div>

              {myBorrowedBookings.length === 0 ? (
                <EmptyState
                  icon={Clock}
                  title="No active reservations"
                  description="Explore accredited institutional labs to reserve precision instruments."
                  action={
                    <Link
                      href="/resources"
                      className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold rounded-xl inline-flex items-center gap-1.5 transition"
                    >
                      <Compass className="w-4 h-4" />
                      Find a Resource
                    </Link>
                  }
                />
              ) : (
                <div className="space-y-3">
                  {myBorrowedBookings.slice(0, 5).map((b) => (
                    <div
                      key={b.id}
                      className="p-3.5 bg-slate-50 border border-slate-200/60 rounded-xl flex items-center justify-between text-xs"
                    >
                      <div className="space-y-0.5">
                        <div className="font-semibold text-slate-800">
                          Reservation #{b.id.slice(0, 8)}
                        </div>
                        <div className="text-slate-500">{formatDate(b.start_dt)}</div>
                      </div>
                      <div className="flex items-center gap-3">
                        <StateBadge status={b.status} />
                        <Link
                          href={`/bookings/${b.id}`}
                          className="p-1.5 text-slate-400 hover:text-slate-700 rounded-md transition"
                        >
                          <ArrowRight className="w-4 h-4" />
                        </Link>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Quick Find Banner */}
            <div className="lg:col-span-4 bg-gradient-to-br from-blue-50 to-slate-50 border border-blue-100 rounded-2xl p-6 shadow-xs flex flex-col justify-between space-y-4">
              <div>
                <span className="text-[10px] font-bold text-blue-600 uppercase tracking-wider block">
                  Quick Action
                </span>
                <h4 className="text-base font-bold text-slate-900 mt-1">Find a Resource</h4>
                <p className="text-xs text-slate-600 mt-2 leading-relaxed">
                  Search across laboratory equipment, additive fabrication, optics, and precision sensors.
                </p>
              </div>

              <Link
                href="/resources"
                className="w-full py-2.5 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold rounded-xl text-center shadow-xs transition"
              >
                Browse Resource Pool
              </Link>
            </div>
          </div>
        </div>
      )}

      {/* OWNER DASHBOARD VIEW */}
      {mounted && activeRole === "OWNER" && (
        <div className="space-y-6">
          {/* Owner Metrics */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-white border border-slate-200/90 rounded-2xl p-5 shadow-xs">
              <span className="text-xs text-slate-500 font-medium block">
                Pending Approvals
              </span>
              <span className="text-2xl font-black text-amber-600 mt-1 block">
                {ownerPendingApprovals.length}
              </span>
            </div>
            <div className="bg-white border border-slate-200/90 rounded-2xl p-5 shadow-xs">
              <span className="text-xs text-slate-500 font-medium block">Active Handovers</span>
              <span className="text-2xl font-black text-blue-600 mt-1 block">
                {ownerActiveHandovers.length}
              </span>
            </div>
            <div className="bg-white border border-slate-200/90 rounded-2xl p-5 shadow-xs">
              <span className="text-xs text-slate-500 font-medium block">Listed Equipment</span>
              <span className="text-2xl font-black text-slate-900 mt-1 block">
                {myOwnedResources.length}
              </span>
            </div>
            <div className="bg-white border border-slate-200/90 rounded-2xl p-5 shadow-xs">
              <span className="text-xs text-slate-500 font-medium block">Total Incoming</span>
              <span className="text-2xl font-black text-slate-900 mt-1 block">
                {incomingOwnerRequests.length}
              </span>
            </div>
          </div>

          {/* Incoming Booking Requests Requiring Decision */}
          <div className="bg-white border border-slate-200/90 rounded-2xl p-6 shadow-xs space-y-4">
            <div className="flex justify-between items-center pb-2 border-b border-slate-100">
              <h3 className="font-bold text-slate-900 text-sm">
                Incoming Requests Requiring Decision
              </h3>
              <span className="text-xs font-semibold text-amber-600">
                {ownerPendingApprovals.length} pending
              </span>
            </div>

            {ownerPendingApprovals.length === 0 ? (
              <p className="text-xs text-slate-400 py-4 text-center">
                No incoming booking requests currently requiring owner action.
              </p>
            ) : (
              <div className="space-y-3">
                {ownerPendingApprovals.map((b) => (
                  <div
                    key={b.id}
                    className="p-4 bg-amber-50/50 border border-amber-200/70 rounded-xl flex items-center justify-between text-xs"
                  >
                    <div>
                      <div className="font-bold text-slate-900">
                        Booking Request #{b.id.slice(0, 8)}
                      </div>
                      <div className="text-slate-500 mt-0.5">
                        Dates: {formatDate(b.start_dt)} — {formatDate(b.end_dt)}
                      </div>
                      <p className="text-slate-600 mt-1 italic">Purpose: {b.purpose}</p>
                    </div>

                    <Link
                      href={`/bookings/${b.id}`}
                      className="px-3.5 py-1.5 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-lg shadow-xs transition"
                    >
                      Review & Approve
                    </Link>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* My Listed Equipment */}
          <div className="bg-white border border-slate-200/90 rounded-2xl p-6 shadow-xs space-y-4">
            <div className="flex justify-between items-center pb-2 border-b border-slate-100">
              <h3 className="font-bold text-slate-900 text-sm">My Listed Resources</h3>
              <Link
                href="/resources"
                className="text-xs text-blue-600 font-semibold hover:underline"
              >
                Catalog Pool
              </Link>
            </div>

            {myOwnedResources.length === 0 ? (
              <EmptyState
                icon={Box}
                title="No equipment listed yet"
                description="List your institutional laboratory instruments, 3D printers, or sensors to start accepting verified bookings."
              />
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {myOwnedResources.map((r) => (
                  <div
                    key={r.id}
                    className="p-4 bg-slate-50 border border-slate-200/70 rounded-xl flex items-center justify-between text-xs"
                  >
                    <div>
                      <div className="font-bold text-slate-900">{r.title}</div>
                      <div className="text-slate-500 mt-0.5">{r.location}</div>
                      <div className="text-slate-700 font-semibold mt-1">
                        {formatCurrency(r.daily_rate)} / day
                      </div>
                    </div>
                    <Link
                      href={`/resources/${r.id}`}
                      className="p-2 text-slate-400 hover:text-slate-700 rounded-lg transition"
                    >
                      <ArrowRight className="w-4 h-4" />
                    </Link>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
