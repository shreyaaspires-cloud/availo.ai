import Link from "next/link"
import { ShieldCheck, Cpu, ArrowRight, Zap, CheckCircle2 } from "lucide-react"

export default function HomePage() {
  return (
    <div className="space-y-16 py-8">
      {/* Hero section */}
      <div className="text-center max-w-3xl mx-auto space-y-6">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-50 border border-blue-200 text-blue-700 text-xs font-semibold">
          <Zap className="w-3.5 h-3.5 text-blue-600" />
          Zero-Dispute Institutional Resource Sharing
        </div>
        <h1 className="text-4xl sm:text-5xl font-extrabold text-slate-900 tracking-tight leading-tight">
          Share Labs, Sensors & Specialized Gear with Confidence
        </h1>
        <p className="text-base sm:text-lg text-slate-600 leading-relaxed">
          Availo protects high-value institutional assets with 6-angle automated AI damage inspection, smart digital legal contracts, and escrow deposit guarantees.
        </p>
        <div className="flex items-center justify-center gap-4 pt-2">
          <Link
            href="/resources"
            className="px-6 py-3 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-semibold text-sm shadow-md hover:shadow-lg transition flex items-center gap-2"
          >
            Explore Resources <ArrowRight className="w-4 h-4" />
          </Link>
          <Link
            href="/dashboard"
            className="px-6 py-3 rounded-xl bg-white hover:bg-gray-50 border border-gray-300 text-slate-700 font-semibold text-sm transition"
          >
            Owner Dashboard
          </Link>
        </div>
      </div>

      {/* Feature Pillars */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 pt-6">
        <div className="bg-white border border-gray-200 rounded-2xl p-6 shadow-sm space-y-3">
          <div className="w-10 h-10 rounded-lg bg-blue-100 text-blue-600 flex items-center justify-center">
            <Cpu className="w-5 h-5" />
          </div>
          <h3 className="font-bold text-gray-900 text-base">Gemini 2.0 Vision AI</h3>
          <p className="text-xs text-gray-500 leading-relaxed">
            6-angle canonical photo capture at check-in & return. AI inspects scratches, cracks, and missing parts in a single API batch.
          </p>
        </div>

        <div className="bg-white border border-gray-200 rounded-2xl p-6 shadow-sm space-y-3">
          <div className="w-10 h-10 rounded-lg bg-emerald-100 text-emerald-600 flex items-center justify-center">
            <ShieldCheck className="w-5 h-5" />
          </div>
          <h3 className="font-bold text-gray-900 text-base">Cryptographic Contracts</h3>
          <p className="text-xs text-gray-500 leading-relaxed">
            Plain-English rental contracts auto-drafted by AI, rendered into immutable PDF artifacts with SHA-256 tamper-proof verification.
          </p>
        </div>

        <div className="bg-white border border-gray-200 rounded-2xl p-6 shadow-sm space-y-3">
          <div className="w-10 h-10 rounded-lg bg-purple-100 text-purple-600 flex items-center justify-center">
            <CheckCircle2 className="w-5 h-5" />
          </div>
          <h3 className="font-bold text-gray-900 text-base">Verified Badge Access</h3>
          <p className="text-xs text-gray-500 leading-relaxed">
            Gate precision equipment to verified Researchers, Faculty, or Professionals with automated credential validation.
          </p>
        </div>
      </div>
    </div>
  )
}
