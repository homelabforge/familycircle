import { useState } from 'react'
import { Save, Loader2, Check } from 'lucide-react'
import { toast } from 'sonner'
import { useBigMode } from '@/contexts/BigModeContext'
import { eventTemplatesApi, type Event } from '@/lib/api'

interface SaveTemplateButtonProps {
  event: Event
}

export default function SaveTemplateButton({ event }: SaveTemplateButtonProps) {
  const { bigMode } = useBigMode()
  const [showForm, setShowForm] = useState(false)
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)
  const [name, setName] = useState(`${event.title} Template`)
  const [description, setDescription] = useState('')

  async function handleSave() {
    if (!name.trim()) {
      toast.error('Template name is required')
      return
    }

    const templateData = {
      title: event.title,
      description: event.description,
      location_name: event.location_name,
      location_address: event.location_address,
      event_type: event.event_type,
      has_gift_exchange: event.has_gift_exchange,
      has_potluck: event.has_potluck,
      has_rsvp: event.has_rsvp,
      potluck_mode: event.potluck_mode,
      potluck_host_providing: event.potluck_host_providing,
      gift_exchange_budget_min: event.gift_exchange_budget_min,
      gift_exchange_budget_max: event.gift_exchange_budget_max,
      gift_exchange_notes: event.gift_exchange_notes,
    }

    setSaving(true)
    try {
      await eventTemplatesApi.create({
        name: name.trim(),
        description: description.trim() || undefined,
        template_json: JSON.stringify(templateData),
      })
      setSaved(true)
      setShowForm(false)
      toast.success('Template saved')
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to save template')
    } finally {
      setSaving(false)
    }
  }

  if (saved) {
    return (
      <span className={`inline-flex items-center gap-1.5 text-emerald-400 ${bigMode ? 'text-base' : 'text-sm'}`}>
        <Check className="w-4 h-4" />
        Template saved
      </span>
    )
  }

  if (!showForm) {
    return (
      <button
        onClick={() => setShowForm(true)}
        className={`inline-flex items-center gap-1.5 text-fc-text-muted hover:text-fc-text ${bigMode ? 'text-base' : 'text-sm'}`}
      >
        <Save className="w-4 h-4" />
        Save as Template
      </button>
    )
  }

  const inputClass = `w-full px-3 py-2 bg-fc-bg border border-fc-border rounded-lg text-fc-text focus:outline-none focus:ring-2 focus:ring-primary ${bigMode ? 'text-lg' : 'text-sm'}`

  return (
    <div className="p-3 bg-fc-surface border border-fc-border rounded-lg space-y-3">
      <div>
        <label className={`block font-medium text-fc-text mb-1 ${bigMode ? 'text-base' : 'text-sm'}`}>
          Template Name *
        </label>
        <input
          type="text"
          value={name}
          onChange={e => setName(e.target.value)}
          className={inputClass}
        />
      </div>
      <div>
        <label className={`block font-medium text-fc-text mb-1 ${bigMode ? 'text-base' : 'text-sm'}`}>
          Description (optional)
        </label>
        <input
          type="text"
          value={description}
          onChange={e => setDescription(e.target.value)}
          className={inputClass}
          placeholder="e.g., Annual family BBQ setup"
        />
      </div>
      <div className="flex gap-2 justify-end">
        <button
          onClick={() => setShowForm(false)}
          className={`px-3 py-1.5 text-fc-text-muted hover:text-fc-text ${bigMode ? 'text-base' : 'text-sm'}`}
        >
          Cancel
        </button>
        <button
          onClick={handleSave}
          disabled={saving}
          className={`px-3 py-1.5 bg-primary text-white rounded-lg hover:bg-primary/90 disabled:opacity-50 flex items-center gap-1.5 ${bigMode ? 'text-base' : 'text-sm'}`}
        >
          {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
          Save
        </button>
      </div>
    </div>
  )
}
