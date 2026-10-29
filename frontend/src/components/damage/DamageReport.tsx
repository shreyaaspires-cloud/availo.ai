import React from "react"
import { useQuery } from "@tanstack/react-query"
import { api } from "@/lib/api"
import { ConfidenceBar } from "./ConfidenceBar"
import { Alert } from "@/components/ui/Alert"
import { Skeleton } from "@/components/ui/Skeleton"
import { ShieldCheck, AlertTriangle, CheckCircle, Info, ImageOff, UserCheck } from "lucide-react"

interface DamageReportProps {
  bookingId: string
  bookingStatus?: string
}

export const DamageReport: React.FC<DamageReportProps> = ({ bookingId, bookingStatus }) => {
  const { data: incident, isLoading } = useQuery<any>({
    queryKey: ["damage-assessment", bookingId],
    queryFn: () => api.get(`/incidents/${bookingId}/damage-assessment`),
  })

  if (isLoading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-16 w-full rounded-xl" />
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Skeleton className="h-64 rounded-xl" />
          <Skeleton className="h-64 rounded-xl" />
        </div>
      </div>
    )
  }

  if (!incident) {
    return (
      <div className="p-8 bg-slate-50 border border-slate-200/80 rounded-2xl text-center space-y-2">
        <Info className="w-6 h-6 text-slate-400 mx-auto" />
        <h4 className="text-sm font-semibold text-slate-800">Inspection in queue</h4>
        <p className="text-xs text-slate-500 max-w-sm mx-auto">
          Condition inspection records will appear once return photos are processed by Gemini Vision AI.
        </p>
      </div>
    )
  }

  const assessments = incident.assessments || []
  const hasDamage = assessments.some((a: any) => a.confidence_score >= 0.3 || !a.match)
  const isResolved = incident.status === "RESOLVED" || bookingStatus?.startsWith("RESOLVED_") || bookingStatus === "COMPLETED"

  return (
    <div className="space-y-6">
      {/* Banner matching precise backend state */}
      {incident.status === "UNDER_REVIEW" || incident.status === "OPEN" ? (
        <Alert variant="warning" title="Possible change — review required">
          AI visual comparison detected potential condition anomalies or angle discrepancies. The
          reservation is under owner condition review. Escrow remains secured in holding until
          determination.
        </Alert>
      ) : isResolved && !hasDamage ? (
        <Alert variant="success" title="No obvious change detected — Escrow Released">
          The equipment was verified undamaged across all canonical perspectives. Escrow deposit has
          been released back to the borrower.
        </Alert>
      ) : isResolved && hasDamage ? (
        <Alert variant="info" title="Arbitration Completed">
          The condition report has been resolved. Outcome: {incident.resolution_note || "Settled by administrator"}.
        </Alert>
      ) : (
        <Alert variant="info" title="AI analysis complete — awaiting determination">
          Visual comparison completed. Human review pending for final escrow authorization.
        </Alert>
      )}

      {/* Side-by-side Before/After Angle Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        {assessments.map((a: any) => {
          const isAnomaly = a.confidence_score >= 0.3 || !a.match
          const statusText = isAnomaly
            ? "Possible change — review required"
            : "No obvious change detected"

          return (
            <div
              key={a.id}
              className="border border-slate-200 rounded-2xl p-4 bg-white shadow-xs space-y-4 hover:border-slate-300 transition"
            >
              <div className="flex justify-between items-center pb-2 border-b border-slate-100">
                <span className="font-mono text-xs font-bold text-slate-900 bg-slate-100 px-2.5 py-1 rounded-md">
                  Angle: {a.angle}
                </span>
                <span
                  className={`text-xs font-semibold px-2 py-0.5 rounded-full ${
                    isAnomaly
                      ? "bg-amber-50 text-amber-800 border border-amber-200"
                      : "bg-emerald-50 text-emerald-800 border border-emerald-200"
                  }`}
                >
                  {statusText}
                </span>
              </div>

              {/* Side-by-Side Images */}
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1">
                  <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider block">
                    Check-in (Baseline)
                  </span>
                  <div className="relative aspect-[4/3] rounded-lg overflow-hidden bg-slate-100 border border-slate-200">
                    {a.before_image_url ? (
                      <img
                        src={a.before_image_url}
                        alt={`Check-in ${a.angle}`}
                        className="w-full h-full object-cover"
                      />
                    ) : (
                      <div className="w-full h-full flex items-center justify-center text-slate-400 text-xs">
                        <ImageOff className="w-5 h-5" />
                      </div>
                    )}
                  </div>
                </div>

                <div className="space-y-1">
                  <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider block">
                    Check-out (Return)
                  </span>
                  <div className="relative aspect-[4/3] rounded-lg overflow-hidden bg-slate-100 border border-slate-200">
                    {a.after_image_url ? (
                      <img
                        src={a.after_image_url}
                        alt={`Return ${a.angle}`}
                        className="w-full h-full object-cover"
                      />
                    ) : (
                      <div className="w-full h-full flex items-center justify-center text-slate-400 text-xs">
                        <ImageOff className="w-5 h-5" />
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {/* Anomaly list */}
              {a.anomalies && a.anomalies.length > 0 && (
                <div className="p-3 bg-amber-50/70 border border-amber-200/80 rounded-xl space-y-1">
                  <span className="text-[11px] font-bold text-amber-900 block">
                    Observed Anomalies:
                  </span>
                  <ul className="text-xs text-amber-800 list-disc list-inside space-y-0.5">
                    {a.anomalies.map((anom: string, i: number) => (
                      <li key={i}>{anom}</li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Confidence metric with plain wording */}
              <div className="space-y-1 pt-1">
                <div className="flex justify-between text-[11px]">
                  <span className="text-slate-500">Visual Similarity Match</span>
                  <span className="font-bold text-slate-800">
                    {Math.round((1 - (a.confidence_score || 0)) * 100)}%
                  </span>
                </div>
                <div className="w-full bg-slate-100 h-1.5 rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full transition-all ${
                      isAnomaly ? "bg-amber-500" : "bg-emerald-500"
                    }`}
                    style={{
                      width: `${Math.round((1 - (a.confidence_score || 0)) * 100)}%`,
                    }}
                  />
                </div>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
