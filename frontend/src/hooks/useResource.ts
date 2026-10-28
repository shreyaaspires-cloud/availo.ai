import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { api } from "@/lib/api"

export interface ResourceImage {
  id: string
  url: string
  angle: "FRONT" | "BACK" | "LEFT" | "RIGHT" | "TOP" | "BOTTOM"
  is_primary: boolean
}

export interface ResourceItem {
  id: string
  owner_id: string
  title: string
  description: string
  category: string
  location: string
  daily_rate: string | number
  deposit_amount: string | number
  max_booking_days: number
  requires_badge: string[]
  condition: string
  is_active: boolean
  fair_use_limit_per_week: number
  images: ResourceImage[]
  created_at: string
}

export interface ResourceFilters {
  search?: string
  category?: string
  location?: string
  date_start?: string
  date_end?: string
  badge_required?: string
  max_daily_rate?: number
}

export function useResources(filters: ResourceFilters = {}) {
  return useQuery<ResourceItem[]>({
    queryKey: ["resources", filters],
    queryFn: () => api.get("/resources", filters),
    staleTime: 30000,
  })
}

export function useResource(id: string) {
  return useQuery<ResourceItem>({
    queryKey: ["resource", id],
    queryFn: () => api.get(`/resources/${id}`),
    enabled: !!id,
  })
}

export function useResourceEligibility(id: string) {
  return useQuery<{ eligible: boolean; missing_badges: string[]; reason: string }>({
    queryKey: ["resource-eligibility", id],
    queryFn: () => api.get(`/resources/${id}/eligibility`),
    enabled: !!id,
  })
}

export function useCreateResource() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: any) => api.post("/resources", data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["resources"] })
    },
  })
}
