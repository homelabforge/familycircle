import { useState, useEffect, useCallback } from 'react'
import { Image, X, ChevronLeft, ChevronRight, Trash2, Loader2 } from 'lucide-react'
import { useBigMode } from '@/contexts/BigModeContext'
import { eventPhotosApi, type EventPhoto } from '@/lib/api'

interface PhotoGalleryProps {
  eventId: string
  canManage: boolean
  isCancelled: boolean
}

export default function PhotoGallery({ eventId, canManage, isCancelled }: PhotoGalleryProps) {
  const { bigMode } = useBigMode()
  const [photos, setPhotos] = useState<EventPhoto[]>([])
  const [loading, setLoading] = useState(true)
  const [lightboxIndex, setLightboxIndex] = useState<number | null>(null)
  const [deleting, setDeleting] = useState<string | null>(null)

  const loadPhotos = useCallback(async () => {
    try {
      setLoading(true)
      const data = await eventPhotosApi.list(eventId)
      setPhotos(data.photos)
    } catch {
      // Non-critical
    } finally {
      setLoading(false)
    }
  }, [eventId])

  useEffect(() => {
    loadPhotos()
  }, [loadPhotos])

  const handleDelete = async (photoId: string) => {
    if (!confirm('Delete this photo?')) return
    try {
      setDeleting(photoId)
      await eventPhotosApi.delete(eventId, photoId)
      setPhotos((prev) => prev.filter((p) => p.id !== photoId))
      if (lightboxIndex !== null) {
        const newPhotos = photos.filter((p) => p.id !== photoId)
        if (newPhotos.length === 0) {
          setLightboxIndex(null)
        } else if (lightboxIndex >= newPhotos.length) {
          setLightboxIndex(newPhotos.length - 1)
        }
      }
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to delete photo')
    } finally {
      setDeleting(null)
    }
  }

  const openLightbox = (index: number) => {
    setLightboxIndex(index)
  }

  const closeLightbox = () => {
    setLightboxIndex(null)
  }

  const navigateLightbox = (direction: 'prev' | 'next') => {
    if (lightboxIndex === null) return
    if (direction === 'prev') {
      setLightboxIndex(lightboxIndex > 0 ? lightboxIndex - 1 : photos.length - 1)
    } else {
      setLightboxIndex(lightboxIndex < photos.length - 1 ? lightboxIndex + 1 : 0)
    }
  }

  // Keyboard navigation for lightbox
  useEffect(() => {
    if (lightboxIndex === null) return
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') closeLightbox()
      if (e.key === 'ArrowLeft') navigateLightbox('prev')
      if (e.key === 'ArrowRight') navigateLightbox('next')
    }
    window.addEventListener('keydown', handleKey)
    return () => window.removeEventListener('keydown', handleKey)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [lightboxIndex, photos.length])

  if (loading) {
    return (
      <div className="bg-fc-surface border border-fc-border rounded-2xl p-6 mb-6">
        <div className="flex items-center gap-3 mb-4">
          <Image className={`text-primary ${bigMode ? 'w-6 h-6' : 'w-5 h-5'}`} />
          <h2 className={`font-semibold text-fc-text ${bigMode ? 'text-xl' : 'text-lg'}`}>
            Photos
          </h2>
        </div>
        <div className="flex justify-center py-4">
          <Loader2 className="w-6 h-6 animate-spin text-primary" />
        </div>
      </div>
    )
  }

  if (photos.length === 0 && !canManage) return <></>
  if (photos.length === 0 && isCancelled) return <></>

  return (
    <>
      <div className="bg-fc-surface border border-fc-border rounded-2xl p-6 mb-6">
        <div className="flex items-center gap-3 mb-4">
          <Image className={`text-primary ${bigMode ? 'w-6 h-6' : 'w-5 h-5'}`} />
          <h2 className={`font-semibold text-fc-text ${bigMode ? 'text-xl' : 'text-lg'}`}>
            Photos {photos.length > 0 && `(${photos.length})`}
          </h2>
        </div>

        {photos.length === 0 ? (
          <p className={`text-fc-text-muted ${bigMode ? 'text-base' : 'text-sm'}`}>
            No photos yet. Upload some to share with the family!
          </p>
        ) : (
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
            {photos.map((photo, index) => (
              <div key={photo.id} className="relative group aspect-square">
                <button
                  onClick={() => openLightbox(index)}
                  className="w-full h-full rounded-xl overflow-hidden focus:outline-none focus:ring-2 focus:ring-primary"
                >
                  <img
                    src={photo.url}
                    alt={photo.caption || photo.filename}
                    className="w-full h-full object-cover transition-transform group-hover:scale-105"
                    loading="lazy"
                  />
                </button>
                {canManage && (
                  <button
                    onClick={() => handleDelete(photo.id)}
                    disabled={deleting === photo.id}
                    className="absolute top-2 right-2 p-1.5 bg-black/60 text-white rounded-lg opacity-0 group-hover:opacity-100 transition-opacity hover:bg-error"
                  >
                    {deleting === photo.id ? (
                      <Loader2 className="w-4 h-4 animate-spin" />
                    ) : (
                      <Trash2 className="w-4 h-4" />
                    )}
                  </button>
                )}
                {photo.caption && (
                  <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/70 to-transparent p-2 rounded-b-xl opacity-0 group-hover:opacity-100 transition-opacity">
                    <p className="text-white text-xs truncate">{photo.caption}</p>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Lightbox */}
      {lightboxIndex !== null && photos[lightboxIndex] && (
        <div
          className="fixed inset-0 bg-black/90 z-50 flex items-center justify-center"
          onClick={closeLightbox}
        >
          {/* Close button */}
          <button
            onClick={closeLightbox}
            className="absolute top-4 right-4 p-2 text-white/80 hover:text-white transition-colors z-10"
          >
            <X className="w-8 h-8" />
          </button>

          {/* Navigation */}
          {photos.length > 1 && (
            <>
              <button
                onClick={(e) => { e.stopPropagation(); navigateLightbox('prev') }}
                className="absolute left-4 p-2 text-white/80 hover:text-white transition-colors z-10"
              >
                <ChevronLeft className="w-10 h-10" />
              </button>
              <button
                onClick={(e) => { e.stopPropagation(); navigateLightbox('next') }}
                className="absolute right-4 p-2 text-white/80 hover:text-white transition-colors z-10"
              >
                <ChevronRight className="w-10 h-10" />
              </button>
            </>
          )}

          {/* Image */}
          <div
            className="max-w-[90vw] max-h-[85vh] flex flex-col items-center"
            onClick={(e) => e.stopPropagation()}
          >
            <img
              src={photos[lightboxIndex].url}
              alt={photos[lightboxIndex].caption || photos[lightboxIndex].filename}
              className="max-w-full max-h-[80vh] object-contain rounded-lg"
            />
            <div className="mt-3 text-center">
              {photos[lightboxIndex].caption && (
                <p className="text-white text-sm mb-1">{photos[lightboxIndex].caption}</p>
              )}
              <p className="text-white/50 text-xs">
                Uploaded by {photos[lightboxIndex].uploaded_by_name} &middot;{' '}
                {lightboxIndex + 1} / {photos.length}
              </p>
            </div>
          </div>
        </div>
      )}
    </>
  )
}
