import { useState } from 'react'
import { X, Loader2 } from 'lucide-react'
import { toast } from 'sonner'
import { useBigMode } from '@/contexts/BigModeContext'
import { babyShowerUpdatesApi, type BabyShowerUpdate } from '@/lib/api'

const UPDATE_TYPES = [
  { value: 'milestone', label: 'Milestone' },
  { value: 'baby_born', label: 'Baby Born!' },
  { value: 'name_announced', label: 'Name Announced' },
  { value: 'gender_revealed', label: 'Gender Revealed' },
  { value: 'custom', label: 'Custom Update' },
]

export default function BabyShowerUpdateForm({
  eventId,
  onClose,
  onCreated,
}: {
  eventId: string
  onClose: () => void
  onCreated: (update: BabyShowerUpdate) => void
}) {
  const { bigMode } = useBigMode()
  const [updateType, setUpdateType] = useState('milestone')
  const [title, setTitle] = useState('')
  const [notes, setNotes] = useState('')
  const [updateDate, setUpdateDate] = useState('')
  const [saving, setSaving] = useState(false)

  const handleSubmit = async (e: React.FormEvent): Promise<void> => {
    e.preventDefault()
    if (!title.trim()) {
      toast.error('Title is required')
      return
    }

    try {
      setSaving(true)
      const result = await babyShowerUpdatesApi.create(eventId, {
        update_type: updateType,
        title: title.trim(),
        notes: notes.trim() || undefined,
        update_date: updateDate || undefined,
      })
      toast.success('Update posted!')
      onCreated(result)
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to post update')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className={`bg-fc-surface border border-fc-border rounded-2xl max-w-md w-full ${bigMode ? 'p-8' : 'p-6'}`}>
        <div className="flex items-center justify-between mb-4">
          <h2 className={`font-bold text-fc-text ${bigMode ? 'text-xl' : 'text-lg'}`}>
            Add Timeline Update
          </h2>
          <button onClick={onClose} className="text-fc-text-muted hover:text-fc-text transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-fc-text mb-2">
              Update Type
            </label>
            <select
              value={updateType}
              onChange={(e) => setUpdateType(e.target.value)}
              className="w-full px-4 py-3 bg-fc-bg border border-fc-border rounded-xl text-fc-text focus:outline-none focus:ring-2 focus:ring-primary"
            >
              {UPDATE_TYPES.map((t) => (
                <option key={t.value} value={t.value}>{t.label}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-fc-text mb-2">
              Title *
            </label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="w-full px-4 py-3 bg-fc-bg border border-fc-border rounded-xl text-fc-text focus:outline-none focus:ring-2 focus:ring-primary"
              placeholder={
                updateType === 'baby_born' ? 'e.g., Welcome baby Emma!' :
                updateType === 'name_announced' ? "e.g., We've chosen a name!" :
                'e.g., First ultrasound'
              }
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-fc-text mb-2">
              Date
            </label>
            <input
              type="date"
              value={updateDate}
              onChange={(e) => setUpdateDate(e.target.value)}
              className="w-full px-4 py-3 bg-fc-bg border border-fc-border rounded-xl text-fc-text focus:outline-none focus:ring-2 focus:ring-primary"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-fc-text mb-2">
              Notes
            </label>
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              className="w-full px-4 py-3 bg-fc-bg border border-fc-border rounded-xl text-fc-text focus:outline-none focus:ring-2 focus:ring-primary"
              rows={3}
              placeholder="Share more details..."
            />
          </div>

          <div className="flex gap-3 justify-end pt-2">
            <button
              type="button"
              onClick={onClose}
              disabled={saving}
              className="px-4 py-2 text-fc-text-muted hover:text-fc-text transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={saving}
              className="px-6 py-2 bg-primary text-white rounded-xl hover:bg-primary-hover transition-colors disabled:opacity-50 flex items-center gap-2"
            >
              {saving && <Loader2 className="w-4 h-4 animate-spin" />}
              {saving ? 'Posting...' : 'Post Update'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
