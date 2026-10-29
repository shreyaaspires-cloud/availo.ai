import React from "react"
import { useQuery } from "@tanstack/react-query"
import { api } from "@/lib/api"
import { SignatureCapture } from "./SignatureCapture"
import { useAuth } from "@/hooks/useAuth"
import { FileText, CheckCircle2, Copy, Download } from "lucide-react"
import toast from "react-hot-toast"

interface ContractViewerProps {
  bookingId: string
  onRefetchBooking?: () => void
}

export const ContractViewer: React.FC<ContractViewerProps> = ({ bookingId, onRefetchBooking }) => {
  const { user } = useAuth()
  const { data: contract, isLoading, refetch } = useQuery<any>({
    queryKey: ["contract", bookingId],
    queryFn: () => api.get(`/contracts/${bookingId}`),
  })

  if (isLoading) {
    return <div className="p-6 text-center text-sm text-gray-500">Generating plain-English contract via Gemini AI...</div>
  }

  if (!contract) {
    return <div className="p-4 text-center text-sm text-gray-500">No contract found for this reservation.</div>
  }

  const signatures = contract.signatures || []
  const hasUserSigned = signatures.some((s: any) => s.user_id === user?.id)
  const isFullySigned = contract.status === "SIGNED"

  const handleCopyHash = () => {
    if (contract.sha256_hash) {
      navigator.clipboard.writeText(contract.sha256_hash)
      toast.success("SHA-256 hash copied to clipboard")
    }
  }

  return (
    <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm space-y-6">
      <div className="flex justify-between items-center pb-4 border-b border-gray-100">
        <div className="flex items-center gap-2">
          <FileText className="w-5 h-5 text-blue-600" />
          <h3 className="font-bold text-gray-900 text-base">Resource Sharing Agreement</h3>
        </div>
        {isFullySigned ? (
          <span className="flex items-center gap-1.5 bg-emerald-100 text-emerald-800 text-xs px-2.5 py-1 rounded-full font-semibold">
            <CheckCircle2 className="w-4 h-4 text-emerald-600" /> Fully Executed
          </span>
        ) : (
          <span className="bg-amber-100 text-amber-800 text-xs px-2.5 py-1 rounded-full font-semibold">
            Awaiting Signatures
          </span>
        )}
      </div>

      {/* Contract HTML Preview */}
      <div
        className="max-h-96 overflow-y-auto p-4 bg-gray-50 rounded-lg border border-gray-200 text-sm leading-relaxed prose max-w-none"
        dangerouslySetInnerHTML={{ __html: contract.content_html }}
      />

      {/* SHA256 & Cryptographic Proof */}
      <div className="bg-gray-50 p-3 rounded-lg flex items-center justify-between text-xs">
        <div className="truncate mr-2">
          <span className="font-semibold text-gray-700">Document SHA-256: </span>
          <span className="font-mono text-gray-600">{contract.sha256_hash || "Generating..."}</span>
        </div>
        <button
          onClick={handleCopyHash}
          className="p-1 hover:bg-gray-200 rounded text-gray-600 transition shrink-0"
          title="Copy Hash"
        >
          <Copy className="w-4 h-4" />
        </button>
      </div>

      {/* Signature Status */}
      <div className="grid grid-cols-2 gap-3 text-xs">
        <div className="p-3 border border-gray-200 rounded-lg">
          <span className="text-gray-500 block">User Signature</span>
          <span className="font-semibold text-gray-800">
            {signatures.some((s: any) => s.role_in_contract === "USER") ? "Signed ✓" : "Pending Signature"}
          </span>
        </div>
        <div className="p-3 border border-gray-200 rounded-lg">
          <span className="text-gray-500 block">Owner Signature</span>
          <span className="font-semibold text-gray-800">
            {signatures.some((s: any) => s.role_in_contract === "OWNER") ? "Signed ✓" : "Pending Signature"}
          </span>
        </div>
      </div>

      {/* Signature Capture Pad if user has not yet signed */}
      {!hasUserSigned && contract.status !== "SIGNED" && (
        <SignatureCapture
          contractId={contract.id}
          onSigned={() => {
            refetch()
            onRefetchBooking?.()
          }}
        />
      )}
    </div>
  )
}
