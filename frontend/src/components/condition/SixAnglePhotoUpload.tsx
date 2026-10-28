import React, { useState } from "react"
import { useDropzone } from "react-dropzone"
import { Camera, Check, UploadCloud, AlertCircle } from "lucide-react"
import { api } from "@/lib/api"
import { Button } from "@/components/ui/Button"
import toast from "react-hot-toast"

const ANGLES = ["FRONT", "BACK", "LEFT", "RIGHT", "TOP", "BOTTOM"] as const
type Angle = typeof ANGLES[number]

interface SixAnglePhotoUploadProps {
  bookingId: string
  reportType: "CHECK_IN" | "CHECK_OUT"
  onComplete: () => void
}

export const SixAnglePhotoUpload: React.FC<SixAnglePhotoUploadProps> = ({
  bookingId,
  reportType,
  onComplete,
}) => {
  const [uploads, setUploads] = useState<Record<Angle, { file?: File; preview?: string; uploaded: boolean }>>({
    FRONT: { uploaded: false },
    BACK: { uploaded: false },
    LEFT: { uploaded: false },
    RIGHT: { uploaded: false },
    TOP: { uploaded: false },
    BOTTOM: { uploaded: false },
  })
  const [submitting, setSubmitting] = useState(false)

  const handleFileDrop = async (angle: Angle, files: File[]) => {
    if (!files.length) return
    const file = files[0]
    const preview = URL.createObjectURL(file)

    setUploads((prev) => ({
      ...prev,
      [angle]: { file, preview, uploaded: false },
    }))

    // Upload individual angle
    const formData = new FormData()
    formData.append("file", file)
    formData.append("report_type", reportType)
    formData.append("angle", angle)

    try {
      await api.post(`/conditions/${bookingId}/photos`, formData)
      setUploads((prev) => ({
        ...prev,
        [angle]: { file, preview, uploaded: true },
      }))
      toast.success(`${angle} photo uploaded`)
    } catch (err: any) {
      toast.error(`Failed to upload ${angle} photo`)
    }
  }

  const allComplete = ANGLES.every((angle) => uploads[angle].uploaded)

  const handleSubmitReport = async () => {
    if (!allComplete) return
    setSubmitting(true)
    try {
      if (reportType === "CHECK_IN") {
        await api.post(`/conditions/${bookingId}/checkin-complete`)
        toast.success("Check-in verified successfully!")
      } else {
        await api.post(`/conditions/${bookingId}/checkout-complete`)
        toast.success("Check-out submitted. AI Damage analysis running!")
      }
      onComplete()
    } catch (err: any) {
      toast.error(err.message || "Failed to submit condition report")
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
      <div className="mb-4">
        <h3 className="text-base font-bold text-gray-900 flex items-center gap-2">
          <Camera className="w-5 h-5 text-blue-600" />
          {reportType === "CHECK_IN" ? "Check-in Photo Inspection" : "Return & Check-out Inspection"}
        </h3>
        <p className="text-xs text-gray-500 mt-1">
          Capture all 6 canonical angles to calibrate AI tamper and baseline damage detection.
        </p>
      </div>

      <div className="grid grid-cols-2 md:grid_cols-3 gap-3">
        {ANGLES.map((angle) => {
          const slot = uploads[angle]
          return (
            <AngleDropzone
              key={angle}
              angle={angle}
              slot={slot}
              onDrop={(files) => handleFileDrop(angle, files)}
            />
          )
        })}
      </div>

      <div className="mt-6 flex items-center justify-between pt-4 border-t border-gray-100">
        <div className="text-xs text-gray-500">
          {ANGLES.filter((a) => uploads[a].uploaded).length} of 6 angles uploaded
        </div>

        <Button
          onClick={handleSubmitReport}
          disabled={!allComplete || submitting}
          loading={submitting}
        >
          {reportType === "CHECK_IN" ? "Complete Check-in" : "Submit Return for Inspection"}
        </Button>
      </div>
    </div>
  )
}

function AngleDropzone({
  angle,
  slot,
  onDrop,
}: {
  angle: string
  slot: { preview?: string; uploaded: boolean }
  onDrop: (files: File[]) => void
}) {
  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { "image/*": [".jpeg", ".jpg", ".png", ".webp"] },
    maxFiles: 1,
  })

  return (
    <div
      {...getRootProps()}
      className={`relative aspect-video rounded-lg border-2 border-dashed flex flex-col items-center justify-center p-2 text-center cursor-pointer transition overflow-hidden ${
        slot.uploaded
          ? "border-emerald-500 bg-emerald-50/20"
          : isDragActive
          ? "border-blue-500 bg-blue-50/50"
          : "border-gray-200 hover:border-gray-300 bg-gray-50"
      }`}
    >
      <input {...getInputProps()} />

      {slot.preview ? (
        <>
          <img
            src={slot.preview}
            alt={angle}
            className="absolute inset-0 w-full h-full object-cover"
          />
          <div className="absolute inset-0 bg-black/30 flex items-center justify-center">
            {slot.uploaded ? (
              <span className="bg-emerald-600 text-white rounded-full p-1.5 shadow">
                <Check className="w-4 h-4 stroke-[3]" />
              </span>
            ) : (
              <span className="text-white text-xs bg-black/60 px-2 py-0.5 rounded">
                Uploading...
              </span>
            )}
          </div>
        </>
      ) : (
        <>
          <UploadCloud className="w-5 h-5 text-gray-400 mb-1" />
          <span className="text-[11px] font-medium text-gray-600">Upload {angle}</span>
        </>
      )}

      <span className="absolute bottom-1 right-1 bg-black/70 text-white text-[10px] px-1.5 py-0.5 rounded font-mono">
        {angle}
      </span>
    </div>
  )
}
