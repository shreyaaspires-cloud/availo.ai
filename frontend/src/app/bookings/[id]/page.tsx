"use client"

import React, { useState } from "react"
import { useParams } from "next/navigation"
import Link from "next/link"
import {
  useBooking,
  useApproveBooking,
  useRejectBooking,
  useConfirmPayment,
} from "@/hooks/useBooking"
import { useResource } from "@/hooks/useResource"
import { useAuth } from "@/hooks/useAuth"
import { BookingTimeline } from "@/components/booking/BookingTimeline"
import { StateBadge } from "@/components/booking/StateBadge"
import { ContractViewer } from "@/components/contract/ContractViewer"
import { SixAnglePhotoUpload } from "@/components/condition/SixAnglePhotoUpload"
import { DamageReport } from "@/components/damage/DamageReport"
import { ChatWindow } from "@/components/chat/ChatWindow"
import { Button } from "@/components/ui/Button"
import { Alert } from "@/components/ui/Alert"
import { ConfirmationDialog } from "@/components/ui/ConfirmationDialog"
import { Textarea } from "@/components/ui/Input"
import { Skeleton } from "@/components/ui/Skeleton"
import { formatCurrency, formatDate } from "@/lib/utils"
import {
  CreditCard,
  Check,
  X,
  Sparkles,
  ChevronLeft,
  Calendar,
  User,
  ShieldCheck,
  AlertCircle,
  HelpCircle,
} from "lucide-react"
import toast from "react-hot-toast"

