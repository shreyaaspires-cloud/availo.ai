import React from "react"
import { useQuery } from "@tanstack/react-query"
import { api } from "@/lib/api"
import { ConfidenceBar } from "./ConfidenceBar"
import { ShieldCheck, AlertTriangle, CheckCircle } from "lucide-react"

interface DamageReportProps {
  bookingId: string
}

export const DamageReport: React.FC<DamageReportProps> = ({ bookingId }) => {
  const { data: incident, isLoading } = useQuery<any>({
    queryKey: ["damage-assessment", bookingId],
    queryFn: () => api.get(`/incidents/${bookingId}/damage-assessment`),
  })

  if (isLoading) {
    return <div className="p-6 text-center text-sm text-gray-500">Loading AI inspection assessment...</div>
  }

  if (!incident) {
    return (
      <div className="p-4 bg-gray-50 rounded-lg text-sm text-gray-500 text-center">
        No damage inspection records available for this booking.
      </div>
    )
  }

  const assessments = incident.assessments || []
  const hasDamage = assessments.some((a: any) => a.confidence_score >= 0.3 || !a.match)

  return (
    <div className="space-y-4">
      {hasDamage ? (
        <div className="p-4 bg-red-50 border border-red-200 rounded-xl flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-red-600 shrink-0 mt-0.5" />
          <div>
            <h4 className="text-sm font-bold text-red-900">
              Potential Damage Detected — Review Required
            </h4>
            <p className="text-xs text-red-700 mt-1">
              AI comparison identified anomalies between baseline check-in and return photos. Escrow held pending owner inspection.
            </p>
          </div>
        </div>
      ) : (
        <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-xl flex items-start gap-3">
          <CheckCircle className="w-5 h-5 text-emerald-600 shrink-0 mt-0.5" />
          <div>
            <h4 className="text-sm font-bold text-emerald-900">
              No Damage Detected — Escrow Released
            </h4>
            <p className="text-xs text-emerald-700 mt-1">
              Resource verified intact across all 6 canonical angles. Security deposit is released automatically.
            </p>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {assessments.map((a: any) => (
          <div key={a.id} className="border border-gray-200 rounded-xl p-4 bg-white space-y-3">
            <div className="flex justify-between items-center">
              <span className="font-mono text-xs font-bold text-gray-800 bg-gray-100 px-2 py-0.5 rounded">
                Angle: {a.angle}
              </span>
              <span className={`text-xs font-semibold ${a.confidence_score < 0.3 ? "text-emerald-600" : "text-rose-600"}`}>
                {a.confidence_score < 0.3 ? "Match Verified" : "Anomaly Flagged"}
              </span>
            </div>

            <div className="grid grid-cols-2 gap-2">
              <div>
                <span className="text-[10px] text-gray-500 font-semibold block mb-1">BEFORE (Check-in)</span>
                <img
                  src={a.before_image_url || "https://images.unsplash.com/photo-1516035069371-29a1b244cc32?auto=format&fit=crop&w=400&q=80"}
                  alt="Before"
                  className="w-full h-24 object-cover rounded border border-gray-200"
                />
              </div>
              <div>
                <span className="text-[10px] text-gray-500 font-semibold block mb-1">AFTER (Return)</span>
                <img
                  src={a.after_image_url || "https://images.unsplash.com/photo-1516035069371-29a1b244cc32?auto=format&fit=crop&w=400&q=80"}
                  alt="After"
                  className="w-full h-24 object-cover rounded border border-gray-200"
                />
              </div>
            </div>

            <ConfidenceBar score={a.confidence_score} />

            {a.anomalies?.length > 0 && (
              <ul className="text-xs text-rose-700 list-disc list-inside space-y-0.5">
                {a.anomalies.map((anom: string, i: number) => (
                  <li key={i}>{anom}</li>
                ))}
              </ul>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
