import React from "react"
import { X } from "lucide-react"
import { Button } from "./Button"

export interface ConfirmationDialogProps {
  isOpen: boolean
  title: string
  description: string
  confirmText?: string
  cancelText?: string
  variant?: "danger" | "primary"
  loading?: boolean
  onConfirm: () => void
  onCancel: () => void
}

export const ConfirmationDialog: React.FC<ConfirmationDialogProps> = ({
  isOpen,
  title,
  description,
  confirmText = "Confirm",
  cancelText = "Cancel",
  variant = "primary",
  loading = false,
  onConfirm,
  onCancel,
}) => {
  if (!isOpen) return null

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs transition-opacity"
      role="dialog"
      aria-modal="true"
    >
      <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-xl border border-slate-100 space-y-4 animate-in fade-in zoom-in-95 duration-150">
        <div className="flex justify-between items-start">
          <h3 className="text-base font-bold text-slate-900">{title}</h3>
          <button
            onClick={onCancel}
            disabled={loading}
            className="text-slate-400 hover:text-slate-600 rounded-lg p-1 -mr-1 -mt-1 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <p className="text-xs text-slate-600 leading-relaxed">{description}</p>

        <div className="flex items-center justify-end gap-2 pt-2 border-t border-slate-100">
          <Button variant="ghost" size="sm" onClick={onCancel} disabled={loading}>
            {cancelText}
          </Button>
          <Button
            variant={variant === "danger" ? "danger" : "primary"}
            size="sm"
            onClick={onConfirm}
            loading={loading}
          >
            {confirmText}
          </Button>
        </div>
      </div>
    </div>
  )
}
