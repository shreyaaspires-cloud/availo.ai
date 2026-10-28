import React from "react"
import { AlertCircle, AlertTriangle, CheckCircle, Info, X } from "lucide-react"
import { cn } from "@/lib/utils"

export interface AlertProps {
  variant?: "info" | "success" | "warning" | "error"
  title?: string
  children: React.ReactNode
  className?: string
  onClose?: () => void
}

const variants = {
  info: {
    container: "bg-blue-50 border-blue-200 text-blue-900",
    icon: <Info className="w-5 h-5 text-blue-600 shrink-0 mt-0.5" />,
  },
  success: {
    container: "bg-emerald-50 border-emerald-200 text-emerald-900",
    icon: <CheckCircle className="w-5 h-5 text-emerald-600 shrink-0 mt-0.5" />,
  },
  warning: {
    container: "bg-amber-50 border-amber-200 text-amber-900",
    icon: <AlertTriangle className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />,
  },
  error: {
    container: "bg-rose-50 border-rose-200 text-rose-900",
    icon: <AlertCircle className="w-5 h-5 text-rose-600 shrink-0 mt-0.5" />,
  },
}

export const Alert: React.FC<AlertProps> = ({
  variant = "info",
  title,
  children,
  className,
  onClose,
}) => {
  const current = variants[variant]

  return (
    <div
      role="alert"
      className={cn(
        "rounded-xl border p-4 text-xs transition flex items-start gap-3 relative",
        current.container,
        className
      )}
    >
      {current.icon}
      <div className="flex-1 space-y-0.5">
        {title && <h5 className="font-semibold text-sm leading-tight">{title}</h5>}
        <div className="leading-relaxed opacity-95">{children}</div>
      </div>
      {onClose && (
        <button
          onClick={onClose}
          className="text-slate-400 hover:text-slate-600 p-1 -mr-1 -mt-1 rounded-md transition"
          aria-label="Dismiss alert"
        >
          <X className="w-4 h-4" />
        </button>
      )}
    </div>
  )
}
