import React, { useState } from "react"
import { useQuery } from "@tanstack/react-query"
import { api } from "@/lib/api"
import { Alert } from "@/components/ui/Alert"
import { Skeleton } from "@/components/ui/Skeleton"
import {
  ShieldCheck,
  AlertTriangle,
  CheckCircle2,
  Info,
  ImageOff,
  Eye,
  Crosshair,
  Sliders,
  Sparkles,
  HelpCircle,
  Camera,
  Layers,
} from "lucide-react"

interface DamageReportProps {
  bookingId: string
  bookingStatus?: string
}

export const DamageReport: React.FC<DamageReportProps> = ({ bookingId, bookingStatus }) => {
  const { data: incident, isLoading } = useQuery<any>({
    queryKey: ["damage-assessment", bookingId],
    queryFn: () => api.get(`/incidents/${bookingId}/damage-assessment`),
  })

  const [activeDiffTab, setActiveDiffTab] = useState<Record<string, "original" | "diff">>({})

  if (isLoading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-16 w-full rounded-2xl" />
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          <Skeleton className="h-72 rounded-2xl" />
          <Skeleton className="h-72 rounded-2xl" />
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
          Condition inspection records will appear once return photos are processed by Gemini Vision AI and the Explainable AI (XAI) engine.
        </p>
      </div>
    )
  }

  const assessments = incident.assessments || []
  const hasDamage = assessments.some(
    (a: any) => (a.confidence_score >= 0.25 || !a.match || a.human_review_required)
  )
  const isResolved =
    incident.status === "RESOLVED" ||
    incident.status === "RESOLVED_USER" ||
    incident.status === "RESOLVED_OWNER" ||
    incident.status === "RESOLVED_SPLIT" ||
    bookingStatus?.startsWith("RESOLVED_") ||
    bookingStatus === "COMPLETED"

  return (
    <div className="space-y-6">
      {/* Top Banner with Clear Human-Understandable Status */}
      {incident.status === "UNDER_REVIEW" || incident.status === "OPEN" ? (
        <Alert variant="warning" title="Possible change detected — Manual Review Required">
          Explainable AI comparison flagged potential condition discrepancies or perspective shifts. The reservation is under owner/admin review. Escrow deposit remains held safely in escrow.
        </Alert>
      ) : isResolved && !hasDamage ? (
        <Alert variant="success" title="No obvious damage detected — Escrow Released">
          The equipment was verified undamaged across all 6 canonical perspectives. Escrow deposit has been released to the borrower.
        </Alert>
      ) : isResolved && hasDamage ? (
        <Alert variant="info" title="Arbitration Completed">
          The condition report has been resolved. Note: {incident.resolution_note || "Settled by administrator"}.
        </Alert>
      ) : (
        <Alert variant="info" title="XAI Inspection Complete — Awaiting Verification">
          Visual comparison completed. Human review pending for final escrow authorization.
        </Alert>
      )}

      {/* Methodology & Limitations Notice */}
      <div className="bg-blue-50/70 border border-blue-200/80 rounded-2xl p-4 flex items-start gap-3 text-xs text-blue-900">
        <Sparkles className="w-5 h-5 text-blue-600 shrink-0 mt-0.5" />
        <div className="space-y-1">
          <p className="font-semibold text-blue-950">
            Explainable AI (XAI) Forensic Inspection Framework
          </p>
          <p className="text-blue-800 leading-relaxed">
            Availo pairs high-resolution Gemini Vision inspection with localized computer-vision difference heatmaps. Similarity metrics reflect pixel distribution fidelity (L1 difference) and do not represent damage probability. Difference images are diagnostic visual aids, not proof of liability.
          </p>
        </div>
      </div>

      {/* 6 Canonical Perspective Comparison Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        {assessments.map((a: any) => {
          const isAnomaly =
            (a.confidence_score >= 0.25 || !a.match || a.human_review_required)
          const currentTab = activeDiffTab[a.id] || (a.difference_image_url ? "diff" : "original")

          return (
            <div
              key={a.id}
              className="border border-slate-200 rounded-2xl p-5 bg-white shadow-xs space-y-4 hover:border-slate-300 transition"
            >
              {/* Card Header */}
              <div className="flex justify-between items-center pb-3 border-b border-slate-100">
                <div className="flex items-center gap-2">
                  <span className="font-mono text-xs font-bold text-slate-900 bg-slate-100 px-2.5 py-1 rounded-md">
                    Perspective: {a.angle}
                  </span>
                  <span className="text-[11px] text-slate-500 capitalize">
                    {a.comparison_status ? a.comparison_status.replace(/_/g, " ") : "Comparable"}
                  </span>
                </div>
                <span
                  className={`text-xs font-semibold px-2.5 py-0.5 rounded-full flex items-center gap-1 ${
                    isAnomaly
                      ? "bg-amber-50 text-amber-800 border border-amber-200"
                      : "bg-emerald-50 text-emerald-800 border border-emerald-200"
                  }`}
                >
                  {isAnomaly ? (
                    <>
                      <AlertTriangle className="w-3.5 h-3.5" /> Possible Change
                    </>
                  ) : (
                    <>
                      <CheckCircle2 className="w-3.5 h-3.5" /> Undamaged
                    </>
                  )}
                </span>
              </div>

              {/* View Switcher: Original Photos vs Difference Heatmap */}
              <div className="flex items-center justify-between text-xs">
                <span className="text-slate-500 font-medium">Evidence Viewer</span>
                <div className="inline-flex rounded-lg bg-slate-100 p-0.5 text-slate-600">
                  <button
                    type="button"
                    onClick={() => setActiveDiffTab((prev) => ({ ...prev, [a.id]: "original" }))}
                    className={`px-2.5 py-1 rounded-md font-medium text-xs transition ${
                      currentTab === "original"
                        ? "bg-white text-slate-900 shadow-xs"
                        : "hover:text-slate-900"
                    }`}
                  >
                    Original Photos
                  </button>
                  {a.difference_image_url && (
                    <button
                      type="button"
                      onClick={() => setActiveDiffTab((prev) => ({ ...prev, [a.id]: "diff" }))}
                      className={`px-2.5 py-1 rounded-md font-medium text-xs transition flex items-center gap-1 ${
                        currentTab === "diff"
                          ? "bg-blue-600 text-white shadow-xs"
                          : "hover:text-slate-900"
                      }`}
                    >
                      <Layers className="w-3 h-3" />
                      Difference Heatmap
                    </button>
                  )}
                </div>
              </div>

              {/* Photos or Heatmap Area */}
              {currentTab === "diff" && a.difference_image_url ? (
                <div className="space-y-1.5">
                  <div className="relative aspect-[16/10] rounded-xl overflow-hidden bg-slate-950 border border-slate-800">
                    <img
                      src={a.difference_image_url}
                      alt={`Difference heatmap for ${a.angle}`}
                      className="w-full h-full object-contain"
                    />
                  </div>
                  <p className="text-[11px] text-slate-500 italic">
                    Highlighted contours indicate localized pixel variance clusters against check-in baseline.
                  </p>
                </div>
              ) : (
                <div className="grid grid-cols-2 gap-3">
                  <div className="space-y-1">
                    <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider block">
                      Check-in (Baseline)
                    </span>
                    <div className="relative aspect-[4/3] rounded-xl overflow-hidden bg-slate-100 border border-slate-200">
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
                    <div className="relative aspect-[4/3] rounded-xl overflow-hidden bg-slate-100 border border-slate-200">
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
              )}

              {/* Explainability Breakdown Section */}
              <div className="bg-slate-50 rounded-xl p-3.5 space-y-2.5 text-xs border border-slate-100">
                {a.damage_category && a.damage_category !== "none" && (
                  <div className="flex items-center justify-between pb-1.5 border-b border-slate-200/60">
                    <span className="text-slate-500 font-medium">Suspected Category:</span>
                    <span className="font-semibold text-rose-700 uppercase tracking-wide bg-rose-50 px-2 py-0.5 rounded border border-rose-200">
                      {a.damage_category.replace(/_/g, " ")}
                    </span>
                  </div>
                )}

                {a.location_description && (
                  <div>
                    <span className="text-slate-500 font-medium block text-[11px] mb-0.5">
                      Suspected Location:
                    </span>
                    <p className="text-slate-800 font-medium">{a.location_description}</p>
                  </div>
                )}

                {a.supporting_evidence && (
                  <div>
                    <span className="text-slate-500 font-medium block text-[11px] mb-0.5">
                      Visual Evidence:
                    </span>
                    <p className="text-slate-700 leading-relaxed">{a.supporting_evidence}</p>
                  </div>
                )}

                {/* Alternative Explanations */}
                {a.alternative_explanations && a.alternative_explanations.length > 0 && (
                  <div className="pt-1">
                    <span className="text-amber-800 font-medium block text-[11px] mb-1">
                      Plausible Alternative Explanations:
                    </span>
                    <ul className="text-amber-900/80 list-disc list-inside space-y-0.5 text-[11px]">
                      {a.alternative_explanations.map((alt: string, idx: number) => (
                        <li key={idx}>{alt}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>

              {/* Similarity Metric & Algorithm Transparency */}
              <div className="space-y-1.5 pt-1">
                <div className="flex justify-between items-center text-[11px]">
                  <span className="text-slate-500">Visual Similarity Metric:</span>
                  <span className="font-bold text-slate-900">
                    {Math.round((a.similarity_metric ?? 1.0) * 100)}%
                  </span>
                </div>
                <div className="w-full bg-slate-100 h-2 rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full transition-all ${
                      (a.similarity_metric ?? 1.0) < 0.85 ? "bg-amber-500" : "bg-emerald-500"
                    }`}
                    style={{
                      width: `${Math.round((a.similarity_metric ?? 1.0) * 100)}%`,
                    }}
                  />
                </div>
                <p className="text-[10px] text-slate-400">
                  Algorithm: {a.similarity_algorithm || "Normalized Grayscale L1 Pixel Difference (PIL/OpenCV)"}
                </p>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
