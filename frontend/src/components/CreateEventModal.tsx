import { useState } from 'react'
import { Calendar, X, Loader2 } from 'lucide-react'
import { toast } from 'sonner'
import { useBigMode } from '@/contexts/BigModeContext'
import { eventsApi } from '@/lib/api'

interface CreateEventModalProps {
  isOpen: boolean
  onClose: () => void
  onEventCreated?: () => void
}

interface EventFormData {
  title: string
  description: string
  event_date: string
  location_name: string
  location_address: string
  has_secret_santa: boolean
  has_potluck: boolean
  has_rsvp: boolean
}

const emptyForm: EventFormData = {
  title: '',
  description: '',
  event_date: '',
  location_name: '',
  location_address: '',
  has_secret_santa: false,
  has_potluck: false,
  has_rsvp: true,
}

export default function CreateEventModal({
  isOpen,
  onClose,
  onEventCreated,
}: CreateEventModalProps) {
  const { bigMode } = useBigMode()
  const [formData, setFormData] = useState<EventFormData>(emptyForm)
  const [saving, setSaving] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!formData.title.trim() || !formData.event_date) {
      toast.error('Title and date are required')
      return
    }

    try {
      setSaving(true)
      await eventsApi.create(formData)
      toast.success('Event created successfully!')
      setFormData(emptyForm)
      onEventCreated?.()
      onClose()
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to create event')
    } finally {
      setSaving(false)
    }
  }

  const handleClose = () => {
    setFormData(emptyForm)
    onClose()
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/50 backdrop-blur-sm"
        onClick={handleClose}
      />

      {/* Modal */}
      <div
        className={`
        relative bg-fc-surface border border-fc-border rounded-2xl
        w-full max-w-2xl mx-4 shadow-xl max-h-[90vh] overflow-y-auto
        ${bigMode ? 'p-8' : 'p-6'}
      `}
      >
        {/* Close button */}
        <button
          onClick={handleClose}
          className="absolute top-4 right-4 p-2 text-fc-text-muted hover:text-fc-text transition-colors"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Header */}
        <div className="flex items-center gap-3 mb-6">
          <div className="p-2 bg-primary/10 rounded-xl">
            <Calendar
              className={`text-primary ${bigMode ? 'w-6 h-6' : 'w-5 h-5'}`}
            />
          </div>
          <h2
            className={`font-bold text-fc-text ${bigMode ? 'text-2xl' : 'text-xl'}`}
          >
            Create Event
          </h2>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Title */}
          <div>
            <label className="block text-sm font-medium text-fc-text mb-2">
              Event Title *
            </label>
            <input
              type="text"
              value={formData.title}
              onChange={(e) =>
                setFormData({ ...formData, title: e.target.value })
              }
              className="w-full px-4 py-3 bg-fc-bg border border-fc-border rounded-xl text-fc-text focus:outline-none focus:ring-2 focus:ring-primary"
              placeholder="e.g., Family Christmas Party"
              required
            />
          </div>

          {/* Date */}
          <div>
            <label className="block text-sm font-medium text-fc-text mb-2">
              Date & Time *
            </label>
            <input
              type="datetime-local"
              value={formData.event_date}
              onChange={(e) =>
                setFormData({ ...formData, event_date: e.target.value })
              }
              className="w-full px-4 py-3 bg-fc-bg border border-fc-border rounded-xl text-fc-text focus:outline-none focus:ring-2 focus:ring-primary"
              required
            />
          </div>

          {/* Description */}
          <div>
            <label className="block text-sm font-medium text-fc-text mb-2">
              Description
            </label>
            <textarea
              value={formData.description}
              onChange={(e) =>
                setFormData({ ...formData, description: e.target.value })
              }
              className="w-full px-4 py-3 bg-fc-bg border border-fc-border rounded-xl text-fc-text focus:outline-none focus:ring-2 focus:ring-primary"
              rows={3}
              placeholder="What's this event about?"
            />
          </div>

          {/* Location Name */}
          <div>
            <label className="block text-sm font-medium text-fc-text mb-2">
              Location Name
            </label>
            <input
              type="text"
              value={formData.location_name}
              onChange={(e) =>
                setFormData({ ...formData, location_name: e.target.value })
              }
              className="w-full px-4 py-3 bg-fc-bg border border-fc-border rounded-xl text-fc-text focus:outline-none focus:ring-2 focus:ring-primary"
              placeholder="e.g., Grandma's House"
            />
          </div>

          {/* Location Address */}
          <div>
            <label className="block text-sm font-medium text-fc-text mb-2">
              Address
            </label>
            <input
              type="text"
              value={formData.location_address}
              onChange={(e) =>
                setFormData({ ...formData, location_address: e.target.value })
              }
              className="w-full px-4 py-3 bg-fc-bg border border-fc-border rounded-xl text-fc-text focus:outline-none focus:ring-2 focus:ring-primary"
              placeholder="Full address"
            />
          </div>

          {/* Feature Toggles */}
          <div className="pt-4 border-t border-fc-border">
            <h3 className="text-sm font-semibold text-fc-text mb-3">
              Event Features
            </h3>
            <div className="space-y-3">
              {/* Gift Exchange */}
              <label className="flex items-start gap-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={formData.has_secret_santa}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      has_secret_santa: e.target.checked,
                    })
                  }
                  className="mt-1 w-5 h-5 text-primary border-fc-border rounded focus:ring-2 focus:ring-primary"
                />
                <div>
                  <div className="font-medium text-fc-text">Gift Exchange</div>
                  <div className="text-sm text-fc-text-muted">
                    Enable secret gift assignments for this event
                  </div>
                </div>
              </label>

              {/* Potluck */}
              <label className="flex items-start gap-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={formData.has_potluck}
                  onChange={(e) =>
                    setFormData({ ...formData, has_potluck: e.target.checked })
                  }
                  className="mt-1 w-5 h-5 text-primary border-fc-border rounded focus:ring-2 focus:ring-primary"
                />
                <div>
                  <div className="font-medium text-fc-text">Potluck</div>
                  <div className="text-sm text-fc-text-muted">
                    Let attendees sign up to bring dishes
                  </div>
                </div>
              </label>

              {/* RSVP */}
              <label className="flex items-start gap-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={formData.has_rsvp}
                  onChange={(e) =>
                    setFormData({ ...formData, has_rsvp: e.target.checked })
                  }
                  className="mt-1 w-5 h-5 text-primary border-fc-border rounded focus:ring-2 focus:ring-primary"
                />
                <div>
                  <div className="font-medium text-fc-text">RSVP Tracking</div>
                  <div className="text-sm text-fc-text-muted">
                    Track who's attending this event
                  </div>
                </div>
              </label>
            </div>
          </div>

          {/* Submit Buttons */}
          <div className="flex gap-3 justify-end pt-4">
            <button
              type="button"
              onClick={handleClose}
              disabled={saving}
              className="px-4 py-2 text-fc-text-muted hover:text-fc-text transition-colors disabled:opacity-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={saving}
              className="px-6 py-2 bg-primary text-white rounded-xl hover:bg-primary-hover transition-colors disabled:opacity-50 flex items-center gap-2"
            >
              {saving && <Loader2 className="w-4 h-4 animate-spin" />}
              {saving ? 'Creating...' : 'Create Event'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
