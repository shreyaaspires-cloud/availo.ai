import React, { useState } from "react"
import Link from "next/link"
import { MapPin, ShieldCheck, ArrowRight, ImageOff } from "lucide-react"
import { ResourceItem } from "@/hooks/useResource"
import { formatCurrency } from "@/lib/utils"

export const ResourceCard: React.FC<{ resource: ResourceItem }> = ({ resource }) => {
  const [imageError, setImageError] = useState(false)

  const primaryImg =
    resource.images?.find((img) => img.is_primary)?.url ||
    resource.images?.[0]?.url ||
    "https://images.unsplash.com/photo-1581092160607-ee22621dd758?auto=format&fit=crop&w=800&q=80"

  const hasResearcherRequirement = resource.requires_badge?.includes("RESEARCHER")

  return (
    <div className="bg-white border border-slate-200/90 rounded-2xl overflow-hidden hover:shadow-md hover:border-slate-300 transition flex flex-col group">
      {/* Image container */}
      <div className="relative aspect-[16/10] bg-slate-100 overflow-hidden">
        {!imageError ? (
          <img
            src={primaryImg}
            alt={resource.title}
            onError={() => setImageError(true)}
            className="w-full h-full object-cover group-hover:scale-103 transition duration-300"
          />
        ) : (
          <div className="w-full h-full flex flex-col items-center justify-center text-slate-400 gap-1 bg-slate-50">
            <ImageOff className="w-6 h-6 stroke-[1.5]" />
            <span className="text-[11px] font-medium">Equipment Preview</span>
          </div>
        )}

        {/* Category & Badge pills */}
        <div className="absolute top-3 left-3 flex gap-1.5 flex-wrap">
          <span className="bg-white/95 backdrop-blur-xs text-xs font-semibold px-2.5 py-0.5 rounded-full text-slate-800 shadow-xs border border-slate-200/60">
            {resource.category.replace(/_/g, " ")}
          </span>
          {hasResearcherRequirement && (
            <span className="bg-purple-600/95 backdrop-blur-xs text-white text-[11px] font-semibold px-2 py-0.5 rounded-full shadow-xs flex items-center gap-1">
              <ShieldCheck className="w-3 h-3" />
              Verified
            </span>
          )}
        </div>

        {/* Confirmation status pill */}
        <div className="absolute bottom-3 right-3 bg-slate-900/80 backdrop-blur-xs text-white text-[11px] font-medium px-2.5 py-0.5 rounded-full flex items-center gap-1.5 shadow-xs">
          <span
            className={`w-1.5 h-1.5 rounded-full ${
              resource.is_active ? "bg-emerald-400" : "bg-slate-400"
            }`}
          />
          {resource.is_active ? "Active Pool" : "Inactive"}
        </div>
      </div>

      {/* Content */}
      <div className="p-4 flex-1 flex flex-col justify-between space-y-3">
        <div>
          <h3 className="font-bold text-slate-900 text-sm line-clamp-1 group-hover:text-blue-600 transition">
            {resource.title}
          </h3>
          <p className="text-slate-500 text-xs flex items-center gap-1 mt-1">
            <MapPin className="w-3.5 h-3.5 text-slate-400 shrink-0" />
            <span className="truncate">{resource.location}</span>
          </p>
          <p className="text-slate-600 text-xs mt-2 line-clamp-2 leading-relaxed">
            {resource.description}
          </p>
        </div>

        {/* Pricing and single obvious primary CTA */}
        <div className="pt-3 border-t border-slate-100 flex items-center justify-between gap-2">
          <div>
            <div className="text-base font-extrabold text-slate-900">
              {formatCurrency(resource.daily_rate)}
              <span className="text-xs font-normal text-slate-500"> /day</span>
            </div>
            <div className="text-[11px] text-slate-500">
              Deposit: {formatCurrency(resource.deposit_amount)}
            </div>
          </div>

          <Link
            href={`/resources/${resource.id}`}
            className="px-3.5 py-2 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold rounded-xl flex items-center gap-1.5 shadow-xs transition"
          >
            <span>View Resource</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>
      </div>
    </div>
  )
}
