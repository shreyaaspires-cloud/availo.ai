"use client"

import React, { useState, useEffect } from "react"
import { useResources } from "@/hooks/useResource"
import { ResourceCard } from "@/components/resource/ResourceCard"
import { EmptyState } from "@/components/ui/EmptyState"
import { Skeleton } from "@/components/ui/Skeleton"
import { Button } from "@/components/ui/Button"
import { Search, SlidersHorizontal, RotateCcw, Box } from "lucide-react"

export default function ResourcesPage() {
  const [mounted, setMounted] = useState(false)
  useEffect(() => {
    setMounted(true)
  }, [])

  const [searchInput, setSearchInput] = useState("")
  const [debouncedSearch, setDebouncedSearch] = useState("")
  const [category, setCategory] = useState("")
  const [location, setLocation] = useState("")
  const [maxRate, setMaxRate] = useState<number | undefined>(undefined)

  // 300ms debounce on search input
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearch(searchInput.trim())
    }, 300)
    return () => clearTimeout(timer)
  }, [searchInput])

  const { data: resources = [], isLoading } = useResources({
    search: debouncedSearch || undefined,
    category: category || undefined,
    location: location || undefined,
    max_daily_rate: maxRate,
  })

  const hasActiveFilters = Boolean(searchInput || category || location || maxRate)

  const clearAllFilters = () => {
    setSearchInput("")
    setDebouncedSearch("")
    setCategory("")
    setLocation("")
    setMaxRate(undefined)
  }

  return (
    <div className="space-y-6">
      {/* Page Heading & Search Bar */}
      <div className="bg-white border border-slate-200/90 p-6 md:p-8 rounded-2xl shadow-xs space-y-4">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl md:text-3xl font-extrabold text-slate-900 tracking-tight">
              Find a Resource
            </h1>
            <p className="text-sm text-slate-500 mt-1 max-w-2xl leading-relaxed">
              Borrow laboratory equipment, 3D printers, microscopy platforms, and media hardware
              from accredited institutional laboratories with automated AI damage inspection.
            </p>
          </div>
        </div>

        {/* Prominent Search Bar */}
        <div className="relative pt-2">
          <Search className="w-5 h-5 text-slate-400 absolute left-3.5 top-5" />
          <input
            type="text"
            placeholder="Search equipment by title, specification or model (e.g., 'Microscope', '3D Printer', 'Oscilloscope')..."
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            className="w-full bg-slate-50 border border-slate-200 hover:border-slate-300 rounded-xl pl-11 pr-4 py-3 text-sm text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-600 focus:bg-white transition"
          />
        </div>
      </div>

      {/* Main Grid: Filters Sidebar + Results */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 items-start">
        {/* Filters Sidebar */}
        <div className="bg-white border border-slate-200/90 rounded-2xl p-5 shadow-xs space-y-6 sticky top-24">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <h3 className="text-sm font-bold text-slate-800 flex items-center gap-2">
              <SlidersHorizontal className="w-4 h-4 text-slate-500" /> Filters
            </h3>
            {hasActiveFilters && (
              <button
                onClick={clearAllFilters}
                className="text-xs text-blue-600 hover:text-blue-700 font-semibold flex items-center gap-1 transition"
              >
                <RotateCcw className="w-3 h-3" />
                Clear
              </button>
            )}
          </div>

          {/* Category Filter */}
          <div>
            <label className="text-xs font-semibold text-slate-700 block mb-1.5">Category</label>
            <select
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-xs text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-600 focus:bg-white transition"
            >
              <option value="">All Categories</option>
              <option value="LABORATORY_EQUIPMENT">Laboratory Equipment</option>
              <option value="FABRICATION">Fabrication & 3D Printing</option>
              <option value="MEDIA">Media & Sensors</option>
            </select>
          </div>

          {/* Location Filter */}
          <div>
            <label className="text-xs font-semibold text-slate-700 block mb-1.5">Location / Campus</label>
            <input
              type="text"
              placeholder="e.g., Block B, Nanotech Lab"
              value={location}
              onChange={(e) => setLocation(e.target.value)}
              className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-xs text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-600 focus:bg-white transition"
            />
          </div>

          {/* Price Range Slider */}
          <div>
            <div className="flex justify-between items-center mb-1.5">
              <label className="text-xs font-semibold text-slate-700">Max Daily Rate</label>
              <span className="text-xs font-bold text-blue-600">
                {maxRate ? `₹${maxRate}` : "Any Rate"}
              </span>
            </div>
            <input
              type="range"
              min={100}
              max={3000}
              step={100}
              value={maxRate || 3000}
              onChange={(e) => setMaxRate(Number(e.target.value))}
              className="w-full accent-blue-600 cursor-pointer"
            />
            <div className="flex justify-between text-[10px] text-slate-400 mt-1">
              <span>₹100</span>
              <span>₹3,000+</span>
            </div>
          </div>
        </div>

        {/* Results Area */}
        <div className="lg:col-span-3 space-y-4">
          {/* Header count indicator */}
          <div className="flex items-center justify-between text-xs text-slate-500 px-1">
            <span>
              Showing <strong className="text-slate-800 font-bold">{resources.length}</strong> available{" "}
              {resources.length === 1 ? "resource" : "resources"}
            </span>
            {hasActiveFilters && (
              <span className="text-slate-400 italic">Filters currently applied</span>
            )}
          </div>

          {!mounted || isLoading ? (
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-5">
              {[1, 2, 3, 4, 5, 6].map((n) => (
                <div key={n} className="bg-white border border-slate-200 rounded-2xl p-4 space-y-3">
                  <Skeleton className="h-44 w-full rounded-xl" />
                  <Skeleton className="h-4 w-3/4 rounded" />
                  <Skeleton className="h-3 w-1/2 rounded" />
                  <div className="pt-3 border-t border-slate-100 flex justify-between items-center">
                    <Skeleton className="h-6 w-20 rounded" />
                    <Skeleton className="h-8 w-24 rounded-lg" />
                  </div>
                </div>
              ))}
            </div>
          ) : resources.length === 0 ? (
            <EmptyState
              icon={Box}
              title="No resources match your filters"
              description="Try adjusting your search query, location or maximum rate slider to see available institutional equipment."
              action={
                hasActiveFilters ? (
                  <Button variant="outline" size="sm" onClick={clearAllFilters}>
                    <RotateCcw className="w-3.5 h-3.5 mr-1" /> Clear All Filters
                  </Button>
                ) : undefined
              }
            />
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-5">
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
