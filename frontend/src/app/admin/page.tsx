"use client"

import React from "react"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { api } from "@/lib/api"
import { Button } from "@/components/ui/Button"
import { ShieldCheck, AlertCircle, Clock, Check, X, ShieldAlert } from "lucide-react"
import toast from "react-hot-toast"

export default function AdminDashboardPage() {
  const queryClient = useQueryClient()

  const { data: stats } = useQuery<any>({
    queryKey: ["admin-dashboard"],
    queryFn: () => api.get("/admin/dashboard"),
    refetchInterval: 15000,
  })

  const { data: verifications = [] } = useQuery<any[]>({
    queryKey: ["admin-verifications"],
    queryFn: () => api.get("/admin/verifications"),
  })

  const { data: disputes = [] } = useQuery<any[]>({
    queryKey: ["admin-disputes"],
    queryFn: () => api.get("/admin/disputes"),
  })

  const approveBadgeMutation = useMutation({
    mutationFn: (id: string) => api.post(`/admin/verifications/${id}/approve`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-verifications"] })
      queryClient.invalidateQueries({ queryKey: ["admin-dashboard"] })
      toast.success("Credential approved & badge issued")
    },
  })

  const rejectBadgeMutation = useMutation({
    mutationFn: (id: string) => api.post(`/admin/verifications/${id}/reject`, { reason: "Credential unverified" }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-verifications"] })
      toast.success("Credential rejected")
    },
  })

  const resolveDisputeMutation = useMutation({
    mutationFn: ({ bookingId, outcome }: { bookingId: string; outcome: string }) =>
      api.post(`/admin/disputes/${bookingId}/resolve`, {
        outcome,
        note: `Administrative arbitration outcome: ${outcome}`,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-disputes"] })
      queryClient.invalidateQueries({ queryKey: ["admin-dashboard"] })
      toast.success("Dispute arbitration executed & escrow settled")
    },
  })

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="bg-white border border-gray-200 rounded-2xl p-6 shadow-sm flex justify-between items-center">
        <div>
          <h1 className="text-xl font-bold text-gray-900">Availo Administrative Portal</h1>
          <p className="text-xs text-gray-500 mt-1">Platform moderation, verification badge decisions & escrow dispute arbitration</p>
        </div>
        <span className="bg-purple-100 text-purple-800 text-xs px-3 py-1 rounded-full font-bold">
          ADMIN ACCESS
        </span>
      </div>

      {/* Metrics */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-white border border-gray-200 rounded-xl p-4 shadow-sm">
          <span className="text-xs text-gray-500 font-medium">Pending Verifications</span>
          <span className="text-2xl font-black text-gray-900 block mt-1">{stats?.pending_verifications ?? 0}</span>
        </div>
        <div className="bg-white border border-gray-200 rounded-xl p-4 shadow-sm">
          <span className="text-xs text-gray-500 font-medium">Open Disputes</span>
          <span className="text-2xl font-black text-rose-600 block mt-1">{stats?.open_disputes ?? 0}</span>
        </div>
        <div className="bg-white border border-gray-200 rounded-xl p-4 shadow-sm">
          <span className="text-xs text-gray-500 font-medium">Active Bookings</span>
          <span className="text-2xl font-black text-blue-600 block mt-1">{stats?.active_bookings ?? 0}</span>
        </div>
        <div className="bg-white border border-gray-200 rounded-xl p-4 shadow-sm">
          <span className="text-xs text-gray-500 font-medium">Platform Utilisation</span>
          <span className="text-2xl font-black text-emerald-600 block mt-1">
            {stats?.platform_utilisation_pct ?? 0}%
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Verification Queue */}
        <div className="bg-white border border-gray-200 rounded-2xl p-6 shadow-sm space-y-4">
          <div className="flex items-center gap-2 pb-2 border-b border-gray-100">
            <ShieldCheck className="w-5 h-5 text-purple-600" />
            <h3 className="font-bold text-gray-900 text-sm">Badge Verification Queue</h3>
          </div>

          <div className="space-y-3">
            {verifications.length === 0 ? (
              <div className="p-8 text-center text-xs text-gray-400">
                No pending badge verifications awaiting review.
              </div>
            ) : (
              verifications.map((v) => (
                <div key={v.id} className="p-4 border border-gray-100 rounded-xl bg-gray-50 space-y-2">
                  <div className="flex justify-between items-center text-xs">
                    <span className="font-bold text-gray-800">Badge Type: {v.badge_type}</span>
                    <span className="bg-amber-100 text-amber-800 px-2 py-0.5 rounded text-[11px] font-semibold">
                      PENDING REVIEW
                    </span>
                  </div>
                  <p className="text-[11px] text-gray-500 truncate">Doc: {v.document_url}</p>
                  <div className="flex justify-end gap-2 pt-2 border-t border-gray-200">
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => rejectBadgeMutation.mutate(v.id)}
                      className="text-rose-600 border-rose-200"
                    >
                      <X className="w-3.5 h-3.5 mr-1" /> Reject
                    </Button>
                    <Button
                      size="sm"
                      onClick={() => approveBadgeMutation.mutate(v.id)}
                    >
                      <Check className="w-3.5 h-3.5 mr-1" /> Approve
                    </Button>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Dispute Arbitration Queue */}
        <div className="bg-white border border-gray-200 rounded-2xl p-6 shadow-sm space-y-4">
          <div className="flex items-center gap-2 pb-2 border-b border-gray-100">
            <ShieldAlert className="w-5 h-5 text-rose-600" />
            <h3 className="font-bold text-gray-900 text-sm">Escrow Dispute Arbitration</h3>
          </div>

          <div className="space-y-3">
            {disputes.length === 0 ? (
              <div className="p-8 text-center text-xs text-gray-400">
                No open disputes in arbitration queue.
              </div>
            ) : (
              disputes.map((d) => (
                <div key={d.id} className="p-4 border border-rose-100 rounded-xl bg-rose-50/40 space-y-3">
                  <div className="flex justify-between items-center text-xs">
                    <span className="font-bold text-rose-900">Booking #{d.booking_id.slice(0, 8)}</span>
                    <span className="bg-rose-100 text-rose-800 px-2 py-0.5 rounded text-[11px] font-semibold">
                      DISPUTE OPEN
                    </span>
                  </div>
                  <div className="flex gap-2 justify-end pt-2 border-t border-rose-200">
                    <button
                      onClick={() => resolveDisputeMutation.mutate({ bookingId: d.booking_id, outcome: "OWNER" })}
                      className="px-2.5 py-1 text-xs bg-white rounded border border-gray-300 font-semibold text-gray-800 hover:bg-gray-50"
                    >
                      Release to Owner
                    </button>
                    <button
                      onClick={() => resolveDisputeMutation.mutate({ bookingId: d.booking_id, outcome: "SPLIT" })}
                      className="px-2.5 py-1 text-xs bg-white rounded border border-gray-300 font-semibold text-gray-800 hover:bg-gray-50"
                    >
                      50 / 50 Split
                    </button>
                    <button
                      onClick={() => resolveDisputeMutation.mutate({ bookingId: d.booking_id, outcome: "USER" })}
                      className="px-2.5 py-1 text-xs bg-emerald-600 text-white rounded font-semibold hover:bg-emerald-700"
                    >
                      Refund User
                    </button>
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
