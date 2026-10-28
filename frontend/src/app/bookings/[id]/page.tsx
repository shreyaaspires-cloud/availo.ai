"use client"

import React, { useState } from "react"
import { useParams } from "next/navigation"
import {
  useBooking,
  useApproveBooking,
  useRejectBooking,
  useConfirmPayment,
} from "@/hooks/useBooking"
import { useAuth } from "@/hooks/useAuth"
import { BookingTimeline } from "@/components/booking/BookingTimeline"
import { StateBadge } from "@/components/booking/StateBadge"
import { ContractViewer } from "@/components/contract/ContractViewer"
import { SixAnglePhotoUpload } from "@/components/condition/SixAnglePhotoUpload"
import { DamageReport } from "@/components/damage/DamageReport"
import { ChatWindow } from "@/components/chat/ChatWindow"
import { Button } from "@/components/ui/Button"
import { formatCurrency, formatDate } from "@/lib/utils"
import { CreditCard, Check, X, ShieldAlert, Sparkles } from "lucide-react"
import toast from "react-hot-toast"

export default function BookingDetailPage() {
  const params = useParams()
  const id = params?.id as string
  const { user } = useAuth()

  // Poll booking every 10 seconds for real-time lifecycle transitions
  const { data: booking, isLoading, refetch } = useBooking(id, 10000)

  const approveMutation = useApproveBooking()
  const rejectMutation = useRejectBooking()
  const confirmPaymentMutation = useConfirmPayment()

  const [rejectReason, setRejectReason] = useState("")
  const [showRejectModal, setShowRejectModal] = useState(false)

  if (isLoading || !booking) {
    return <div className="p-12 text-center text-sm text-gray-500">Loading reservation status...</div>
  }

  const isUser = user?.id === booking.user_id
  const isOwner = user?.roles?.includes("OWNER")

  const handleApprove = async () => {
    try {
      await approveMutation.mutateAsync(id)
      toast.success("Booking approved. Contract auto-generated!")
      refetch()
    } catch (err: any) {
      toast.error(err.message || "Failed to approve booking")
    }
  }

  const handleReject = async () => {
    if (!rejectReason) {
      toast.error("Please provide a rejection reason")
      return
    }
    try {
      await rejectMutation.mutateAsync({ id, reason: rejectReason })
      toast.success("Booking rejected")
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
      toast.success("Payment confirmed & held in platform escrow!")
      refetch()
    } catch (err: any) {
      toast.error(err.message || "Failed to process payment")
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white border border-gray-200 rounded-2xl p-6 shadow-sm flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div className="space-y-1">
          <div className="flex items-center gap-3">
            <h1 className="text-xl font-bold text-gray-900">
              Booking #{booking.id.slice(0, 8)}
            </h1>
            <StateBadge status={booking.status} />
          </div>
          <p className="text-xs text-gray-500">
            {formatDate(booking.start_dt)} — {formatDate(booking.end_dt)}
          </p>
        </div>

        {/* Top level actions for Owner Review */}
        {booking.status === "PENDING_APPROVAL" && isOwner && (
          <div className="flex items-center gap-2">
            <Button
              size="sm"
              variant="outline"
              onClick={() => setShowRejectModal(true)}
              className="text-rose-600 border-rose-200 hover:bg-rose-50"
            >
              <X className="w-3.5 h-3.5 mr-1" /> Reject
            </Button>
            <Button
              size="sm"
              onClick={handleApprove}
              loading={approveMutation.isPending}
            >
              <Check className="w-3.5 h-3.5 mr-1" /> Approve Request
            </Button>
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column (60%): Timeline & Context-Sensitive Action Panel */}
        <div className="lg:col-span-7 space-y-6">
          <BookingTimeline booking={booking} />

          {/* Context Action Panel */}
          {booking.status === "AWAITING_SIGNATURES" && (
            <ContractViewer bookingId={booking.id} onRefetchBooking={refetch} />
          )}

          {booking.status === "AWAITING_PAYMENT" && (
            <div className="bg-white border border-gray-200 rounded-2xl p-6 shadow-sm space-y-4">
              <div className="flex items-center gap-2">
                <CreditCard className="w-5 h-5 text-indigo-600" />
                <h3 className="font-bold text-gray-900 text-base">Escrow Payment Required</h3>
              </div>
              <p className="text-xs text-gray-600">
                Both parties have executed the digital rental contract. Deposit and rental fees are placed into secure escrow until safe equipment return.
              </p>
              <div className="bg-gray-50 p-3 rounded-lg flex justify-between text-xs font-semibold">
                <span>Total Amount Due (Rental + Escrow):</span>
                <span>{formatCurrency(Number(booking.total_amount) + Number(booking.deposit_amount))}</span>
              </div>
              <Button
                onClick={handleMockPayment}
                loading={confirmPaymentMutation.isPending}
                className="w-full bg-indigo-600 hover:bg-indigo-700"
              >
                Pay with Razorpay (Demo Mock Payment)
              </Button>
            </div>
          )}

          {booking.status === "CONFIRMED" && (
            <SixAnglePhotoUpload
              bookingId={booking.id}
              reportType="CHECK_IN"
              onComplete={refetch}
            />
          )}

          {booking.status === "CHECKED_IN" && (
            <div className="space-y-4">
              <div className="bg-cyan-50 border border-cyan-200 p-4 rounded-xl text-xs text-cyan-800">
                Resource is in active use. When ready to return, capture all 6 check-out photos below.
              </div>
              <SixAnglePhotoUpload
                bookingId={booking.id}
                reportType="CHECK_OUT"
                onComplete={refetch}
              />
            </div>
          )}

          {booking.status === "RETURN_SUBMITTED" && (
            <div className="bg-white border border-gray-200 rounded-2xl p-8 text-center space-y-3">
              <Sparkles className="w-8 h-8 text-blue-600 mx-auto animate-spin" />
              <h3 className="font-bold text-gray-900 text-base">Running AI Damage Inspection</h3>
              <p className="text-xs text-gray-500 max-w-sm mx-auto">
                Gemini 2.0 Flash is evaluating all 6 before-and-after photo pairs for structural or cosmetic anomalies.
              </p>
            </div>
          )}

          {(booking.status === "DAMAGE_REVIEW" ||
            booking.status === "COMPLETED" ||
            booking.status === "DISPUTE_OPEN" ||
            booking.status.startsWith("RESOLVED_")) && (
            <div className="bg-white border border-gray-200 rounded-2xl p-6 shadow-sm">
              <DamageReport bookingId={booking.id} />
            </div>
          )}
        </div>

        {/* Right Column (40%): Live Chat & Financial Summary */}
        <div className="lg:col-span-5 space-y-6">
          <ChatWindow bookingId={booking.id} />

          <div className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm space-y-3 text-xs">
            <h4 className="font-bold text-gray-800 text-sm">Financial Breakdown</h4>
            <div className="flex justify-between py-1 border-b border-gray-100">
              <span className="text-gray-500">Rental Fee:</span>
              <span className="font-semibold text-gray-800">{formatCurrency(booking.total_amount)}</span>
            </div>
            <div className="flex justify-between py-1 border-b border-gray-100">
              <span className="text-gray-500">Refundable Deposit:</span>
              <span className="font-semibold text-gray-800">{formatCurrency(booking.deposit_amount)}</span>
            </div>
            <div className="flex justify-between pt-1 font-bold text-gray-900">
              <span>Total Value:</span>
              <span>{formatCurrency(Number(booking.total_amount) + Number(booking.deposit_amount))}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Reject Modal */}
      {showRejectModal && (
        <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-sm w-full p-6 space-y-4">
            <h3 className="font-bold text-gray-900 text-base">Reject Booking Request</h3>
            <textarea
              rows={3}
              value={rejectReason}
              onChange={(e) => setRejectReason(e.target.value)}
              placeholder="State reason for rejecting request..."
              className="w-full bg-gray-50 border border-gray-200 rounded-lg p-2.5 text-xs text-gray-800 focus:outline-none focus:ring-1 focus:ring-blue-500"
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
                Confirm Rejection
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
