import { useState, useRef } from 'react'
import { Upload, X, Loader2, ImagePlus } from 'lucide-react'
import { useBigMode } from '@/contexts/BigModeContext'
import { eventPhotosApi } from '@/lib/api'

interface PhotoUploadProps {
  eventId: string
  onUploaded: () => void
}

const MAX_SIZE_MB = 10
const ACCEPTED_TYPES = ['image/jpeg', 'image/png', 'image/webp']

export default function PhotoUpload({ eventId, onUploaded }: PhotoUploadProps) {
  const { bigMode } = useBigMode()
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [dragOver, setDragOver] = useState(false)
  const [preview, setPreview] = useState<{ file: File; url: string } | null>(null)
  const [caption, setCaption] = useState('')

  const validateFile = (file: File): string | null => {
    if (!ACCEPTED_TYPES.includes(file.type)) {
      return 'Only JPEG, PNG, and WebP images are allowed.'
    }
    if (file.size > MAX_SIZE_MB * 1024 * 1024) {
      return `File is too large (${(file.size / 1024 / 1024).toFixed(1)} MB). Maximum is ${MAX_SIZE_MB} MB.`
    }
    return null
  }

  const handleFile = (file: File) => {
    setError(null)
    const validationError = validateFile(file)
    if (validationError) {
      setError(validationError)
      return
    }
    const url = URL.createObjectURL(file)
    setPreview({ file, url })
    setCaption('')
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setDragOver(false)
    const file = e.dataTransfer.files[0]
    if (file) handleFile(file)
  }

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    setDragOver(true)
  }

  const handleDragLeave = () => {
    setDragOver(false)
  }

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) handleFile(file)
    // Reset input so the same file can be selected again
    if (fileInputRef.current) fileInputRef.current.value = ''
  }

  const clearPreview = () => {
    if (preview) URL.revokeObjectURL(preview.url)
    setPreview(null)
    setCaption('')
    setError(null)
  }

  const handleUpload = async () => {
    if (!preview) return
    try {
      setUploading(true)
      setError(null)
      await eventPhotosApi.upload(eventId, preview.file, caption.trim() || undefined)
      clearPreview()
      onUploaded()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed')
    } finally {
      setUploading(false)
    }
  }

  return (
    <div className="mb-4">
      {!preview ? (
        <div
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onClick={() => fileInputRef.current?.click()}
          className={`
            border-2 border-dashed rounded-xl cursor-pointer transition-colors
            flex flex-col items-center justify-center gap-2
            ${bigMode ? 'p-6' : 'p-4'}
            ${dragOver
              ? 'border-primary bg-primary/5'
              : 'border-fc-border hover:border-primary/50 hover:bg-fc-bg/50'
            }
          `}
        >
          <ImagePlus className={`text-fc-text-muted ${bigMode ? 'w-8 h-8' : 'w-6 h-6'}`} />
          <p className={`text-fc-text-muted text-center ${bigMode ? 'text-base' : 'text-sm'}`}>
            Drop an image here or click to browse
          </p>
          <p className="text-fc-text-muted text-xs">
            JPEG, PNG, WebP &middot; Max {MAX_SIZE_MB} MB
          </p>
          <input
            ref={fileInputRef}
            type="file"
            accept="image/jpeg,image/png,image/webp"
            onChange={handleInputChange}
            className="hidden"
          />
        </div>
      ) : (
        <div className="border border-fc-border rounded-xl p-4 bg-fc-bg/30">
          <div className="flex gap-4">
            {/* Preview thumbnail */}
            <div className="w-24 h-24 flex-shrink-0 rounded-lg overflow-hidden">
              <img
                src={preview.url}
                alt="Preview"
                className="w-full h-full object-cover"
              />
            </div>

            <div className="flex-1 min-w-0">
              <div className="flex items-start justify-between gap-2 mb-2">
                <p className={`text-fc-text truncate ${bigMode ? 'text-base' : 'text-sm'}`}>
                  {preview.file.name}
                </p>
                <button
                  onClick={clearPreview}
                  disabled={uploading}
                  className="text-fc-text-muted hover:text-error transition-colors flex-shrink-0"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              <input
                type="text"
                value={caption}
                onChange={(e) => setCaption(e.target.value)}
                placeholder="Add a caption (optional)"
                maxLength={500}
                disabled={uploading}
                className={`
                  w-full bg-fc-bg border border-fc-border rounded-lg text-fc-text
                  placeholder:text-fc-text-muted focus:outline-none focus:ring-2 focus:ring-primary
                  ${bigMode ? 'px-3 py-2 text-base' : 'px-2.5 py-1.5 text-sm'}
                `}
              />

              <button
                onClick={handleUpload}
                disabled={uploading}
                className={`
                  mt-2 flex items-center gap-2 bg-primary text-white rounded-lg
                  hover:bg-primary/90 transition-colors disabled:opacity-50
                  ${bigMode ? 'px-4 py-2 text-base' : 'px-3 py-1.5 text-sm'}
                `}
              >
                {uploading ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Uploading...
                  </>
                ) : (
                  <>
                    <Upload className="w-4 h-4" />
                    Upload
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {error && (
        <p className="mt-2 text-error text-sm">{error}</p>
      )}
    </div>
  )
}
