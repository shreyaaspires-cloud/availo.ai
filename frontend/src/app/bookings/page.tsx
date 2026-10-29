"use client"

import React, { useState, useEffect } from "react"
import Link from "next/link"
import { useBookings } from "@/hooks/useBooking"
import { StateBadge } from "@/components/booking/StateBadge"
import { EmptyState } from "@/components/ui/EmptyState"
import { Skeleton } from "@/components/ui/Skeleton"
import { formatCurrency, formatDate } from "@/lib/utils"
import { Calendar, ArrowRight, Compass, Filter } from "lucide-react"

export default function BookingsListPage() {
  const [mounted, setMounted] = useState(false)
  useEffect(() => {
    setMounted(true)
  }, [])

  const { data: bookings = [], isLoading } = useBookings()
  const [filterTab, setFilterTab] = useState<"ALL" | "ACTIVE" | "COMPLETED" | "ACTION_REQUIRED">("ALL")

  const filteredBookings = bookings.filter((b) => {
    if (filterTab === "ACTIVE") {
      return ["CONFIRMED", "CHECKED_IN", "AWAITING_PAYMENT", "AWAITING_SIGNATURES"].includes(b.status)
    }
    if (filterTab === "ACTION_REQUIRED") {
      return ["PENDING_APPROVAL", "AWAITING_SIGNATURES", "AWAITING_PAYMENT", "DAMAGE_REVIEW", "DISPUTE_OPEN"].includes(b.status)
    }
    if (filterTab === "COMPLETED") {
      return ["COMPLETED", "RESOLVED_USER", "RESOLVED_OWNER", "RESOLVED_SPLIT", "REJECTED", "CANCELLED"].includes(b.status)
    }
    return true
  })

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white border border-slate-200/90 p-6 rounded-2xl shadow-xs">
        <div>
          <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">
            My Reservations & Bookings
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            Track smart contract progression, condition inspections, and escrow releases.
          </p>
        </div>
        <Link
          href="/resources"
          className="inline-flex items-center gap-1.5 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold rounded-xl shadow-xs transition"
        >
          <Compass className="w-4 h-4" />
          Browse Resources
        </Link>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 border-b border-slate-200 pb-2 overflow-x-auto text-xs font-medium">
        {[
          { key: "ALL", label: `All (${bookings.length})` },
          {
            key: "ACTION_REQUIRED",
            label: `Action Required (${
              bookings.filter((b) =>
                ["PENDING_APPROVAL", "AWAITING_SIGNATURES", "AWAITING_PAYMENT", "DAMAGE_REVIEW"].includes(
                  b.status
                )
              ).length
            })`,
          },
          {
            key: "ACTIVE",
            label: `Active In-Use (${
              bookings.filter((b) => ["CONFIRMED", "CHECKED_IN"].includes(b.status)).length
            })`,
          },
          {
            key: "COMPLETED",
            label: `Archived & Settled (${
              bookings.filter((b) =>
                ["COMPLETED", "RESOLVED_USER", "RESOLVED_OWNER", "RESOLVED_SPLIT", "CANCELLED", "REJECTED"].includes(
                  b.status
                )
              ).length
            })`,
          },
        ].map((tab) => (
          <button
            key={tab.key}
            onClick={() => setFilterTab(tab.key as any)}
            className={`px-3 py-1.5 rounded-lg transition whitespace-nowrap ${
              filterTab === tab.key
                ? "bg-slate-900 text-white font-semibold shadow-xs"
                : "text-slate-600 hover:bg-slate-100"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* List */}
      {!mounted || isLoading ? (
        <div className="space-y-3">
          {[1, 2, 3].map((n) => (
            <div key={n} className="bg-white border border-slate-200 rounded-2xl p-5 space-y-3">
              <Skeleton className="h-5 w-48 rounded" />
              <Skeleton className="h-4 w-72 rounded" />
            </div>
          ))}
        </div>
      ) : filteredBookings.length === 0 ? (
        <EmptyState
          icon={Calendar}
          title="No reservations found"
          description={
            filterTab === "ALL"
              ? "You haven't requested any equipment reservations yet. Find available instruments in the resource catalog."
              : "No bookings match the selected status category."
          }
          action={
            filterTab === "ALL" ? (
              <Link
                href="/resources"
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold rounded-xl transition"
              >
                Find a Resource
              </Link>
            ) : undefined
          }
        />
      ) : (
        <div className="space-y-3">
          {filteredBookings.map((booking) => (
            <div
              key={booking.id}
              className="bg-white border border-slate-200/90 rounded-2xl p-5 hover:border-slate-300 hover:shadow-xs transition flex flex-col md:flex-row md:items-center justify-between gap-4"
            >
              <div className="space-y-1.5">
                <div className="flex items-center gap-2.5">
                  <span className="font-mono text-xs font-bold text-slate-900">
                    Booking #{booking.id.slice(0, 8)}
                  </span>
                  <StateBadge status={booking.status} />
                </div>
                <div className="text-xs text-slate-500 flex items-center gap-4">
                  <span>Start: {formatDate(booking.start_dt)}</span>
                  <span>End: {formatDate(booking.end_dt)}</span>
                </div>
                <p className="text-xs text-slate-600 italic">
                  Purpose: {booking.purpose || "Institutional research / lab experiment"}
                </p>
              </div>

              <div className="flex items-center gap-6 self-end md:self-center">
                <div className="text-right">
                  <div className="text-sm font-extrabold text-slate-900">
                    {formatCurrency(booking.total_amount)}
                  </div>
                  <div className="text-[11px] text-slate-400">
                    Deposit: {formatCurrency(booking.deposit_amount)}
                  </div>
                </div>

                <Link
                  href={`/bookings/${booking.id}`}
                  className="px-4 py-2 bg-slate-900 hover:bg-slate-800 text-white text-xs font-semibold rounded-xl flex items-center gap-1.5 shadow-xs transition"
                >
                  Manage <ArrowRight className="w-3.5 h-3.5" />
                </Link>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
