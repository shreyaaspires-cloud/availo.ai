"use client"

import React, { useState } from "react"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { api } from "@/lib/api"
import { Button } from "@/components/ui/Button"
import { Alert } from "@/components/ui/Alert"
import { EmptyState } from "@/components/ui/EmptyState"
import { ConfirmationDialog } from "@/components/ui/ConfirmationDialog"
import { Skeleton } from "@/components/ui/Skeleton"
import {
  ShieldCheck,
  ShieldAlert,
  Clock,
  Check,
  X,
  AlertTriangle,
  History,
  FileCheck,
  ExternalLink,
} from "lucide-react"
import toast from "react-hot-toast"

export default function AdminDashboardPage() {
  const queryClient = useQueryClient()
  const [activeTab, setActiveTab] = useState<"OVERVIEW" | "VERIFICATIONS" | "DISPUTES" | "AUDIT">(
    "OVERVIEW"
  )

  const [disputeToResolve, setDisputeToResolve] = useState<{
    bookingId: string
    outcome: string
  } | null>(null)

  const { data: stats, isLoading: statsLoading } = useQuery<any>({
    queryKey: ["admin-dashboard"],
    queryFn: () => api.get("/admin/dashboard"),
    refetchInterval: 15000,
  })

  const { data: verifications = [], isLoading: verificationsLoading } = useQuery<any[]>({
    queryKey: ["admin-verifications"],
    queryFn: () => api.get("/admin/verifications"),
  })

  const { data: disputes = [], isLoading: disputesLoading } = useQuery<any[]>({
    queryKey: ["admin-disputes"],
    queryFn: () => api.get("/admin/disputes"),
  })

  const { data: overdueBookings = [], isLoading: overdueLoading } = useQuery<any[]>({
    queryKey: ["admin-overdue"],
    queryFn: () => api.get("/admin/overdue"),
  })

  const approveBadgeMutation = useMutation({
    mutationFn: (id: string) => api.post(`/admin/verifications/${id}/approve`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-verifications"] })
      queryClient.invalidateQueries({ queryKey: ["admin-dashboard"] })
      toast.success("Credential approved and institutional badge issued!")
    },
    onError: (err: any) => {
      toast.error(err.message || "Failed to approve badge")
    },
  })

  const rejectBadgeMutation = useMutation({
    mutationFn: (id: string) =>
      api.post(`/admin/verifications/${id}/reject`, {
        reason: "Credential documentation did not meet verification criteria",
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-verifications"] })
      queryClient.invalidateQueries({ queryKey: ["admin-dashboard"] })
      toast.success("Credential submission rejected")
    },
    onError: (err: any) => {
      toast.error(err.message || "Failed to reject badge")
    },
  })

  const resolveDisputeMutation = useMutation({
    mutationFn: ({ bookingId, outcome }: { bookingId: string; outcome: string }) =>
      api.post(`/admin/disputes/${bookingId}/resolve`, {
        outcome,
        note: `Administrative arbitration determination: ${outcome}`,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-disputes"] })
      queryClient.invalidateQueries({ queryKey: ["admin-dashboard"] })
      toast.success("Dispute arbitration resolved & escrow distributed!")
      setDisputeToResolve(null)
    },
    onError: (err: any) => {
      toast.error(err.message || "Failed to resolve dispute")
    },
  })

  const escalateOverdueMutation = useMutation({
    mutationFn: (bookingId: string) => api.post(`/admin/overdue/${bookingId}/escalate`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-overdue"] })
      queryClient.invalidateQueries({ queryKey: ["admin-dashboard"] })
      toast.success("Overdue booking escalated to dispute arbitration")
    },
  })

  return (
    <div className="space-y-8">
      {/* Header Banner */}
      <div className="bg-white border border-slate-200/90 rounded-2xl p-6 shadow-xs flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold text-slate-900">
              Availo Institutional Administrative Console
            </h1>
            <span className="bg-purple-100 text-purple-800 text-[10px] font-extrabold px-2.5 py-0.5 rounded-full uppercase tracking-wider">
              Admin Privilege
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Identity verification queues, escrow arbitration, overdue equipment recovery, and audit tracking.
          </p>
        </div>

        {/* Console Tabs */}
        <div className="flex gap-1.5 bg-slate-100 p-1 rounded-xl text-xs font-semibold">
          {[
            { key: "OVERVIEW", label: "Overview" },
            { key: "VERIFICATIONS", label: `Verifications (${verifications.length})` },
            { key: "DISPUTES", label: `Disputes (${disputes.length})` },
          ].map((t) => (
            <button
              key={t.key}
              onClick={() => setActiveTab(t.key as any)}
              className={`px-3 py-1.5 rounded-lg transition ${
                activeTab === t.key
                  ? "bg-white text-slate-900 shadow-xs"
                  : "text-slate-600 hover:text-slate-900"
              }`}
            >
              {t.label}
            </button>
          ))}
        </div>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-white border border-slate-200/90 rounded-2xl p-5 shadow-xs">
          <span className="text-xs text-slate-500 font-medium block">Pending Badges</span>
          <span className="text-2xl font-black text-amber-600 mt-1 block">
            {stats?.pending_verifications ?? 0}
          </span>
        </div>
        <div className="bg-white border border-slate-200/90 rounded-2xl p-5 shadow-xs">
          <span className="text-xs text-slate-500 font-medium block">Open Disputes</span>
          <span className="text-2xl font-black text-rose-600 mt-1 block">
            {stats?.open_disputes ?? 0}
          </span>
        </div>
        <div className="bg-white border border-slate-200/90 rounded-2xl p-5 shadow-xs">
          <span className="text-xs text-slate-500 font-medium block">Active Bookings</span>
          <span className="text-2xl font-black text-blue-600 mt-1 block">
            {stats?.active_bookings ?? 0}
          </span>
        </div>
        <div className="bg-white border border-slate-200/90 rounded-2xl p-5 shadow-xs">
          <span className="text-xs text-slate-500 font-medium block">Overdue Returns</span>
          <span className="text-2xl font-black text-slate-900 mt-1 block">
            {stats?.overdue_returns ?? 0}
          </span>
        </div>
      </div>

      {/* Verification Queue Section */}
      {(activeTab === "OVERVIEW" || activeTab === "VERIFICATIONS") && (
        <div className="bg-white border border-slate-200/90 rounded-2xl p-6 shadow-xs space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100">
            <div className="flex items-center gap-2">
              <ShieldCheck className="w-5 h-5 text-purple-600" />
              <h3 className="font-bold text-slate-900 text-sm">
                Identity & Researcher Verification Queue
              </h3>
            </div>
            <span className="text-xs text-slate-500 font-medium">
              {verifications.length} submissions pending
            </span>
          </div>

          {verifications.length === 0 ? (
            <p className="text-xs text-slate-400 py-6 text-center">
              All submitted credentials and researcher badges have been reviewed.
            </p>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {verifications.map((v) => (
                <div
                  key={v.id}
                  className="p-4 border border-slate-200 rounded-xl bg-slate-50 space-y-3"
                >
                  <div className="flex justify-between items-center text-xs">
                    <span className="font-bold text-slate-800">Badge: {v.badge_type}</span>
                    <span className="bg-amber-100 text-amber-800 px-2 py-0.5 rounded font-semibold text-[10px]">
                      PENDING REVIEW
                    </span>
                  </div>

                  <div className="text-xs text-slate-600 bg-white p-2.5 rounded-lg border border-slate-200 truncate flex items-center justify-between">
                    <span className="truncate">Document: {v.document_url}</span>
                    <a
                      href={v.document_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-blue-600 ml-2 hover:underline shrink-0"
                    >
                      <ExternalLink className="w-3.5 h-3.5" />
                    </a>
                  </div>

                  <div className="flex justify-end gap-2 pt-2 border-t border-slate-200">
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => rejectBadgeMutation.mutate(v.id)}
                      loading={rejectBadgeMutation.isPending}
                      className="text-rose-600 border-rose-200 hover:bg-rose-50"
                    >
                      <X className="w-3.5 h-3.5 mr-1" /> Reject
                    </Button>
                    <Button
                      size="sm"
                      onClick={() => approveBadgeMutation.mutate(v.id)}
                      loading={approveBadgeMutation.isPending}
                    >
                      <Check className="w-3.5 h-3.5 mr-1" /> Approve & Issue Badge
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Escrow Dispute Arbitration Section */}
      {(activeTab === "OVERVIEW" || activeTab === "DISPUTES") && (
        <div className="bg-white border border-slate-200/90 rounded-2xl p-6 shadow-xs space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100">
            <div className="flex items-center gap-2">
              <ShieldAlert className="w-5 h-5 text-rose-600" />
              <h3 className="font-bold text-slate-900 text-sm">
                Escrow Dispute Arbitration Queue
              </h3>
            </div>
            <span className="text-xs text-slate-500 font-medium">
              {disputes.length} open cases
            </span>
          </div>

          {disputes.length === 0 ? (
            <p className="text-xs text-slate-400 py-6 text-center">
              No open condition discrepancies or escrow disputes under arbitration.
            </p>
          ) : (
            <div className="space-y-4">
              {disputes.map((d) => (
                <div
                  key={d.id}
                  className="p-5 border border-rose-200 rounded-xl bg-rose-50/30 space-y-4"
                >
                  <div className="flex justify-between items-center text-xs">
                    <div>
                      <span className="font-bold text-rose-900 text-sm">
                        Booking Case #{d.booking_id.slice(0, 8)}
                      </span>
                      <span className="text-slate-500 block mt-0.5">
                        Status: {d.status.replace(/_/g, " ")}
                      </span>
                    </div>
                    <span className="bg-rose-100 text-rose-800 px-2.5 py-1 rounded font-bold text-xs">
                      DISPUTE OPEN
                    </span>
                  </div>

                  {/* Render assessments if present */}
                  {d.assessments && d.assessments.length > 0 && (
                    <div className="text-xs text-slate-700 bg-white p-3 rounded-lg border border-rose-100">
                      <span className="font-semibold block mb-1">AI Inspection Findings:</span>
                      <ul className="list-disc list-inside space-y-0.5 text-slate-600">
                        {d.assessments.map((a: any) => (
                          <li key={a.id}>
                            Angle {a.angle}: {a.anomalies?.join(", ") || "Visual anomaly flagged"}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  <div className="flex flex-wrap gap-2 justify-end pt-3 border-t border-rose-200">
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() =>
                        setDisputeToResolve({ bookingId: d.booking_id, outcome: "OWNER" })
                      }
                    >
                      Release Escrow to Owner
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() =>
                        setDisputeToResolve({ bookingId: d.booking_id, outcome: "SPLIT" })
                      }
                    >
                      50 / 50 Split Determination
                    </Button>
                    <Button
                      size="sm"
                      variant="secondary"
                      onClick={() =>
                        setDisputeToResolve({ bookingId: d.booking_id, outcome: "USER" })
                      }
                    >
                      Refund Borrower In Full
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Confirmation Modal for Consequential Dispute Determination */}
      <ConfirmationDialog
        isOpen={Boolean(disputeToResolve)}
        title="Confirm Administrative Escrow Resolution"
        description={`Are you sure you want to execute the outcome "${disputeToResolve?.outcome}" for booking #${disputeToResolve?.bookingId.slice(
          0,
          8
        )}? This action settles escrow funds irrevocably.`}
        confirmText="Execute Settlement"
        variant="primary"
        loading={resolveDisputeMutation.isPending}
        onConfirm={() => {
          if (disputeToResolve) {
            resolveDisputeMutation.mutate(disputeToResolve)
          }
        }}
        onCancel={() => setDisputeToResolve(null)}
      />
    </div>
  )
}
