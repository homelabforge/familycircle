import { useEffect, useState } from 'react'
import { Calendar, Plus, Edit, Trash2, X, Loader2, TreePine, Utensils } from 'lucide-react'
import { toast } from 'sonner'
import { useBigMode } from '@/contexts/BigModeContext'
import { eventsApi, type Event } from '@/lib/api'

interface ManageEventsModalProps {
  isOpen: boolean
  onClose: () => void
}

interface EventFormData {
  title: string
  description: string
  event_date: string
  location_name: string
  location_address: string
  has_secret_santa: boolean
  has_potluck: boolean
}

const emptyForm: EventFormData = {
  title: '',
  description: '',
  event_date: '',
  location_name: '',
  location_address: '',
  has_secret_santa: false,
  has_potluck: false,
}

export default function ManageEventsModal({ isOpen, onClose }: ManageEventsModalProps) {
  const { bigMode } = useBigMode()
  const [events, setEvents] = useState<Event[]>([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [showForm, setShowForm] = useState(false)
  const [editingId, setEditingId] = useState<string | null>(null)
  const [formData, setFormData] = useState<EventFormData>(emptyForm)
  const [deleteConfirm, setDeleteConfirm] = useState<string | null>(null)

  useEffect(() => {
    if (isOpen) {
      loadEvents()
    }
  }, [isOpen])

  const loadEvents = async () => {
    try {
      setLoading(true)
      const res = await eventsApi.list()
      setEvents(res.events)
    } catch (err) {
      toast.error('Failed to load events')
    } finally {
      setLoading(false)
    }
  }

  const openCreateForm = () => {
    setFormData(emptyForm)
    setEditingId(null)
    setShowForm(true)
  }

  const openEditForm = (event: Event) => {
    setFormData({
      title: event.title,
      description: event.description || '',
      event_date: event.event_date.split('T')[0],
      location_name: event.location_name || '',
      location_address: event.location_address || '',
      has_secret_santa: event.has_secret_santa,
      has_potluck: event.has_potluck,
    })
    setEditingId(event.id)
    setShowForm(true)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!formData.title.trim() || !formData.event_date) {
      toast.error('Title and date are required')
      return
    }

    try {
      setSaving(true)
      if (editingId) {
        await eventsApi.update(editingId, formData)
        toast.success('Event updated')
      } else {
        await eventsApi.create(formData)
        toast.success('Event created')
      }
      setShowForm(false)
      await loadEvents()
    } catch (err) {
      toast.error(editingId ? 'Failed to update event' : 'Failed to create event')
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async (id: string) => {
    try {
      await eventsApi.delete(id)
      toast.success('Event deleted')
      setDeleteConfirm(null)
      await loadEvents()
    } catch (err) {
      toast.error('Failed to delete event')
    }
  }

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr)
    return date.toLocaleDateString('en-US', {
      weekday: 'short',
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    })
  }

  const handleClose = () => {
    setShowForm(false)
    setEditingId(null)
    setDeleteConfirm(null)
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
          w-full max-w-2xl mx-4 shadow-xl max-h-[90vh] overflow-hidden flex flex-col
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
            <Calendar className={`text-primary ${bigMode ? 'w-7 h-7' : 'w-6 h-6'}`} />
          </div>
          <h2 className={`font-bold text-fc-text ${bigMode ? 'text-2xl' : 'text-xl'}`}>
            Manage Events
          </h2>
        </div>

        {showForm ? (
          /* Event Form */
          <form onSubmit={handleSubmit} className="space-y-4 overflow-y-auto flex-1">
            <div>
              <label className={`block text-fc-text mb-2 ${bigMode ? 'text-base' : 'text-sm'}`}>
                Event Title *
              </label>
              <input
                type="text"
                value={formData.title}
                onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                placeholder="e.g., Christmas Dinner"
                className={`
                  w-full bg-fc-bg border border-fc-border rounded-xl
                  text-fc-text placeholder:text-fc-text-muted
                  focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent
                  ${bigMode ? 'px-4 py-3 text-base' : 'px-3 py-2 text-sm'}
                `}
              />
            </div>

            <div>
              <label className={`block text-fc-text mb-2 ${bigMode ? 'text-base' : 'text-sm'}`}>
                Date *
              </label>
              <input
                type="date"
                value={formData.event_date}
                onChange={(e) => setFormData({ ...formData, event_date: e.target.value })}
                className={`
                  w-full bg-fc-bg border border-fc-border rounded-xl
                  text-fc-text
                  focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent
                  ${bigMode ? 'px-4 py-3 text-base' : 'px-3 py-2 text-sm'}
                `}
              />
            </div>

            <div>
              <label className={`block text-fc-text mb-2 ${bigMode ? 'text-base' : 'text-sm'}`}>
                Description
              </label>
              <textarea
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                placeholder="Optional details..."
                rows={2}
                className={`
                  w-full bg-fc-bg border border-fc-border rounded-xl
                  text-fc-text placeholder:text-fc-text-muted
                  focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent
                  ${bigMode ? 'px-4 py-3 text-base' : 'px-3 py-2 text-sm'}
                `}
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className={`block text-fc-text mb-2 ${bigMode ? 'text-base' : 'text-sm'}`}>
                  Location Name
                </label>
                <input
                  type="text"
                  value={formData.location_name}
                  onChange={(e) => setFormData({ ...formData, location_name: e.target.value })}
                  placeholder="e.g., Grandma's House"
                  className={`
                    w-full bg-fc-bg border border-fc-border rounded-xl
                    text-fc-text placeholder:text-fc-text-muted
                    focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent
                    ${bigMode ? 'px-4 py-3 text-base' : 'px-3 py-2 text-sm'}
                  `}
                />
              </div>
              <div>
                <label className={`block text-fc-text mb-2 ${bigMode ? 'text-base' : 'text-sm'}`}>
                  Address
                </label>
                <input
                  type="text"
                  value={formData.location_address}
                  onChange={(e) => setFormData({ ...formData, location_address: e.target.value })}
                  placeholder="123 Main St"
                  className={`
                    w-full bg-fc-bg border border-fc-border rounded-xl
                    text-fc-text placeholder:text-fc-text-muted
                    focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent
                    ${bigMode ? 'px-4 py-3 text-base' : 'px-3 py-2 text-sm'}
                  `}
                />
              </div>
            </div>

            {/* Feature toggles */}
            <div className="flex gap-6">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={formData.has_secret_santa}
                  onChange={(e) => setFormData({ ...formData, has_secret_santa: e.target.checked })}
                  className="w-4 h-4 accent-primary"
                />
                <TreePine className="w-4 h-4 text-success" />
                <span className={`text-fc-text ${bigMode ? 'text-base' : 'text-sm'}`}>Gift Exchange</span>
              </label>

              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={formData.has_potluck}
                  onChange={(e) => setFormData({ ...formData, has_potluck: e.target.checked })}
                  className="w-4 h-4 accent-primary"
                />
                <Utensils className="w-4 h-4 text-warning" />
                <span className={`text-fc-text ${bigMode ? 'text-base' : 'text-sm'}`}>Potluck</span>
              </label>
            </div>

            <div className="flex gap-3 pt-4 border-t border-fc-border">
              <button
                type="button"
                onClick={() => setShowForm(false)}
                className={`
                  flex-1 border border-fc-border text-fc-text rounded-xl
                  hover:bg-fc-bg transition-colors
                  ${bigMode ? 'px-4 py-3 text-base' : 'px-3 py-2.5 text-sm'}
                `}
              >
                Back
              </button>
              <button
                type="submit"
                disabled={saving}
                className={`
                  flex-1 flex items-center justify-center gap-2
                  bg-primary text-white rounded-xl
                  hover:bg-primary-hover transition-colors
                  disabled:opacity-50
                  ${bigMode ? 'px-4 py-3 text-base' : 'px-3 py-2.5 text-sm'}
                `}
              >
                {saving && <Loader2 className="w-4 h-4 animate-spin" />}
                {editingId ? 'Save Changes' : 'Create Event'}
              </button>
            </div>
          </form>
        ) : (
          /* Events List */
          <div className="overflow-y-auto flex-1">
            {/* Create Button */}
            <button
              onClick={openCreateForm}
              className={`
                w-full flex items-center justify-center gap-2
                bg-primary text-white rounded-xl
                hover:bg-primary-hover transition-colors mb-4
                ${bigMode ? 'px-4 py-3 text-base' : 'px-3 py-2.5 text-sm'}
              `}
            >
              <Plus className="w-5 h-5" />
              Create New Event
            </button>

            {loading ? (
              <div className="flex justify-center py-8">
                <Loader2 className="w-8 h-8 animate-spin text-primary" />
              </div>
            ) : events.length === 0 ? (
              <div className="text-center py-8 text-fc-text-muted">
                <Calendar className="w-10 h-10 mx-auto mb-3 opacity-50" />
                <p>No events yet. Create your first one!</p>
              </div>
            ) : (
              <div className="space-y-3">
                {events.map((event) => (
                  <div
                    key={event.id}
                    className={`
                      bg-fc-bg border border-fc-border rounded-xl
                      ${bigMode ? 'p-4' : 'p-3'}
                    `}
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 flex-wrap">
                          <h3 className={`font-medium text-fc-text ${bigMode ? 'text-base' : 'text-sm'}`}>
                            {event.title}
                          </h3>
                          {event.has_secret_santa && (
                            <span className="flex items-center gap-1 text-xs bg-success/10 text-success px-2 py-0.5 rounded-full">
                              <TreePine className="w-3 h-3" />
                            </span>
                          )}
                          {event.has_potluck && (
                            <span className="flex items-center gap-1 text-xs bg-warning/10 text-warning px-2 py-0.5 rounded-full">
                              <Utensils className="w-3 h-3" />
                            </span>
                          )}
                        </div>
                        <p className={`text-fc-text-muted ${bigMode ? 'text-sm' : 'text-xs'}`}>
                          {formatDate(event.event_date)}
                          {event.location_name && ` - ${event.location_name}`}
                        </p>
                      </div>
                      <div className="flex gap-1 flex-shrink-0">
                        <button
                          onClick={() => openEditForm(event)}
                          className="p-1.5 text-fc-text-muted hover:text-primary transition-colors"
                        >
                          <Edit className="w-4 h-4" />
                        </button>
                        {deleteConfirm === event.id ? (
                          <div className="flex items-center gap-1">
                            <button
                              onClick={() => handleDelete(event.id)}
                              className="px-2 py-1 text-xs bg-error text-white rounded"
                            >
                              Yes
                            </button>
                            <button
                              onClick={() => setDeleteConfirm(null)}
                              className="px-2 py-1 text-xs border border-fc-border rounded"
                            >
                              No
                            </button>
                          </div>
                        ) : (
                          <button
                            onClick={() => setDeleteConfirm(event.id)}
                            className="p-1.5 text-fc-text-muted hover:text-error transition-colors"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
