"use client"

import React, { useState } from "react"
import { useRouter, useParams } from "next/navigation"
import { useResource, useResourceEligibility } from "@/hooks/useResource"
import { useCreateBooking } from "@/hooks/useBooking"
import { EligibilityGate } from "@/components/resource/EligibilityGate"
import { Button } from "@/components/ui/Button"
import { Input, Textarea } from "@/components/ui/Input"
import { Alert } from "@/components/ui/Alert"
import { Skeleton } from "@/components/ui/Skeleton"
import { formatCurrency } from "@/lib/utils"
import {
  MapPin,
  Calendar,
  Clock,
  FileCheck,
  Building,
  Info,
  ChevronLeft,
  CheckCircle2,
} from "lucide-react"
import Link from "next/link"
import toast from "react-hot-toast"

export default function ResourceDetailPage() {
  const params = useParams()
  const router = useRouter()
  const id = params?.id as string

  const { data: resource, isLoading } = useResource(id)
  const { data: eligibility } = useResourceEligibility(id)
  const createBookingMutation = useCreateBooking()

  const [selectedImageIdx, setSelectedImageIdx] = useState(0)
  const [startDt, setStartDt] = useState("")
  const [endDt, setEndDt] = useState("")
  const [purpose, setPurpose] = useState("")

  if (isLoading || !resource) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-8 w-40 rounded-lg" />
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <Skeleton className="lg:col-span-2 h-96 rounded-2xl" />
          <Skeleton className="h-96 rounded-2xl" />
        </div>
      </div>
    )
  }

  // Calculate reservation day count and total estimates
  const start = startDt ? new Date(startDt).getTime() : null
  const end = endDt ? new Date(endDt).getTime() : null
  const durationDays =
    start && end && end > start
      ? Math.max(1, Math.ceil((end - start) / (1000 * 60 * 60 * 24)))
      : 1
  const estimatedRental = Number(resource.daily_rate) * durationDays
  const deposit = Number(resource.deposit_amount)
  const totalDue = estimatedRental + deposit

  const isDateInvalid = Boolean(start && end && end <= start)

  const handleBooking = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!startDt || !endDt) {
      toast.error("Please specify both start and end reservation dates")
      return
    }
    if (isDateInvalid) {
      toast.error("End date must be after the reservation start date")
      return
    }

    try {
      const res: any = await createBookingMutation.mutateAsync({
        resource_id: id,
        start_dt: new Date(startDt).toISOString(),
        end_dt: new Date(endDt).toISOString(),
        purpose: purpose.trim() || "Institutional research and evaluation",
      })
      toast.success("Booking request submitted for owner approval!")
      router.push(`/bookings/${res.id}`)
    } catch (err: any) {
      toast.error(err.message || "Failed to submit booking request")
    }
  }

  const galleryImages =
    resource.images && resource.images.length > 0
      ? resource.images
      : [
          {
            id: "fallback",
            url: "https://images.unsplash.com/photo-1581092160607-ee22621dd758?auto=format&fit=crop&w=1200&q=80",
            angle: "FRONT",
            is_primary: true,
          },
        ]

  const activeImage = galleryImages[selectedImageIdx] || galleryImages[0]

  return (
    <div className="space-y-6">
      {/* Back button */}
      <Link
        href="/resources"
        className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-slate-900 transition"
      >
        <ChevronLeft className="w-4 h-4" />
        Back to Resources
      </Link>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* Left Column: Gallery, Specs & Rules */}
        <div className="lg:col-span-7 space-y-6">
          {/* Main Gallery */}
          <div className="bg-white border border-slate-200/90 rounded-2xl overflow-hidden shadow-xs">
            <div className="relative aspect-[16/10] bg-slate-900 overflow-hidden">
              <img
                src={activeImage.url}
                alt={resource.title}
                className="w-full h-full object-cover"
              />
              <span className="absolute bottom-3 left-3 bg-slate-900/80 backdrop-blur-xs text-white text-xs px-2.5 py-1 rounded-md font-mono">
                Angle: {activeImage.angle || "PRIMARY"}
              </span>
            </div>

            {/* Gallery Thumbnails */}
            {galleryImages.length > 1 && (
              <div className="p-3 bg-slate-50 flex gap-2 overflow-x-auto border-t border-slate-200">
                {galleryImages.map((img, idx) => (
                  <button
                    key={img.id || idx}
                    type="button"
                    onClick={() => setSelectedImageIdx(idx)}
                    className={`relative w-20 h-14 rounded-lg overflow-hidden border-2 transition shrink-0 ${
                      selectedImageIdx === idx ? "border-blue-600 ring-2 ring-blue-100" : "border-slate-200 opacity-70 hover:opacity-100"
                    }`}
                  >
                    <img src={img.url} alt={`Thumbnail ${idx}`} className="w-full h-full object-cover" />
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Detailed Specifications */}
          <div className="bg-white border border-slate-200/90 rounded-2xl p-6 shadow-xs space-y-6">
            <div>
              <div className="flex items-center gap-2 mb-2">
                <span className="bg-blue-50 text-blue-700 text-xs font-semibold px-2.5 py-0.5 rounded-full border border-blue-200/60">
                  {resource.category.replace(/_/g, " ")}
                </span>
                <span className="text-xs text-slate-400">·</span>
                <span className="text-xs text-slate-500 font-medium flex items-center gap-1">
                  <Building className="w-3.5 h-3.5 text-slate-400" />
                  Institutional Asset
                </span>
              </div>
              <h1 className="text-2xl font-extrabold text-slate-900">{resource.title}</h1>
              <p className="text-xs text-slate-500 flex items-center gap-1.5 mt-1.5">
                <MapPin className="w-4 h-4 text-slate-400 shrink-0" />
                {resource.location}
              </p>
            </div>

            <div className="space-y-2 border-t border-slate-100 pt-4">
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400">
                About this Equipment
              </h3>
              <p className="text-sm text-slate-700 leading-relaxed whitespace-pre-line">
                {resource.description}
              </p>
            </div>

            {/* Quick Meta Cards */}
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 pt-2">
              <div className="p-3 bg-slate-50 rounded-xl border border-slate-200/60">
                <span className="text-[10px] text-slate-400 font-semibold uppercase block">
                  Condition Rating
                </span>
                <span className="text-xs font-bold text-slate-800 flex items-center gap-1.5 mt-1">
                  <FileCheck className="w-4 h-4 text-emerald-600" />
                  {resource.condition || "EXCELLENT"}
                </span>
              </div>

              <div className="p-3 bg-slate-50 rounded-xl border border-slate-200/60">
                <span className="text-[10px] text-slate-400 font-semibold uppercase block">
                  Max Reservation
                </span>
                <span className="text-xs font-bold text-slate-800 flex items-center gap-1.5 mt-1">
                  <Clock className="w-4 h-4 text-blue-600" />
                  {resource.max_booking_days || 14} Days
                </span>
              </div>

              <div className="p-3 bg-slate-50 rounded-xl border border-slate-200/60 col-span-2 sm:col-span-1">
                <span className="text-[10px] text-slate-400 font-semibold uppercase block">
                  Fair-Use Policy
                </span>
                <span className="text-xs font-bold text-slate-800 mt-1 block">
                  {resource.fair_use_limit_per_week || 2} bookings/week
                </span>
              </div>
            </div>

            {/* Institutional Rules & Guidelines */}
            <div className="border-t border-slate-100 pt-4 space-y-2 text-xs text-slate-600">
              <h4 className="font-bold text-slate-800">Borrowing Guidelines & Terms</h4>
              <ul className="list-disc list-inside space-y-1 text-slate-600">
                <li>Check-in condition baseline requires all 6 canonical photo angles.</li>
                <li>Refundable escrow deposit is held securely until return inspection.</li>
                <li>Gemini visual AI compares return photos against check-in photos.</li>
              </ul>
            </div>
          </div>
        </div>

        {/* Right Column: Eligibility Gate + Booking Request Form */}
        <div className="lg:col-span-5 space-y-6 sticky top-24">
          {/* Eligibility status */}
          {eligibility && (
            <EligibilityGate
              eligible={eligibility.eligible}
              missingBadges={eligibility.missing_badges}
              reason={eligibility.reason}
            />
          )}

          {/* Pricing & Booking Card */}
          <div className="bg-white border border-slate-200/90 rounded-2xl p-6 shadow-xs space-y-6">
            <div className="flex justify-between items-baseline pb-4 border-b border-slate-100">
              <div>
                <span className="text-2xl font-black text-slate-900">
                  {formatCurrency(resource.daily_rate)}
                </span>
                <span className="text-xs text-slate-500 font-medium"> / day</span>
              </div>
              <div className="text-right">
                <span className="text-xs text-slate-500 block">Security Deposit</span>
                <span className="text-xs font-bold text-slate-800">
                  {formatCurrency(resource.deposit_amount)}
                </span>
              </div>
            </div>

            <form onSubmit={handleBooking} className="space-y-4">
              <Input
                label="Start Date & Time"
                type="datetime-local"
                required
                value={startDt}
                onChange={(e) => setStartDt(e.target.value)}
              />

              <Input
                label="End Date & Time"
                type="datetime-local"
                required
                value={endDt}
                error={isDateInvalid ? "End date must be strictly after start date" : undefined}
                onChange={(e) => setEndDt(e.target.value)}
              />

              <Textarea
                label="Intended Research / Project Purpose"
                rows={3}
                required
                value={purpose}
                onChange={(e) => setPurpose(e.target.value)}
                placeholder="State your institutional project or experiment requirements..."
                helperText="Required for owner approval review and audit logging"
              />

              {/* Fee Breakdown */}
              {start && end && !isDateInvalid && (
                <div className="bg-slate-50 rounded-xl p-3.5 border border-slate-200/60 space-y-2 text-xs">
                  <div className="flex justify-between text-slate-600">
                    <span>
                      Daily Rate × {durationDays} {durationDays === 1 ? "day" : "days"}:
                    </span>
                    <span className="font-semibold text-slate-800">
                      {formatCurrency(estimatedRental)}
                    </span>
                  </div>
                  <div className="flex justify-between text-slate-600">
                    <span>Refundable Escrow Deposit:</span>
                    <span className="font-semibold text-slate-800">
                      {formatCurrency(deposit)}
                    </span>
                  </div>
                  <div className="pt-2 border-t border-slate-200 flex justify-between text-sm font-bold text-slate-900">
                    <span>Total Initial Authorization:</span>
                    <span className="text-blue-600">{formatCurrency(totalDue)}</span>
                  </div>
                </div>
              )}

              {eligibility?.eligible === false && (
                <Alert variant="warning" title="Access Gate Restricted">
                  You are not yet eligible to book this equipment. Please verify your institution badge or complete the prerequisite training.
                </Alert>
              )}

              <Button
                type="submit"
                className="w-full py-3"
                disabled={eligibility?.eligible === false || isDateInvalid || createBookingMutation.isPending}
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
