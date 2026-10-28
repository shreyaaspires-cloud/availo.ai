import React from "react"
import Link from "next/link"
import { MapPin, ShieldCheck, Clock } from "lucide-react"
import { ResourceItem } from "@/hooks/useResource"
import { formatCurrency } from "@/lib/utils"

export const ResourceCard: React.FC<{ resource: ResourceItem }> = ({ resource }) => {
  const primaryImg =
    resource.images?.find((img) => img.is_primary)?.url ||
    resource.images?.[0]?.url ||
    "https://images.unsplash.com/photo-1581092160607-ee22621dd758?auto=format&fit=crop&w=800&q=80"

  const hasResearcherRequirement = resource.requires_badge?.includes("RESEARCHER")

  return (
    <div className="bg-white border border-gray-200 rounded-xl overflow-hidden hover:shadow-md transition flex flex-col group">
      <div className="relative aspect-[16/10] bg-gray-100 overflow-hidden">
        <img
          src={primaryImg}
          alt={resource.title}
          className="w-full h-full object-cover group-hover:scale-105 transition duration-300"
        />
        <div className="absolute top-3 left-3 flex gap-1.5 flex-wrap">
          <span className="bg-white/90 backdrop-blur-sm text-xs font-semibold px-2 py-0.5 rounded text-gray-800 shadow-sm">
            {resource.category.replace(/_/g, " ")}
          </span>
          {hasResearcherRequirement && (
            <span className="bg-purple-600 text-white text-xs font-semibold px-2 py-0.5 rounded shadow-sm flex items-center gap-1">
              <ShieldCheck className="w-3 h-3" />
              Verified Researcher
            </span>
          )}
        </div>
        <div className="absolute bottom-3 right-3 bg-black/60 backdrop-blur-sm text-white text-xs px-2 py-0.5 rounded flex items-center gap-1">
          <span className="w-2 h-2 rounded-full bg-emerald-400"></span>
          Available
        </div>
      </div>

      <div className="p-4 flex-1 flex flex-col justify-between">
        <div>
          <h3 className="font-semibold text-gray-900 text-base line-clamp-1">
            {resource.title}
          </h3>
          <p className="text-gray-500 text-xs flex items-center gap-1 mt-1">
            <MapPin className="w-3.5 h-3.5 text-gray-400" />
            {resource.location}
          </p>
          <p className="text-gray-600 text-xs mt-2 line-clamp-2">
            {resource.description}
          </p>
        </div>

        <div className="mt-4 pt-3 border-t border-gray-100 flex items-center justify-between">
          <div>
            <div className="text-base font-bold text-gray-900">
              {formatCurrency(resource.daily_rate)}
              <span className="text-xs font-normal text-gray-500">/day</span>
            </div>
            <div className="text-[11px] text-gray-500">
              Deposit: {formatCurrency(resource.deposit_amount)}
            </div>
          </div>

          <Link
            href={`/resources/${resource.id}`}
            className="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white text-xs font-medium rounded-lg transition"
          >
            View & Book
          </Link>
        </div>
      </div>
    </div>
  )
}
