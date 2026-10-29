"use client"

import React, { useState, useEffect } from "react"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { api } from "@/lib/api"
import { useNotificationStore } from "@/store/notificationStore"
import { EmptyState } from "@/components/ui/EmptyState"
import { Skeleton } from "@/components/ui/Skeleton"
import { formatDate } from "@/lib/utils"
import Link from "next/link"
import { Bell, CheckCheck, ExternalLink, Calendar, ShieldCheck, AlertTriangle } from "lucide-react"

export default function NotificationsPage() {
  const [mounted, setMounted] = useState(false)
  useEffect(() => {
    setMounted(true)
  }, [])

  const queryClient = useQueryClient()
  const { setNotifications } = useNotificationStore()

  const { data: serverNotifications = [], isLoading } = useQuery<any[]>({
    queryKey: ["notifications"],
    queryFn: () => api.get("/notifications"),
    refetchInterval: 15000,
  })

  useEffect(() => {
    if (serverNotifications.length) {
      setNotifications(serverNotifications)
    }
  }, [serverNotifications, setNotifications])

  const markReadMutation = useMutation({
    mutationFn: (id: string) => api.patch(`/notifications/${id}/read`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["notifications"] })
    },
  })

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white border border-slate-200/90 rounded-2xl p-6 shadow-xs flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">
            Notifications & System Alerts
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            Real-time updates regarding booking status changes, condition inspections, and badge approvals.
          </p>
        </div>
        <div className="w-10 h-10 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center">
          <Bell className="w-5 h-5" />
        </div>
      </div>

      {/* List */}
      {!mounted || isLoading ? (
        <div className="space-y-3">
          {[1, 2, 3, 4].map((n) => (
            <div key={n} className="bg-white border border-slate-200 rounded-2xl p-5 space-y-2">
              <Skeleton className="h-5 w-48 rounded" />
              <Skeleton className="h-4 w-full rounded" />
            </div>
          ))}
        </div>
      ) : serverNotifications.length === 0 ? (
        <EmptyState
          icon={Bell}
          title="No notifications"
          description="You are completely caught up. Updates on active reservations, approvals and inspections will appear here in real-time."
        />
      ) : (
        <div className="space-y-3">
          {serverNotifications.map((notif) => {
            const isRead = notif.is_read

            return (
              <div
                key={notif.id}
                className={`border rounded-2xl p-5 transition flex items-start justify-between gap-4 ${
                  isRead
                    ? "bg-white border-slate-200/80"
                    : "bg-blue-50/40 border-blue-200 shadow-xs"
                }`}
              >
                <div className="space-y-1.5 flex-1">
                  <div className="flex items-center gap-2">
                    {!isRead && (
                      <span className="w-2 h-2 rounded-full bg-blue-600 shrink-0" />
                    )}
                    <h4 className="font-bold text-sm text-slate-900">{notif.title}</h4>
                    <span className="text-[10px] text-slate-400">
                      {formatDate(notif.created_at)}
                    </span>
                  </div>

                  <p className="text-xs text-slate-600 leading-relaxed">{notif.body}</p>

                  {notif.booking_id && (
                    <div className="pt-2">
                      <Link
                        href={`/bookings/${notif.booking_id}`}
                        className="text-xs font-semibold text-blue-600 hover:text-blue-700 inline-flex items-center gap-1 transition"
                      >
                        <span>Open Booking Reference</span>
                        <ExternalLink className="w-3.5 h-3.5" />
                      </Link>
                    </div>
                  )}
                </div>

                {!isRead && (
                  <button
                    onClick={() => markReadMutation.mutate(notif.id)}
                    className="p-1.5 text-slate-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition shrink-0"
                    title="Mark as read"
                  >
                    <CheckCheck className="w-4 h-4" />
                  </button>
                )}
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
