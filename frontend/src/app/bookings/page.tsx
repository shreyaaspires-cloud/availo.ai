"use client"

import React from "react"
import Link from "next/link"
import { useBookings } from "@/hooks/useBooking"
import { StateBadge } from "@/components/booking/StateBadge"
import { formatCurrency, formatDate } from "@/lib/utils"
import { Calendar, ArrowRight, ShieldAlert } from "lucide-react"

export default function BookingsListPage() {
  const { data: bookings = [], isLoading } = useBookings()

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center bg-white border border-gray-200 p-6 rounded-2xl shadow-sm">
        <div>
          <h1 className="text-2xl font-extrabold text-gray-900 tracking-tight">Reservations & Bookings</h1>
          <p className="text-xs text-gray-500 mt-1">Track state machine progress, signatures, inspection & returns</p>
        </div>
        <Link
          href="/resources"
          className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold rounded-lg shadow-sm transition"
        >
          Book New Resource
        </Link>
      </div>

      {isLoading ? (
        <div className="space-y-3">
          {[1, 2, 3].map((n) => (
            <div key={n} className="h-24 bg-gray-100 rounded-xl animate-pulse" />
          ))}
        </div>
      ) : bookings.length === 0 ? (
        <div className="bg-white border border-gray-200 rounded-2xl p-12 text-center space-y-3">
          <Calendar className="w-8 h-8 text-gray-300 mx-auto" />
          <h3 className="text-sm font-semibold text-gray-700">No active bookings</h3>
          <p className="text-xs text-gray-400">You haven't requested or managed any equipment reservations yet.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {bookings.map((booking) => (
            <div
              key={booking.id}
              className="bg-white border border-gray-200 rounded-xl p-5 hover:shadow-sm transition flex flex-col md:flex-row md:items-center justify-between gap-4"
            >
              <div className="space-y-1.5">
                <div className="flex items-center gap-2.5">
                  <span className="font-mono text-xs font-bold text-gray-900">
                    Booking #{booking.id.slice(0, 8)}
                  </span>
                  <StateBadge status={booking.status} />
                </div>
                <div className="text-xs text-gray-500 flex items-center gap-4">
                  <span>Start: {formatDate(booking.start_dt)}</span>
                  <span>End: {formatDate(booking.end_dt)}</span>
                </div>
                <p className="text-xs text-gray-600 italic">Purpose: {booking.purpose || "Institutional use"}</p>
              </div>

              <div className="flex items-center gap-6 self-end md:self-center">
                <div className="text-right">
                  <div className="text-sm font-bold text-gray-900">
                    {formatCurrency(booking.total_amount)}
                  </div>
                  <div className="text-[11px] text-gray-400">
                    Deposit: {formatCurrency(booking.deposit_amount)}
                  </div>
                </div>

                <Link
                  href={`/bookings/${booking.id}`}
                  className="px-3.5 py-1.5 bg-gray-900 hover:bg-gray-800 text-white text-xs font-medium rounded-lg flex items-center gap-1.5 transition"
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
