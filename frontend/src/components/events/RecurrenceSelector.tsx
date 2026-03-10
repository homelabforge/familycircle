import { Repeat, Calendar } from 'lucide-react'
import { useBigMode } from '@/contexts/BigModeContext'

interface RecurrenceSelectorProps {
  recurrenceType: string
  endDate: string
  maxOccurrences: string
  onChange: (field: string, value: string) => void
}

const RECURRENCE_OPTIONS = [
  { value: '', label: 'No recurrence' },
  { value: 'weekly', label: 'Weekly' },
  { value: 'monthly', label: 'Monthly' },
  { value: 'yearly', label: 'Yearly' },
]

export default function RecurrenceSelector({
  recurrenceType,
  endDate,
  maxOccurrences,
  onChange,
}: RecurrenceSelectorProps) {
  const { bigMode } = useBigMode()

  const inputClass = `w-full px-4 py-3 bg-fc-bg border border-fc-border rounded-xl text-fc-text focus:outline-none focus:ring-2 focus:ring-primary ${bigMode ? 'text-lg' : ''}`

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        <Repeat className={`${bigMode ? 'w-5 h-5' : 'w-4 h-4'} text-primary`} />
        <h4 className={`font-medium text-fc-text ${bigMode ? 'text-lg' : 'text-sm'}`}>
          Recurring Event
        </h4>
      </div>

      <div>
        <label className={`block font-medium text-fc-text mb-2 ${bigMode ? 'text-lg' : 'text-sm'}`}>
          Repeat
        </label>
        <select
          value={recurrenceType}
          onChange={e => onChange('recurrenceType', e.target.value)}
          className={inputClass}
        >
          {RECURRENCE_OPTIONS.map(opt => (
            <option key={opt.value} value={opt.value}>{opt.label}</option>
          ))}
        </select>
      </div>

      {recurrenceType && (
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className={`block font-medium text-fc-text mb-2 ${bigMode ? 'text-lg' : 'text-sm'}`}>
              <Calendar className="w-3.5 h-3.5 inline mr-1" />
              End Date (optional)
            </label>
            <input
              type="date"
              value={endDate}
              onChange={e => onChange('endDate', e.target.value)}
              className={inputClass}
            />
          </div>
          <div>
            <label className={`block font-medium text-fc-text mb-2 ${bigMode ? 'text-lg' : 'text-sm'}`}>
              Max Occurrences
            </label>
            <input
              type="number"
              min="1"
              max="100"
              value={maxOccurrences}
              onChange={e => onChange('maxOccurrences', e.target.value)}
              className={inputClass}
              placeholder="Unlimited"
            />
          </div>
        </div>
      )}

      {recurrenceType && (
        <p className={`text-fc-text-muted ${bigMode ? 'text-sm' : 'text-xs'}`}>
          New events will be automatically created {recurrenceType} based on this event.
          {!endDate && !maxOccurrences && ' Events will recur indefinitely until stopped.'}
        </p>
      )}
    </div>
  )
}
