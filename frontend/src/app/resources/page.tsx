"use client"

import React, { useState } from "react"
import { useResources } from "@/hooks/useResource"
import { ResourceCard } from "@/components/resource/ResourceCard"
import { Search, Filter, SlidersHorizontal, Sparkles } from "lucide-react"

export default function ResourcesPage() {
  const [searchTerm, setSearchTerm] = useState("")
  const [category, setCategory] = useState("")
  const [maxRate, setMaxRate] = useState<number | undefined>(undefined)

  const { data: resources = [], isLoading } = useResources({
    search: searchTerm || undefined,
    category: category || undefined,
    max_daily_rate: maxRate,
  })

  return (
    <div className="space-y-6">
      {/* Header and Search */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 bg-white border border-gray-200 p-6 rounded-2xl shadow-sm">
        <div>
          <h1 className="text-2xl font-extrabold text-gray-900 tracking-tight">Institutional Resources</h1>
          <p className="text-xs text-gray-500 mt-1">Discover, verify credentials, and book high-precision equipment</p>
        </div>

        <div className="flex items-center gap-3 w-full md:w-auto">
          <div className="relative flex-1 md:w-80">
            <Search className="w-4 h-4 text-gray-400 absolute left-3 top-2.5" />
            <input
              type="text"
              placeholder="Search electron microscope, 3D printer, camera..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full bg-gray-50 border border-gray-200 rounded-lg pl-9 pr-3 py-1.5 text-xs focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Filters Sidebar */}
        <div className="bg-white border border-gray-200 rounded-2xl p-5 shadow-sm space-y-6 h-fit">
          <div className="flex items-center justify-between border-b border-gray-100 pb-3">
            <h3 className="text-sm font-bold text-gray-800 flex items-center gap-2">
              <SlidersHorizontal className="w-4 h-4 text-gray-500" /> Filters
            </h3>
            {(category || maxRate) && (
              <button
                onClick={() => {
                  setCategory("")
                  setMaxRate(undefined)
                }}
                className="text-xs text-blue-600 font-semibold hover:underline"
              >
                Reset
              </button>
            )}
          </div>

          <div>
            <label className="text-xs font-semibold text-gray-700 block mb-2">Category</label>
            <select
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              className="w-full bg-gray-50 border border-gray-200 rounded-lg px-2.5 py-1.5 text-xs text-gray-700 focus:outline-none focus:ring-1 focus:ring-blue-500"
            >
              <option value="">All Categories</option>
              <option value="LABORATORY_EQUIPMENT">Laboratory Equipment</option>
              <option value="FABRICATION">Fabrication & 3D Printing</option>
              <option value="MEDIA">Media & Sensors</option>
            </select>
          </div>

          <div>
            <label className="text-xs font-semibold text-gray-700 block mb-2">
              Max Daily Rate {maxRate ? `(₹${maxRate})` : ""}
            </label>
            <input
              type="range"
              min={100}
              max={1000}
              step={50}
              value={maxRate || 1000}
              onChange={(e) => setMaxRate(Number(e.target.value))}
              className="w-full accent-blue-600 cursor-pointer"
            />
            <div className="flex justify-between text-[10px] text-gray-400 mt-1">
              <span>₹100</span>
              <span>₹1,000+</span>
            </div>
          </div>
        </div>

        {/* Results Grid */}
        <div className="lg:col-span-3">
          {isLoading ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {[1, 2, 3, 4, 5, 6].map((n) => (
                <div key={n} className="h-64 bg-gray-100 rounded-xl animate-pulse" />
              ))}
            </div>
          ) : resources.length === 0 ? (
            <div className="bg-white border border-gray-200 rounded-2xl p-12 text-center space-y-3">
              <Sparkles className="w-8 h-8 text-gray-300 mx-auto" />
              <h3 className="text-sm font-semibold text-gray-700">No resources found</h3>
              <p className="text-xs text-gray-400">Try adjusting your search criteria or category filters.</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
              {resources.map((item) => (
                <ResourceCard key={item.id} resource={item} />
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
