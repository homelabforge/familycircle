import { useState } from 'react'
import { X, Plus, Trash2, BarChart3 } from 'lucide-react'
import { useBigMode } from '@/contexts/BigModeContext'
import { pollsApi, type PollTemplate } from '@/lib/api'
import PollTemplateSelector from '@/components/polls/PollTemplateSelector'
import { toast } from 'sonner'

interface CreatePollModalProps {
  isOpen: boolean
  onClose: () => void
  onCreated: () => void
  eventId?: string
}

interface PollOptionInput {
  text: string
}

export default function CreatePollModal({ isOpen, onClose, onCreated, eventId }: CreatePollModalProps) {
  const { bigMode } = useBigMode()
  const [submitting, setSubmitting] = useState(false)
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [allowMultiple, setAllowMultiple] = useState(false)
  const [isAnonymous, setIsAnonymous] = useState(false)
  const [closeDate, setCloseDate] = useState('')
  const [options, setOptions] = useState<PollOptionInput[]>([
    { text: '' },
    { text: '' },
  ])

  const resetForm = () => {
    setTitle('')
    setDescription('')
    setAllowMultiple(false)
    setIsAnonymous(false)
    setCloseDate('')
    setOptions([{ text: '' }, { text: '' }])
  }

  const handleClose = () => {
    resetForm()
    onClose()
  }

  const handleTemplateSelect = (template: PollTemplate) => {
    setTitle(template.name)
    setDescription(template.description || '')
    setAllowMultiple(template.allow_multiple)
    setOptions(template.options.map((text) => ({ text })))
  }

  const addOption = () => {
    if (options.length >= 10) return
    setOptions([...options, { text: '' }])
  }

  const removeOption = (index: number) => {
    if (options.length <= 2) return
    setOptions(options.filter((_, i) => i !== index))
  }

  const updateOption = (index: number, text: string) => {
    const updated = [...options]
    updated[index] = { text }
    setOptions(updated)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    const trimmedTitle = title.trim()
    if (!trimmedTitle) {
      toast.error('Title is required')
      return
    }

    const validOptions = options.filter((o) => o.text.trim())
    if (validOptions.length < 2) {
      toast.error('At least 2 options are required')
      return
    }

    try {
      setSubmitting(true)
      await pollsApi.create({
        title: trimmedTitle,
        description: description.trim() || undefined,
        event_id: eventId,
        allow_multiple: allowMultiple,
        is_anonymous: isAnonymous,
        close_date: closeDate || undefined,
        options: validOptions.map((o, i) => ({ text: o.text.trim(), display_order: i })),
      })
      toast.success('Poll created')
      handleClose()
      onCreated()
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to create poll')
    } finally {
      setSubmitting(false)
    }
  }

  if (!isOpen) return null

  const inputClass = `
    w-full px-4 py-3 bg-fc-bg border border-fc-border rounded-xl
    text-fc-text placeholder:text-fc-text-muted
    focus:outline-none focus:ring-2 focus:ring-primary
    ${bigMode ? 'text-lg' : 'text-base'}
  `

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-fc-surface border border-fc-border rounded-2xl w-full max-w-lg max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-fc-border">
          <div className="flex items-center gap-3">
            <BarChart3 className={`text-primary ${bigMode ? 'w-7 h-7' : 'w-6 h-6'}`} />
            <h2 className={`font-bold text-fc-text ${bigMode ? 'text-2xl' : 'text-xl'}`}>
              Create Poll
            </h2>
          </div>
          <button
            onClick={handleClose}
            className="p-2 rounded-lg hover:bg-fc-surface-hover transition-colors"
          >
            <X className="w-5 h-5 text-fc-text-muted" />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {/* Template selector */}
          <PollTemplateSelector onSelect={handleTemplateSelect} />

          {/* Title */}
          <div>
            <label className={`block font-medium text-fc-text mb-2 ${bigMode ? 'text-base' : 'text-sm'}`}>
              Question / Title *
            </label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="What should we bring to the potluck?"
              className={inputClass}
              maxLength={300}
            />
          </div>

          {/* Description */}
          <div>
            <label className={`block font-medium text-fc-text mb-2 ${bigMode ? 'text-base' : 'text-sm'}`}>
              Description
            </label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Add more context..."
              className={inputClass}
              rows={2}
            />
          </div>

          {/* Options */}
          <div>
            <label className={`block font-medium text-fc-text mb-2 ${bigMode ? 'text-base' : 'text-sm'}`}>
              Options * (min 2)
            </label>
            <div className="space-y-2">
              {options.map((opt, i) => (
                <div key={i} className="flex items-center gap-2">
                  <input
                    type="text"
                    value={opt.text}
                    onChange={(e) => updateOption(i, e.target.value)}
                    placeholder={`Option ${i + 1}`}
                    className={inputClass}
                    maxLength={500}
                  />
                  {options.length > 2 && (
                    <button
                      type="button"
                      onClick={() => removeOption(i)}
                      className="p-2 rounded-lg text-fc-text-muted hover:text-error hover:bg-error/10 transition-colors shrink-0"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  )}
                </div>
              ))}
            </div>
            {options.length < 10 && (
              <button
                type="button"
                onClick={addOption}
                className={`
                  flex items-center gap-2 mt-2 text-primary hover:text-primary/80 transition-colors
                  ${bigMode ? 'text-base' : 'text-sm'}
                `}
              >
                <Plus className="w-4 h-4" />
                Add Option
              </button>
            )}
          </div>

          {/* Toggles */}
          <div className="space-y-3">
            <label className="flex items-center gap-3 cursor-pointer">
              <input
                type="checkbox"
                checked={allowMultiple}
                onChange={(e) => setAllowMultiple(e.target.checked)}
                className="w-5 h-5 rounded border-fc-border text-primary focus:ring-primary"
              />
              <div>
                <span className={`text-fc-text font-medium ${bigMode ? 'text-base' : 'text-sm'}`}>
                  Allow multiple selections
                </span>
                <p className="text-fc-text-muted text-xs">
                  Voters can select more than one option
                </p>
              </div>
            </label>

            <label className="flex items-center gap-3 cursor-pointer">
              <input
                type="checkbox"
                checked={isAnonymous}
                onChange={(e) => setIsAnonymous(e.target.checked)}
                className="w-5 h-5 rounded border-fc-border text-primary focus:ring-primary"
              />
              <div>
                <span className={`text-fc-text font-medium ${bigMode ? 'text-base' : 'text-sm'}`}>
                  Anonymous voting
                </span>
                <p className="text-fc-text-muted text-xs">
                  Who voted for what is hidden from everyone
                </p>
              </div>
            </label>
          </div>

          {/* Close date */}
          <div>
            <label className={`block font-medium text-fc-text mb-2 ${bigMode ? 'text-base' : 'text-sm'}`}>
              Close Date (optional)
            </label>
            <input
              type="datetime-local"
              value={closeDate}
              onChange={(e) => setCloseDate(e.target.value)}
              className={inputClass}
            />
            <p className="text-fc-text-muted text-xs mt-1">
              Poll will automatically close at this date
            </p>
          </div>

          {/* Submit */}
          <div className="flex gap-3 pt-2">
            <button
              type="button"
              onClick={handleClose}
              className={`
                flex-1 px-4 py-3 border border-fc-border rounded-xl
                text-fc-text hover:bg-fc-surface-hover transition-colors
                ${bigMode ? 'text-lg' : 'text-base'}
              `}
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting}
              className={`
                flex-1 px-4 py-3 bg-primary text-white rounded-xl
                hover:bg-primary/90 transition-colors disabled:opacity-50
                ${bigMode ? 'text-lg' : 'text-base'}
              `}
            >
              {submitting ? 'Creating...' : 'Create Poll'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
