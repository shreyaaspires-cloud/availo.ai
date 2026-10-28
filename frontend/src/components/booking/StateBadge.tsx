import React from "react"
import { BookingStatus } from "@/hooks/useBooking"
import { cn } from "@/lib/utils"

const statusStyles: Record<BookingStatus, string> = {
  COMPLETED: "bg-green-100 text-green-800 border-green-200",
  CONFIRMED: "bg-blue-100 text-blue-800 border-blue-200",
  PENDING_APPROVAL: "bg-yellow-100 text-yellow-800 border-yellow-200",
  AWAITING_SIGNATURES: "bg-amber-100 text-amber-800 border-amber-200",
  AWAITING_PAYMENT: "bg-indigo-100 text-indigo-800 border-indigo-200",
  CHECKED_IN: "bg-cyan-100 text-cyan-800 border-cyan-200",
  RETURN_SUBMITTED: "bg-sky-100 text-sky-800 border-sky-200",
  DAMAGE_REVIEW: "bg-orange-100 text-orange-800 border-orange-200",
  DISPUTE_OPEN: "bg-red-100 text-red-800 border-red-200",
  RESOLVED_OWNER: "bg-purple-100 text-purple-800 border-purple-200",
  RESOLVED_USER: "bg-emerald-100 text-emerald-800 border-emerald-200",
  RESOLVED_SPLIT: "bg-teal-100 text-teal-800 border-teal-200",
  CANCELLED: "bg-gray-100 text-gray-600 border-gray-200",
  WAITLISTED: "bg-purple-100 text-purple-800 border-purple-200",
  DRAFT: "bg-gray-100 text-gray-700 border-gray-200",
  REJECTED: "bg-rose-100 text-rose-800 border-rose-200",
  APPROVED: "bg-blue-50 text-blue-700 border-blue-200",
}

export const StateBadge: React.FC<{ status: BookingStatus; className?: string }> = ({
  status,
  className,
}) => {
  const label = status.replace(/_/g, " ")
  const style = statusStyles[status] || "bg-gray-100 text-gray-800"

  return (
    <span
      className={cn(
        "inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold border",
        style,
        className
      )}
    >
      {label}
    </span>
  )
}
