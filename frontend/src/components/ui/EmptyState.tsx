import React from "react"
import { LucideIcon, Sparkles } from "lucide-react"
import { cn } from "@/lib/utils"

export interface EmptyStateProps {
  icon?: LucideIcon
  title: string
  description?: string
  action?: React.ReactNode
  className?: string
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  icon: Icon = Sparkles,
  title,
  description,
  action,
  className,
}) => {
  return (
    <div
      className={cn(
        "rounded-2xl border border-slate-200/80 bg-white p-12 text-center shadow-sm flex flex-col items-center justify-center space-y-3",
        className
      )}
    >
      <div className="w-12 h-12 rounded-full bg-slate-100 flex items-center justify-center text-slate-400 mb-1">
        <Icon className="w-6 h-6" />
      </div>
      <h3 className="text-sm font-semibold text-slate-800">{title}</h3>
      {description && (
        <p className="text-xs text-slate-500 max-w-sm mx-auto leading-relaxed">{description}</p>
      )}
      {action && <div className="pt-2">{action}</div>}
    </div>
  )
}
