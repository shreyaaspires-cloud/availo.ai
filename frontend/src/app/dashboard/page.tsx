"use client"

import React from "react"
import { useAuth } from "@/hooks/useAuth"
import { useBookings } from "@/hooks/useBooking"
import { useResources } from "@/hooks/useResource"
import { StateBadge } from "@/components/booking/StateBadge"
import { formatCurrency, formatDate } from "@/lib/utils"
import Link from "next/link"
import { ShieldCheck, Plus, Package, ArrowRight, User } from "lucide-react"

export default function DashboardPage() {
  const { user, isOwner, isAdmin } = useAuth()
  const { data: bookings = [] } = useBookings()
  const { data: resources = [] } = useResources()

  const myOwnedResources = resources.filter((r) => r.owner_id === user?.id)
  const pendingApprovals = bookings.filter((b) => b.status === "PENDING_APPROVAL")

  return (
    <div className="space-y-8">
      {/* Header Profile */}
      <div className="bg-white border border-gray-200 rounded-2xl p-6 shadow-sm flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-xl bg-blue-100 text-blue-700 flex items-center justify-center font-bold text-lg">
            {user?.full_name?.charAt(0) || "U"}
          </div>
          <div>
            <h1 className="text-xl font-bold text-gray-900">{user?.full_name || "Availo Member"}</h1>
            <p className="text-xs text-gray-500">{user?.email}</p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <span className="bg-emerald-100 text-emerald-800 text-xs px-2.5 py-1 rounded-full font-semibold flex items-center gap-1">
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" /> Trust Score: {user?.trust_score || 100}/100
          </span>
          {user?.roles?.map((role) => (
            <span key={role} className="bg-gray-100 text-gray-700 text-xs px-2.5 py-1 rounded-full font-semibold">
              {role}
            </span>
          ))}
        </div>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm">
          <span className="text-xs text-gray-500 font-medium block">Total Reservations</span>
          <span className="text-2xl font-black text-gray-900 mt-1 block">{bookings.length}</span>
        </div>
        <div className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm">
          <span className="text-xs text-gray-500 font-medium block">Pending Approvals</span>
          <span className="text-2xl font-black text-amber-600 mt-1 block">{pendingApprovals.length}</span>
        </div>
        <div className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm">
          <span className="text-xs text-gray-500 font-medium block">Listed Equipment</span>
          <span className="text-2xl font-black text-blue-600 mt-1 block">{myOwnedResources.length}</span>
        </div>
      </div>

      {/* Quick Action Tables */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Bookings / Incoming Requests */}
        <div className="bg-white border border-gray-200 rounded-2xl p-6 shadow-sm space-y-4">
          <div className="flex justify-between items-center pb-2 border-b border-gray-100">
            <h3 className="font-bold text-gray-900 text-sm">Recent Reservations</h3>
            <Link href="/bookings" className="text-xs text-blue-600 font-semibold hover:underline">
              View All
            </Link>
          </div>

          <div className="space-y-3">
            {bookings.slice(0, 4).map((b) => (
              <div key={b.id} className="p-3 bg-gray-50 rounded-xl flex items-center justify-between text-xs">
                <div>
                  <div className="font-semibold text-gray-800">Booking #{b.id.slice(0, 8)}</div>
                  <div className="text-gray-500 mt-0.5">{formatDate(b.start_dt)}</div>
                </div>
                <div className="flex items-center gap-3">
                  <StateBadge status={b.status} />
                  <Link href={`/bookings/${b.id}`} className="text-gray-400 hover:text-gray-600">
                    <ArrowRight className="w-4 h-4" />
                  </Link>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Managed Resources (Owner View) */}
        <div className="bg-white border border-gray-200 rounded-2xl p-6 shadow-sm space-y-4">
          <div className="flex justify-between items-center pb-2 border-b border-gray-100">
            <h3 className="font-bold text-gray-900 text-sm">My Listed Resources</h3>
            <Link href="/resources" className="text-xs text-blue-600 font-semibold hover:underline">
              Browse Pool
            </Link>
          </div>

          <div className="space-y-3">
            {myOwnedResources.length === 0 ? (
              <div className="p-8 text-center text-xs text-gray-400">
                You currently have no listed resources. Sign in with an OWNER account to publish assets.
              </div>
            ) : (
              myOwnedResources.map((r) => (
                <div key={r.id} className="p-3 bg-gray-50 rounded-xl flex items-center justify-between text-xs">
                  <div>
                    <div className="font-semibold text-gray-800">{r.title}</div>
                    <div className="text-gray-500 mt-0.5">{r.location}</div>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="font-bold text-gray-900">{formatCurrency(r.daily_rate)}/day</span>
                    <Link href={`/resources/${r.id}`} className="text-gray-400 hover:text-gray-600">
                      <ArrowRight className="w-4 h-4" />
                    </Link>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
