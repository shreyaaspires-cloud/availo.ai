import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { api } from "@/lib/api"

export type BookingStatus =
  | "DRAFT"
  | "PENDING_APPROVAL"
  | "APPROVED"
  | "REJECTED"
  | "WAITLISTED"
  | "AWAITING_SIGNATURES"
  | "AWAITING_PAYMENT"
  | "CONFIRMED"
  | "CHECKED_IN"
  | "RETURN_SUBMITTED"
  | "DAMAGE_REVIEW"
  | "DISPUTE_OPEN"
  | "RESOLVED_OWNER"
  | "RESOLVED_USER"
  | "RESOLVED_SPLIT"
  | "COMPLETED"
  | "CANCELLED"

export interface BookingItem {
  id: string
  resource_id: string
  user_id: string
  status: BookingStatus
  start_dt: string
  end_dt: string
  purpose: string
  total_amount: string | number
  deposit_amount: string | number
  cancellation_reason?: string
  rejection_reason?: string
  payment_reference?: string
  created_at: string
}

export function useBookings() {
  return useQuery<BookingItem[]>({
    queryKey: ["bookings"],
    queryFn: () => api.get("/bookings"),
    staleTime: 10000,
  })
}

export function useBooking(id: string, refetchInterval: number | false = 10000) {
  return useQuery<BookingItem>({
    queryKey: ["booking", id],
    queryFn: () => api.get(`/bookings/${id}`),
    enabled: !!id,
    refetchInterval,
  })
}

export function useCreateBooking() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: {
      resource_id: string
      start_dt: string
      end_dt: string
      purpose: string
    }) => api.post("/bookings", data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["bookings"] })
    },
  })
}

export function useApproveBooking() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => api.post(`/bookings/${id}/approve`),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: ["booking", id] })
      queryClient.invalidateQueries({ queryKey: ["bookings"] })
    },
  })
}

export function useRejectBooking() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, reason }: { id: string; reason: string }) =>
      api.post(`/bookings/${id}/reject`, { reason }),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: ["booking", id] })
      queryClient.invalidateQueries({ queryKey: ["bookings"] })
    },
  })
}

export function useConfirmPayment() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({
      id,
      razorpay_payment_id,
    }: {
      id: string
      razorpay_payment_id: string
    }) => api.post(`/bookings/${id}/confirm-payment`, { razorpay_payment_id }),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: ["booking", id] })
      queryClient.invalidateQueries({ queryKey: ["bookings"] })
    },
  })
}