export default function BookingDetailPage() {
  const params = useParams()
  const id = params?.id as string
  const { user, isOwner: hasOwnerRole, isAdmin } = useAuth()

  // Poll booking every 10 seconds for real-time lifecycle transitions
  const { data: booking, isLoading, refetch } = useBooking(id, 10000)
  const { data: resource } = useResource(booking?.resource_id || "")

  const approveMutation = useApproveBooking()
  const rejectMutation = useRejectBooking()
  const confirmPaymentMutation = useConfirmPayment()

  const [rejectReason, setRejectReason] = useState("")
  const [showRejectModal, setShowRejectModal] = useState(false)
  const [showCancelModal, setShowCancelModal] = useState(false)

  if (isLoading || !booking) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-24 w-full rounded-2xl" />
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          <Skeleton className="lg:col-span-7 h-96 rounded-2xl" />
          <Skeleton className="lg:col-span-5 h-96 rounded-2xl" />
        </div>
      </div>
    )
  }

  const isUser = user?.id === booking.user_id
  const isResourceOwner = resource ? resource.owner_id === user?.id : hasOwnerRole

  // Action Responsibilities
  const getNextActionGuidance = () => {
    switch (booking.status) {
      case "PENDING_APPROVAL":
        return {
          action: "Awaiting Owner Approval",
          actor: isResourceOwner ? "You (Resource Owner)" : "Resource Owner",
          detail: isResourceOwner
            ? "Please review the reservation dates and purpose below, then approve or decline."
            : "The resource owner has been notified and is reviewing your reservation request.",
        }
      case "AWAITING_SIGNATURES":
        return {
          action: "Execute Digital Rental Agreement",
          actor: "Both Borrower & Owner",
          detail: "Sign the cryptographically verifiable smart rental agreement to proceed.",
        }
      case "AWAITING_PAYMENT":
        return {
          action: "Complete Escrow Security Payment",
          actor: isUser ? "You (Borrower)" : "Borrower",
          detail: isUser
            ? "Authorize rental fee and refundable escrow security deposit."
            : "Awaiting borrower to authorize escrow deposit via Razorpay.",
        }
      case "CONFIRMED":
        return {
          action: "Perform Check-in Photo Inspection",
          actor: isUser ? "You (Borrower)" : "Borrower",
          detail: isUser
            ? "Capture and upload all 6 canonical angles to set the equipment condition baseline."
            : "Borrower must capture the 6-angle baseline condition photos before taking equipment possession.",
        }
      case "CHECKED_IN":
        return {
          action: "In Active Use — Return When Ready",
          actor: isUser ? "You (Borrower)" : "Borrower",
          detail: isUser
            ? "Equipment is in your possession. When returning, capture the 6 matching check-out photos."
            : "Equipment is currently checked out to the borrower.",
        }
      case "RETURN_SUBMITTED":
        return {
          action: "Gemini AI Visual Damage Comparison Running",
          actor: "Availo Automated AI Inspection Engine",
          detail: "Before and after photographs are being compared for structural anomalies.",
        }
      case "DAMAGE_REVIEW":
        return {
          action: "Owner Condition Assessment Required",
          actor: isResourceOwner ? "You (Resource Owner)" : "Resource Owner",
          detail: isResourceOwner
            ? "AI detected potential anomalies or discrepancies. Review the report below to finalize escrow."
            : "The owner is reviewing the AI condition findings to confirm equipment status.",
        }
      case "DISPUTE_OPEN":
        return {
          action: "Administrative Arbitration Underway",
          actor: "Platform Administrator",
          detail: "An institutional admin is arbitrating the condition report and escrow distribution.",
        }
      case "COMPLETED":
        return {
          action: "Reservation Successfully Completed",
          actor: "Platform System",
          detail: "Equipment verified intact and security deposit released back to borrower.",
        }
      case "REJECTED":
        return {
          action: "Reservation Declined",
          actor: "Resource Owner",
          detail: booking.rejection_reason || "The reservation request was declined.",
        }
      case "CANCELLED":
        return {
          action: "Reservation Cancelled",
          actor: "Cancelled",
          detail: "This reservation is no longer active.",
        }
      default:
        return {
          action: booking.status.replace(/_/g, " "),
          actor: "System",
          detail: "Processing reservation status.",
        }
    }
  }

  const guidance = getNextActionGuidance()

  const handleApprove = async () => {
    try {
      await approveMutation.mutateAsync(id)
      toast.success("Booking approved! Cryptographic contract generated.")
      refetch()
    } catch (err: any) {
      toast.error(err.message || "Failed to approve booking")
    }
  }

  const handleReject = async () => {
    if (!rejectReason.trim()) {
      toast.error("Please provide a reason for rejecting the booking")
      return
    }
    try {
      await rejectMutation.mutateAsync({ id, reason: rejectReason.trim() })
      toast.success("Booking request declined")
      setShowRejectModal(false)
      refetch()
    } catch (err: any) {
      toast.error(err.message || "Failed to reject booking")
    }
  }

  const handleMockPayment = async () => {
    try {
      await confirmPaymentMutation.mutateAsync({
        id,
        razorpay_payment_id: `pay_mock_${Date.now()}`,
      })
      toast.success("Payment confirmed and held in secure platform escrow!")
      refetch()
    } catch (err: any) {
      toast.error(err.message || "Failed to process payment")
    }
  }

  return (
    <div className="space-y-6">
      {/* Back button */}
      <Link
        href="/bookings"
        className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-slate-900 transition"
      >
        <ChevronLeft className="w-4 h-4" />
        Back to Bookings
      </Link>

      {/* Guided Workflow Header Card */}
      <div className="bg-white border border-slate-200/90 rounded-2xl p-6 shadow-xs space-y-4">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            {resource && resource.images?.[0] && (
              <img
                src={resource.images[0].url}
                alt={resource.title}
                className="w-16 h-16 rounded-xl object-cover border border-slate-200 shrink-0"
              />
            )}
            <div>
              <div className="flex items-center gap-2.5">
                <h1 className="text-xl font-bold text-slate-900">
                  {resource?.title || `Booking #${booking.id.slice(0, 8)}`}
                </h1>
                <StateBadge status={booking.status} />
              </div>
              <p className="text-xs text-slate-500 mt-1 flex items-center gap-2">
                <span>Ref: #{booking.id.slice(0, 8)}</span>
                <span>·</span>
                <span>
                  {formatDate(booking.start_dt)} — {formatDate(booking.end_dt)}
                </span>
              </p>
            </div>
          </div>

          {/* Owner Quick Action Bar */}
          {booking.status === "PENDING_APPROVAL" && isResourceOwner && (
            <div className="flex items-center gap-2">
              <Button
                size="sm"
                variant="outline"
                onClick={() => setShowRejectModal(true)}
                className="text-rose-600 border-rose-200 hover:bg-rose-50"
              >
                <X className="w-3.5 h-3.5 mr-1" /> Decline
              </Button>
              <Button
                size="sm"
                onClick={handleApprove}
                loading={approveMutation.isPending}
              >
                <Check className="w-3.5 h-3.5 mr-1" /> Approve Reservation
              </Button>
            </div>
          )}
        </div>

        {/* Guided Next-Step Banner */}
        <div className="bg-slate-50 border border-slate-200/60 rounded-xl p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs">
          <div className="space-y-0.5">
            <div className="flex items-center gap-2">
              <span className="font-bold text-slate-900">{guidance.action}</span>
              <span className="text-[10px] bg-slate-200 text-slate-700 px-2 py-0.5 rounded font-medium">
                Responsible: {guidance.actor}
              </span>
            </div>
            <p className="text-slate-600">{guidance.detail}</p>
          </div>
        </div>
      </div>

      {/* Main Grid: Left Timeline & Action Panel, Right Chat & Financials */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left Column (7 cols): Lifecycle + Context-sensitive Actions */}
        <div className="lg:col-span-7 space-y-6">
          <BookingTimeline booking={booking} />

          {/* Context Action: Digital Contract Signing */}
          {booking.status === "AWAITING_SIGNATURES" && (
            <ContractViewer bookingId={booking.id} onRefetchBooking={refetch} />
          )}

          {/* Context Action: Escrow Payment */}
          {booking.status === "AWAITING_PAYMENT" && (
            <div className="bg-white border border-slate-200/90 rounded-2xl p-6 shadow-xs space-y-4">
              <div className="flex items-center gap-2">
                <CreditCard className="w-5 h-5 text-indigo-600" />
                <h3 className="font-bold text-slate-900 text-base">Escrow Payment Authorization</h3>
              </div>
              <p className="text-xs text-slate-600 leading-relaxed">
                Both parties have executed the digital rental contract. Rental fees and refundable
                security deposits are secured in institutional escrow until the return condition inspection
                passes.
              </p>
              <div className="bg-slate-50 p-4 rounded-xl border border-slate-200/60 flex justify-between items-center text-xs">
                <span className="text-slate-600 font-medium">Total Escrow Authorization:</span>
                <span className="text-base font-extrabold text-slate-900">
                  {formatCurrency(Number(booking.total_amount) + Number(booking.deposit_amount))}
                </span>
              </div>

              {isUser ? (
                <Button
                  onClick={handleMockPayment}
                  loading={confirmPaymentMutation.isPending}
                  className="w-full bg-indigo-600 hover:bg-indigo-700"
                >
                  Pay with Razorpay (Demo Mock Gateway)
                </Button>
              ) : (
                <p className="text-xs text-slate-400 italic text-center">
                  Awaiting borrower to complete escrow payment.
                </p>
              )}
            </div>
          )}

          {/* Context Action: Check-in Photo Upload */}
          {booking.status === "CONFIRMED" && (
            <SixAnglePhotoUpload
              bookingId={booking.id}
              reportType="CHECK_IN"
              onComplete={refetch}
            />
          )}

          {/* Context Action: Check-out Return Photo Upload */}
          {booking.status === "CHECKED_IN" && (
            <div className="space-y-4">
              <Alert variant="info" title="Resource in Active Use">
                The equipment is currently in the borrower's possession. When ready to conclude the
                borrowing session, capture all 6 matching check-out return photos below.
              </Alert>
              <SixAnglePhotoUpload
                bookingId={booking.id}
                reportType="CHECK_OUT"
                onComplete={refetch}
              />
            </div>
          )}

          {/* Context Action: AI Damage Inspection In Progress */}
          {booking.status === "RETURN_SUBMITTED" && (
            <div className="bg-white border border-slate-200/90 rounded-2xl p-8 text-center space-y-3 shadow-xs">
              <Sparkles className="w-8 h-8 text-blue-600 mx-auto animate-spin" />
              <h3 className="font-bold text-slate-900 text-base">Running AI Damage Inspection</h3>
              <p className="text-xs text-slate-500 max-w-sm mx-auto leading-relaxed">
                Gemini 2.0 Flash is evaluating all 6 before-and-after photo pairs for structural or
                cosmetic anomalies. Results will update automatically.
              </p>
            </div>
          )}

          {/* Context Action: AI Condition Assessment Report */}
          {(booking.status === "DAMAGE_REVIEW" ||
            booking.status === "COMPLETED" ||
            booking.status === "DISPUTE_OPEN" ||
            booking.status.startsWith("RESOLVED_")) && (
            <div className="bg-white border border-slate-200/90 rounded-2xl p-6 shadow-xs">
              <DamageReport bookingId={booking.id} bookingStatus={booking.status} isOwner={isResourceOwner} onRefresh={refetch} />
            </div>
          )}
        </div>

        {/* Right Column (5 cols): Live Chat & Financial Breakdown */}
        <div className="lg:col-span-5 space-y-6">
          <ChatWindow bookingId={booking.id} />

          {/* Financial Breakdown Card */}
          <div className="bg-white border border-slate-200/90 rounded-2xl p-5 shadow-xs space-y-3 text-xs">
            <h4 className="font-bold text-slate-800 text-sm">Financial Accounting</h4>
            <div className="flex justify-between py-1.5 border-b border-slate-100">
              <span className="text-slate-500">Rental Fee:</span>
              <span className="font-semibold text-slate-800">
                {formatCurrency(booking.total_amount)}
              </span>
            </div>
            <div className="flex justify-between py-1.5 border-b border-slate-100">
              <span className="text-slate-500">Refundable Deposit:</span>
              <span className="font-semibold text-slate-800">
                {formatCurrency(booking.deposit_amount)}
              </span>
            </div>
            <div className="flex justify-between pt-2 text-sm font-bold text-slate-900">
              <span>Total Value:</span>
              <span className="text-blue-600">
                {formatCurrency(Number(booking.total_amount) + Number(booking.deposit_amount))}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Reject Modal */}
      {showRejectModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-sm w-full p-6 space-y-4 shadow-xl">
            <h3 className="font-bold text-slate-900 text-base">Decline Booking Request</h3>
            <Textarea
              rows={3}
              value={rejectReason}
              onChange={(e) => setRejectReason(e.target.value)}
              placeholder="State reason for declining reservation..."
              required
            />
            <div className="flex justify-end gap-2">
              <Button size="sm" variant="ghost" onClick={() => setShowRejectModal(false)}>
                Cancel
              </Button>
              <Button
                size="sm"
                variant="danger"
                onClick={handleReject}
                loading={rejectMutation.isPending}
              >
                Confirm Decline
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
