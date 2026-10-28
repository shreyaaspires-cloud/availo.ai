import React from "react"
import { BookingItem, BookingStatus } from "@/hooks/useBooking"
import { Check, Clock, AlertTriangle, ShieldCheck } from "lucide-react"

interface BookingTimelineProps {
  booking: BookingItem
}

const LIFECYCLE_STEPS: { status: BookingStatus; label: string; desc: string }[] = [
  { status: "PENDING_APPROVAL", label: "Awaiting Owner Review", desc: "Submitted to resource owner" },
  { status: "AWAITING_SIGNATURES", label: "Sign Contract", desc: "Dual digital e-signatures required" },
  { status: "AWAITING_PAYMENT", label: "Complete Payment", desc: "Secure escrow deposit and fees" },
  { status: "CONFIRMED", label: "Confirmed", desc: "Ready for check-in inspection" },
  { status: "CHECKED_IN", label: "Checked In & In Use", desc: "Resource currently in possession" },
  { status: "RETURN_SUBMITTED", label: "Return Submitted", desc: "AI Damage inspection executing" },
  { status: "COMPLETED", label: "Completed", desc: "Inspection passed, escrow returned" },
]

export const BookingTimeline: React.FC<BookingTimelineProps> = ({ booking }) => {
  const currentIdx = LIFECYCLE_STEPS.findIndex((s) => s.status === booking.status)

  return (
    <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
      <h3 className="text-sm font-bold text-gray-900 mb-6">Reservation Lifecycle</h3>

      <div className="relative pl-6 space-y-6 before:absolute before:left-2.5 before:top-2 before:bottom-2 before:w-0.5 before:bg-gray-200">
        {LIFECYCLE_STEPS.map((step, idx) => {
          const isPassed = currentIdx > idx || booking.status === "COMPLETED"
          const isCurrent = booking.status === step.status
          const isFuture = currentIdx !== -1 && currentIdx < idx

          return (
            <div key={step.status} className="relative flex items-start gap-4">
              <div
                className={`absolute -left-6 top-0.5 w-5 h-5 rounded-full flex items-center justify-center text-[10px] ${
                  isCurrent
                    ? "bg-blue-600 text-white ring-4 ring-blue-100 animate-pulse"
                    : isPassed
                    ? "bg-emerald-500 text-white"
                    : "bg-gray-200 text-gray-400"
                }`}
              >
                {isPassed ? <Check className="w-3 h-3 stroke-[3]" /> : idx + 1}
              </div>

              <div>
                <h4
                  className={`text-xs font-bold ${
                    isCurrent
                      ? "text-blue-600"
                      : isPassed
                      ? "text-gray-900"
                      : "text-gray-400"
                  }`}
                >
                  {step.label}
                </h4>
                <p className="text-[11px] text-gray-500 mt-0.5">{step.desc}</p>
              </div>
            </div>
          )
        })}

        {booking.status === "DAMAGE_REVIEW" && (
          <div className="relative flex items-start gap-4 text-orange-600">
            <div className="absolute -left-6 top-0.5 w-5 h-5 rounded-full bg-orange-500 text-white flex items-center justify-center">
              <AlertTriangle className="w-3 h-3" />
            </div>
            <div>
              <h4 className="text-xs font-bold text-orange-600">Damage Review Underway</h4>
              <p className="text-[11px] text-orange-500 mt-0.5">Owner review & dispute assessment in progress</p>
            </div>
          </div>
        )}

        {booking.status === "DISPUTE_OPEN" && (
          <div className="relative flex items-start gap-4 text-rose-600">
            <div className="absolute -left-6 top-0.5 w-5 h-5 rounded-full bg-rose-500 text-white flex items-center justify-center">
              <AlertTriangle className="w-3 h-3" />
            </div>
            <div>
              <h4 className="text-xs font-bold text-rose-600">Dispute Escalated</h4>
              <p className="text-[11px] text-rose-500 mt-0.5">Admin arbitration reviewing condition discrepancy</p>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
