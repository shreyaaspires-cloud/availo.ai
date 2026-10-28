import React from "react"
import { cn } from "@/lib/utils"

export const Skeleton: React.FC<{ className?: string }> = ({ className }) => {
  return (
    <div
      className={cn("animate-pulse rounded-lg bg-slate-200/80", className)}
      aria-hidden="true"
    />
  )
}
