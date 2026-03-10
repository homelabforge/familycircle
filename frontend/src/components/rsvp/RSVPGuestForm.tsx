import { useState, useEffect } from 'react'
import { Plus, Trash2, UserPlus, Loader2, UtensilsCrossed, AlertTriangle } from 'lucide-react'
import { toast } from 'sonner'
import { useBigMode } from '@/contexts/BigModeContext'
import { rsvpGuestsApi, type RSVPGuest } from '@/lib/api'

interface RSVPGuestFormProps {
  eventId: string
  hasRsvp: boolean
}

export default function RSVPGuestForm({ eventId, hasRsvp }: RSVPGuestFormProps) {
  const { bigMode } = useBigMode()
  const [guests, setGuests] = useState<RSVPGuest[]>([])
  const [loading, setLoading] = useState(false)
  const [showAdd, setShowAdd] = useState(false)
  const [saving, setSaving] = useState(false)
  const [newGuest, setNewGuest] = useState({
    guest_name: '',
    dietary_restrictions: '',
    allergies: '',
  })

  useEffect(() => {
    if (hasRsvp) {
      rsvpGuestsApi.list(eventId)
        .then(data => setGuests(data.guests))
        .catch(() => setGuests([]))
        .finally(() => setLoading(false))
    }
  }, [eventId, hasRsvp])

  async function handleAdd() {
    if (!newGuest.guest_name.trim()) {
      toast.error('Guest name is required')
      return
    }

    setSaving(true)
    try {
      const guest = await rsvpGuestsApi.add(eventId, {
        guest_name: newGuest.guest_name.trim(),
        dietary_restrictions: newGuest.dietary_restrictions.trim() || undefined,
        allergies: newGuest.allergies.trim() || undefined,
      })
      setGuests(prev => [...prev, guest])
      setNewGuest({ guest_name: '', dietary_restrictions: '', allergies: '' })
      setShowAdd(false)
      toast.success('Guest added')
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to add guest')
    } finally {
      setSaving(false)
    }
  }

  async function handleDelete(guestId: string) {
    try {
      await rsvpGuestsApi.delete(eventId, guestId)
      setGuests(prev => prev.filter(g => g.id !== guestId))
      toast.success('Guest removed')
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to remove guest')
    }
  }

  if (!hasRsvp) return null
  if (loading) return <Loader2 className="w-5 h-5 animate-spin text-fc-text-muted" />

  const inputClass = `w-full px-3 py-2 bg-fc-bg border border-fc-border rounded-lg text-fc-text focus:outline-none focus:ring-2 focus:ring-primary ${bigMode ? 'text-lg' : 'text-sm'}`

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h4 className={`font-medium text-fc-text ${bigMode ? 'text-lg' : 'text-sm'}`}>
          <UserPlus className="w-4 h-4 inline mr-1.5" />
          Additional Guests
        </h4>
        <button
          onClick={() => setShowAdd(!showAdd)}
          className={`text-primary hover:text-primary/80 flex items-center gap-1 ${bigMode ? 'text-base' : 'text-sm'}`}
        >
          <Plus className="w-4 h-4" />
          Add Guest
        </button>
      </div>

      {/* Existing guests */}
      {guests.length > 0 && (
        <div className="space-y-2">
          {guests.map(guest => (
            <div
              key={guest.id}
              className="flex items-start justify-between p-3 bg-fc-bg border border-fc-border rounded-lg"
            >
              <div className="space-y-1">
                <p className={`font-medium text-fc-text ${bigMode ? 'text-base' : 'text-sm'}`}>
                  {guest.guest_name}
                </p>
                {guest.dietary_restrictions && (
                  <p className={`text-fc-text-muted flex items-center gap-1 ${bigMode ? 'text-sm' : 'text-xs'}`}>
                    <UtensilsCrossed className="w-3 h-3" />
                    {guest.dietary_restrictions}
                  </p>
                )}
                {guest.allergies && (
                  <p className={`text-amber-400 flex items-center gap-1 ${bigMode ? 'text-sm' : 'text-xs'}`}>
                    <AlertTriangle className="w-3 h-3" />
                    {guest.allergies}
                  </p>
                )}
              </div>
              <button
                onClick={() => handleDelete(guest.id)}
                className="text-fc-text-muted hover:text-error p-1"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Add guest form */}
      {showAdd && (
        <div className="p-3 bg-fc-surface border border-fc-border rounded-lg space-y-3">
          <div>
            <label className={`block font-medium text-fc-text mb-1 ${bigMode ? 'text-base' : 'text-sm'}`}>
              Guest Name *
            </label>
            <input
              type="text"
              value={newGuest.guest_name}
              onChange={e => setNewGuest(prev => ({ ...prev, guest_name: e.target.value }))}
              className={inputClass}
              placeholder="e.g., John Smith"
            />
          </div>
          <div>
            <label className={`block font-medium text-fc-text mb-1 ${bigMode ? 'text-base' : 'text-sm'}`}>
              Dietary Restrictions
            </label>
            <input
              type="text"
              value={newGuest.dietary_restrictions}
              onChange={e => setNewGuest(prev => ({ ...prev, dietary_restrictions: e.target.value }))}
              className={inputClass}
              placeholder="e.g., Vegetarian, Gluten-free"
            />
          </div>
          <div>
            <label className={`block font-medium text-fc-text mb-1 ${bigMode ? 'text-base' : 'text-sm'}`}>
              Allergies
            </label>
            <input
              type="text"
              value={newGuest.allergies}
              onChange={e => setNewGuest(prev => ({ ...prev, allergies: e.target.value }))}
              className={inputClass}
              placeholder="e.g., Nuts, Shellfish"
            />
          </div>
          <div className="flex gap-2 justify-end">
            <button
              onClick={() => setShowAdd(false)}
              className={`px-3 py-1.5 text-fc-text-muted hover:text-fc-text ${bigMode ? 'text-base' : 'text-sm'}`}
            >
              Cancel
            </button>
            <button
              onClick={handleAdd}
              disabled={saving}
              className={`px-3 py-1.5 bg-primary text-white rounded-lg hover:bg-primary/90 disabled:opacity-50 flex items-center gap-1.5 ${bigMode ? 'text-base' : 'text-sm'}`}
            >
              {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Plus className="w-4 h-4" />}
              Add
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
