import { useEffect, useState } from 'react'
import { UtensilsCrossed, Plus, Pencil, Trash2, Loader2, X } from 'lucide-react'
import { useBigMode } from '@/contexts/BigModeContext'
import { potluckApi, eventsApi, type PotluckItem, type Event } from '@/lib/api'
import { toast } from 'sonner'

const CATEGORIES = ['appetizer', 'main', 'side', 'dessert', 'drink', 'other']

interface PotluckModalProps {
  isOpen: boolean
  onClose: () => void
}

export default function PotluckModal({ isOpen, onClose }: PotluckModalProps) {
  const { bigMode } = useBigMode()
  const [events, setEvents] = useState<Event[]>([])
  const [selectedEventId, setSelectedEventId] = useState<string>('')
  const [items, setItems] = useState<PotluckItem[]>([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)

  // Form state
  const [showForm, setShowForm] = useState(false)
  const [editingId, setEditingId] = useState<string | null>(null)
  const [formData, setFormData] = useState({
    name: '',
    category: '',
    description: '',
    serves: '',
    dietary_info: '',
    allergens: '',
  })

  // Delete confirmation
  const [deleteId, setDeleteId] = useState<string | null>(null)

  useEffect(() => {
    if (isOpen) {
      loadEvents()
    }
  }, [isOpen])

  useEffect(() => {
    if (selectedEventId) {
      loadPotluckItems()
    }
  }, [selectedEventId])

  const loadEvents = async () => {
    try {
      setLoading(true)
      const res = await eventsApi.list()
      const potluckEvents = res.events.filter((e) => e.has_potluck)
      setEvents(potluckEvents)
      if (potluckEvents.length > 0 && !selectedEventId) {
        setSelectedEventId(potluckEvents[0].id)
      }
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to load events')
    } finally {
      setLoading(false)
    }
  }

  const loadPotluckItems = async () => {
    try {
      const res = await potluckApi.get(selectedEventId)
      setItems(res.items)
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to load potluck items')
    }
  }

  const openAddForm = () => {
    setEditingId(null)
    setFormData({ name: '', category: '', description: '', serves: '', dietary_info: '', allergens: '' })
    setShowForm(true)
  }

  const openEditForm = (item: PotluckItem) => {
    setEditingId(item.id)
    setFormData({
      name: item.name,
      category: item.category || '',
      description: item.description || '',
      serves: item.serves?.toString() || '',
      dietary_info: item.dietary_info || '',
      allergens: item.allergens || '',
    })
    setShowForm(true)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!formData.name.trim()) {
      toast.error('Item name is required')
      return
    }

    try {
      setSaving(true)
      const data = {
        name: formData.name.trim(),
        category: formData.category || undefined,
        description: formData.description.trim() || undefined,
        serves: formData.serves ? parseInt(formData.serves) : undefined,
        dietary_info: formData.dietary_info.trim() || undefined,
        allergens: formData.allergens.trim() || undefined,
      }

      if (editingId) {
        await potluckApi.updateItem(selectedEventId, editingId, data)
        toast.success('Item updated')
      } else {
        await potluckApi.addItem(selectedEventId, data)
        toast.success('Item added')
      }

      setShowForm(false)
      await loadPotluckItems()
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to save item')
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async (id: string) => {
    try {
      await potluckApi.deleteItem(selectedEventId, id)
      toast.success('Item deleted')
      setDeleteId(null)
      await loadPotluckItems()
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to delete item')
    }
  }

  const handleUnclaim = async (itemId: string) => {
    try {
      await potluckApi.unclaim(selectedEventId, itemId)
      toast.success('Item unclaimed')
      await loadPotluckItems()
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to unclaim item')
    }
  }

  const handleClose = () => {
    setShowForm(false)
    setDeleteId(null)
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
          <div className="p-2 bg-warning/10 rounded-xl">
            <UtensilsCrossed className={`text-warning ${bigMode ? 'w-7 h-7' : 'w-6 h-6'}`} />
          </div>
          <h2 className={`font-bold text-fc-text ${bigMode ? 'text-2xl' : 'text-xl'}`}>
            Manage Potluck
          </h2>
        </div>

        {loading ? (
          <div className="flex justify-center py-12">
            <Loader2 className="w-8 h-8 animate-spin text-primary" />
          </div>
        ) : events.length === 0 ? (
          <div className="text-center py-8 text-fc-text-muted">
            <UtensilsCrossed className="w-10 h-10 mx-auto mb-3 opacity-50" />
            <p>No events with potluck enabled.</p>
            <p className="text-sm mt-1">Enable it when creating an event.</p>
          </div>
        ) : showForm ? (
          /* Add/Edit Form */
          <form onSubmit={handleSubmit} className="space-y-4 overflow-y-auto flex-1">
            <div>
              <label className={`block text-fc-text mb-2 ${bigMode ? 'text-base' : 'text-sm'}`}>
                Item Name *
              </label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                placeholder="e.g., Green Bean Casserole"
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
                Category
              </label>
              <select
                value={formData.category}
                onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                className={`
                  w-full bg-fc-bg border border-fc-border rounded-xl
                  text-fc-text
                  focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent
                  ${bigMode ? 'px-4 py-3 text-base' : 'px-3 py-2 text-sm'}
                `}
              >
                <option value="">Select category...</option>
                {CATEGORIES.map((cat) => (
                  <option key={cat} value={cat}>
                    {cat.charAt(0).toUpperCase() + cat.slice(1)}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className={`block text-fc-text mb-2 ${bigMode ? 'text-base' : 'text-sm'}`}>
                Description
              </label>
              <textarea
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                rows={2}
                placeholder="Optional notes about the dish"
                className={`
                  w-full bg-fc-bg border border-fc-border rounded-xl
                  text-fc-text placeholder:text-fc-text-muted resize-none
                  focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent
                  ${bigMode ? 'px-4 py-3 text-base' : 'px-3 py-2 text-sm'}
                `}
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className={`block text-fc-text mb-2 ${bigMode ? 'text-base' : 'text-sm'}`}>
                  Serves
                </label>
                <input
                  type="number"
                  value={formData.serves}
                  onChange={(e) => setFormData({ ...formData, serves: e.target.value })}
                  min="1"
                  placeholder="Number of servings"
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
                  Dietary Info
                </label>
                <input
                  type="text"
                  value={formData.dietary_info}
                  onChange={(e) => setFormData({ ...formData, dietary_info: e.target.value })}
                  placeholder="e.g., vegetarian"
                  className={`
                    w-full bg-fc-bg border border-fc-border rounded-xl
                    text-fc-text placeholder:text-fc-text-muted
                    focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent
                    ${bigMode ? 'px-4 py-3 text-base' : 'px-3 py-2 text-sm'}
                  `}
                />
              </div>
            </div>

            <div>
              <label className={`block text-fc-text mb-2 ${bigMode ? 'text-base' : 'text-sm'}`}>
                Allergens
              </label>
              <input
                type="text"
                value={formData.allergens}
                onChange={(e) => setFormData({ ...formData, allergens: e.target.value })}
                placeholder="e.g., nuts, dairy, shellfish"
                className={`
                  w-full bg-fc-bg border border-fc-border rounded-xl
                  text-fc-text placeholder:text-fc-text-muted
                  focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent
                  ${bigMode ? 'px-4 py-3 text-base' : 'px-3 py-2 text-sm'}
                `}
              />
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
                {editingId ? 'Save Changes' : 'Add Item'}
              </button>
            </div>
          </form>
        ) : deleteId ? (
          /* Delete Confirmation */
          <div className="text-center py-4">
            <Trash2 className="w-12 h-12 text-error mx-auto mb-4" />
            <h3 className={`font-semibold text-fc-text mb-2 ${bigMode ? 'text-xl' : 'text-lg'}`}>
              Delete Item?
            </h3>
            <p className={`text-fc-text-muted mb-6 ${bigMode ? 'text-base' : 'text-sm'}`}>
              This will remove the item from the potluck list.
            </p>
            <div className="flex gap-3 max-w-xs mx-auto">
              <button
                onClick={() => setDeleteId(null)}
                className={`
                  flex-1 border border-fc-border text-fc-text rounded-xl
                  hover:bg-fc-bg transition-colors
                  ${bigMode ? 'px-4 py-3 text-base' : 'px-3 py-2.5 text-sm'}
                `}
              >
                Cancel
              </button>
              <button
                onClick={() => handleDelete(deleteId)}
                className={`
                  flex-1 bg-error text-white rounded-xl
                  hover:opacity-90 transition-opacity
                  ${bigMode ? 'px-4 py-3 text-base' : 'px-3 py-2.5 text-sm'}
                `}
              >
                Delete
              </button>
            </div>
          </div>
        ) : (
          /* Items List */
          <div className="overflow-y-auto flex-1 space-y-4">
            {/* Event Selector */}
            <div>
              <label className={`block text-fc-text mb-2 ${bigMode ? 'text-base' : 'text-sm'}`}>
                Select Event
              </label>
              <select
                value={selectedEventId}
                onChange={(e) => setSelectedEventId(e.target.value)}
                className={`
                  w-full bg-fc-bg border border-fc-border rounded-xl
                  text-fc-text
                  focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent
                  ${bigMode ? 'px-4 py-3 text-base' : 'px-3 py-2 text-sm'}
                `}
              >
                {events.map((event) => (
                  <option key={event.id} value={event.id}>
                    {event.title} - {new Date(event.event_date).toLocaleDateString()}
                  </option>
                ))}
              </select>
            </div>

            {/* Add Item Button */}
            <button
              onClick={openAddForm}
              className={`
                w-full flex items-center justify-center gap-2
                bg-primary text-white rounded-xl
                hover:bg-primary-hover transition-colors
                ${bigMode ? 'px-4 py-3 text-base' : 'px-3 py-2.5 text-sm'}
              `}
            >
              <Plus className="w-5 h-5" />
              Add Item
            </button>

            {/* Items List */}
            {items.length === 0 ? (
              <div className="text-center py-8 text-fc-text-muted">
                <UtensilsCrossed className="w-10 h-10 mx-auto mb-3 opacity-50" />
                <p>No potluck items yet.</p>
                <p className="text-sm mt-1">Add some items for guests to claim!</p>
              </div>
            ) : (
              <div className="space-y-2">
                {items.map((item) => (
                  <div
                    key={item.id}
                    className={`
                      bg-fc-bg border border-fc-border rounded-xl
                      ${bigMode ? 'p-4' : 'p-3'}
                    `}
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className={`font-medium text-fc-text ${bigMode ? 'text-base' : 'text-sm'}`}>
                            {item.name}
                          </span>
                          {item.category && (
                            <span className="text-xs bg-primary/10 text-primary px-2 py-0.5 rounded-full">
                              {item.category}
                            </span>
                          )}
                        </div>
                        {item.description && (
                          <p className={`text-fc-text-muted ${bigMode ? 'text-sm' : 'text-xs'}`}>
                            {item.description}
                          </p>
                        )}
                        <div className="flex flex-wrap items-center gap-x-3 gap-y-1 mt-1">
                          {item.serves && (
                            <span className={`text-fc-text-muted ${bigMode ? 'text-sm' : 'text-xs'}`}>
                              Serves {item.serves}
                            </span>
                          )}
                          {item.dietary_info && (
                            <span className={`text-primary ${bigMode ? 'text-sm' : 'text-xs'}`}>
                              {item.dietary_info}
                            </span>
                          )}
                          {item.allergens && (
                            <span className={`text-warning ${bigMode ? 'text-sm' : 'text-xs'}`}>
                              Contains: {item.allergens}
                            </span>
                          )}
                          {item.claimed_by_name ? (
                            <span className={`text-success ${bigMode ? 'text-sm' : 'text-xs'}`}>
                              Claimed by {item.claimed_by_name}
                            </span>
                          ) : (
                            <span className={`text-warning ${bigMode ? 'text-sm' : 'text-xs'}`}>
                              Unclaimed
                            </span>
                          )}
                        </div>
                      </div>
                      <div className="flex items-center gap-1 flex-shrink-0">
                        {item.claimed_by_id && (
                          <button
                            onClick={() => handleUnclaim(item.id)}
                            className="p-1.5 text-warning hover:bg-warning/10 rounded-lg transition-colors"
                            title="Remove claim"
                          >
                            <X className="w-4 h-4" />
                          </button>
                        )}
                        <button
                          onClick={() => openEditForm(item)}
                          className="p-1.5 text-fc-text-muted hover:text-primary transition-colors"
                          title="Edit"
                        >
                          <Pencil className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => setDeleteId(item.id)}
                          className="p-1.5 text-fc-text-muted hover:text-error transition-colors"
                          title="Delete"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
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
