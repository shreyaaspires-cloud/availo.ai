import React from "react"
import { CheckCircle2, XCircle, ShieldAlert } from "lucide-react"

interface EligibilityGateProps {
  eligible: boolean
  missingBadges: string[]
  reason?: string
}

export const EligibilityGate: React.FC<EligibilityGateProps> = ({
  eligible,
  missingBadges,
  reason,
}) => {
  if (eligible) {
    return (
      <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-lg flex items-start gap-2.5">
        <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0 mt-0.5" />
        <div>
          <h4 className="text-sm font-semibold text-emerald-900">
            Eligibility Confirmed
          </h4>
          <p className="text-xs text-emerald-700 mt-0.5">
            Your verified institutional badges satisfy all access credentials for this resource.
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="p-3 bg-rose-50 border border-rose-200 rounded-lg flex items-start gap-2.5">
      <XCircle className="w-5 h-5 text-rose-600 shrink-0 mt-0.5" />
      <div>
        <h4 className="text-sm font-semibold text-rose-900">
          Restricted Resource Access
        </h4>
        <p className="text-xs text-rose-700 mt-0.5">
          {reason || "You are currently missing required verified badges to book this equipment."}
        </p>
        {missingBadges.length > 0 && (
          <div className="mt-2 flex gap-1.5 flex-wrap">
            {missingBadges.map((badge) => (
              <span
                key={badge}
                className="bg-rose-100 text-rose-800 text-[11px] font-medium px-2 py-0.5 rounded border border-rose-200"
              >
                Missing: {badge}
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
