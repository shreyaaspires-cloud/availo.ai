"use client"

import React, { useState } from "react"
import { useRouter, useParams } from "next/navigation"
import { useResource, useResourceEligibility } from "@/hooks/useResource"
import { useCreateBooking } from "@/hooks/useBooking"
import { EligibilityGate } from "@/components/resource/EligibilityGate"
import { Button } from "@/components/ui/Button"
import { formatCurrency } from "@/lib/utils"
import { MapPin, Calendar, ShieldCheck, Clock, FileCheck } from "lucide-react"
import toast from "react-hot-toast"

export default function ResourceDetailPage() {
  const params = useParams()
  const router = useRouter()
  const id = params?.id as string

  const { data: resource, isLoading } = useResource(id)
  const { data: eligibility } = useResourceEligibility(id)
  const createBookingMutation = useCreateBooking()

  const [startDt, setStartDt] = useState("")
  const [endDt, setEndDt] = useState("")
  const [purpose, setPurpose] = useState("")

  if (isLoading || !resource) {
    return <div className="p-12 text-center text-sm text-gray-500">Loading resource specifications...</div>
  }

  const handleBooking = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!startDt || !endDt) {
      toast.error("Please select start and end reservation dates")
      return
    }

    try {
      const res: any = await createBookingMutation.mutateAsync({
        resource_id: id,
        start_dt: new Date(startDt).toISOString(),
        end_dt: new Date(endDt).toISOString(),
        purpose: purpose || "Academic/institutional project research",
      })
      toast.success("Booking request submitted!")
      router.push(`/bookings/${res.id}`)
    } catch (err: any) {
      toast.error(err.message || "Failed to submit booking")
    }
  }

  const primaryImg =
    resource.images?.find((i) => i.is_primary)?.url ||
    resource.images?.[0]?.url ||
    "https://images.unsplash.com/photo-1581092160607-ee22621dd758?auto=format&fit=crop&w=800&q=80"

  return (
    <div className="space-y-8">
      {/* Top Banner & Images */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2 space-y-6">
          <div className="bg-white border border-gray-200 rounded-2xl overflow-hidden shadow-sm">
            <img
              src={primaryImg}
              alt={resource.title}
              className="w-full h-80 object-cover"
            />
            {resource.images?.length > 1 && (
              <div className="p-3 bg-gray-50 flex gap-2 overflow-x-auto border-t border-gray-200">
                {resource.images.map((img) => (
                  <img
                    key={img.id}
                    src={img.url}
                    alt={img.angle}
                    className="w-16 h-12 object-cover rounded border border-gray-200"
                  />
                ))}
              </div>
            )}
          </div>

          <div className="bg-white border border-gray-200 rounded-2xl p-6 shadow-sm space-y-4">
            <div>
              <span className="bg-blue-50 text-blue-700 text-xs font-semibold px-2.5 py-0.5 rounded-full">
                {resource.category.replace(/_/g, " ")}
              </span>
              <h1 className="text-2xl font-bold text-gray-900 mt-2">{resource.title}</h1>
              <p className="text-xs text-gray-500 flex items-center gap-1 mt-1">
                <MapPin className="w-3.5 h-3.5 text-gray-400" />
                {resource.location}
              </p>
            </div>

            <p className="text-sm text-gray-700 leading-relaxed">{resource.description}</p>

            <div className="pt-4 border-t border-gray-100 flex items-center gap-6 text-xs text-gray-600">
              <span className="flex items-center gap-1.5">
                <FileCheck className="w-4 h-4 text-emerald-600" />
                Condition: {resource.condition}
              </span>
              <span className="flex items-center gap-1.5">
                <Clock className="w-4 h-4 text-blue-600" />
                Max Booking: {resource.max_booking_days} Days
              </span>
            </div>
          </div>
        </div>

        {/* Right Action & Eligibility Gate */}
        <div className="space-y-6">
          {eligibility && (
            <EligibilityGate
              eligible={eligibility.eligible}
              missingBadges={eligibility.missing_badges}
              reason={eligibility.reason}
            />
          )}

          <div className="bg-white border border-gray-200 rounded-2xl p-6 shadow-sm space-y-5">
            <div className="flex justify-between items-baseline pb-4 border-b border-gray-100">
              <div>
                <span className="text-2xl font-extrabold text-gray-900">
                  {formatCurrency(resource.daily_rate)}
                </span>
                <span className="text-xs text-gray-500 font-normal"> / day</span>
              </div>
              <div className="text-xs text-gray-500 text-right">
                Deposit: {formatCurrency(resource.deposit_amount)}
              </div>
            </div>

            <form onSubmit={handleBooking} className="space-y-4">
              <div>
                <label className="text-xs font-semibold text-gray-700 block mb-1">Start Date & Time</label>
                <input
                  type="datetime-local"
                  required
                  value={startDt}
                  onChange={(e) => setStartDt(e.target.value)}
                  className="w-full bg-gray-50 border border-gray-200 rounded-lg px-3 py-2 text-xs text-gray-800 focus:outline-none focus:ring-1 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="text-xs font-semibold text-gray-700 block mb-1">End Date & Time</label>
                <input
                  type="datetime-local"
                  required
                  value={endDt}
                  onChange={(e) => setEndDt(e.target.value)}
                  className="w-full bg-gray-50 border border-gray-200 rounded-lg px-3 py-2 text-xs text-gray-800 focus:outline-none focus:ring-1 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="text-xs font-semibold text-gray-700 block mb-1">Project Purpose</label>
                <textarea
                  rows={3}
                  value={purpose}
                  onChange={(e) => setPurpose(e.target.value)}
                  placeholder="Outline intended institutional/research use..."
                  className="w-full bg-gray-50 border border-gray-200 rounded-lg p-2.5 text-xs text-gray-800 focus:outline-none focus:ring-1 focus:ring-blue-500"
                />
              </div>

              <Button
                type="submit"
                className="w-full"
                disabled={eligibility?.eligible === false || createBookingMutation.isPending}
                loading={createBookingMutation.isPending}
              >
                Request Booking
              </Button>
            </form>
          </div>
        </div>
      </div>
    </div>
  )
}
