import { EyeOff } from 'lucide-react'
import { toast } from 'sonner'
import type { FamilyMember } from '@/lib/api'
import type { BirthdayConfig } from './types'

interface BirthdayConfigStepProps {
  config: BirthdayConfig
  setConfig: (c: BirthdayConfig) => void
  familyMembers: FamilyMember[]
  eventDate: string
  onBack: () => void
  onNext: () => void
  bigMode: boolean
}

export default function BirthdayConfigStep({
  config,
  setConfig,
  familyMembers,
  eventDate,
  onBack,
  onNext,
  bigMode,
}: BirthdayConfigStepProps) {
  const handleMemberChange = (value: string) => {
    if (value === '__other__') {
      setConfig({
        ...config,
        birthday_person_id: '',
        birthday_person_name: '',
      })
    } else if (value) {
      const member = familyMembers.find((m) => m.user_id === value)
      if (member) {
        setConfig({
          ...config,
          birthday_person_id: member.user_id,
          birthday_person_name: member.display_name,
        })
      }
    } else {
      setConfig({
        ...config,
        birthday_person_id: '',
        birthday_person_name: '',
      })
    }
  }

  // Auto-calculate age from birth_date and event_date
  const calculateAge = (birthDate: string, evtDate: string): string => {
    if (!birthDate || !evtDate) return ''
    const birth = new Date(birthDate)
    const evt = new Date(evtDate)
    let age = evt.getFullYear() - birth.getFullYear()
    const m = evt.getMonth() - birth.getMonth()
    if (m < 0 || (m === 0 && evt.getDate() < birth.getDate())) {
      age--
    }
    return age > 0 ? age.toString() : ''
  }

  const handleBirthDateChange = (birthDate: string) => {
    const age = calculateAge(birthDate, eventDate)
    setConfig({ ...config, birth_date: birthDate, age_turning: age })
  }

  const handleNext = () => {
    if (!config.birthday_person_name.trim()) {
      toast.error('Please enter the birthday person\'s name')
      return
    }
    onNext()
  }

  const isOtherPerson = !config.birthday_person_id && config.birthday_person_name !== ''
  const selectValue = config.birthday_person_id
    ? config.birthday_person_id
    : isOtherPerson
      ? '__other__'
      : ''

  return (
    <>
      <h2
        className={`font-bold text-fc-text mb-2 ${bigMode ? 'text-2xl' : 'text-xl'}`}
      >
        Birthday Details
      </h2>
      <p className="text-fc-text-muted mb-6">
        Who is this birthday for?
      </p>

      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-fc-text mb-2">
            Birthday Person *
          </label>
          <select
            value={selectValue}
            onChange={(e) => handleMemberChange(e.target.value)}
            className="w-full px-4 py-3 bg-fc-bg border border-fc-border rounded-xl text-fc-text focus:outline-none focus:ring-2 focus:ring-primary"
          >
            <option value="">Select a family member...</option>
            {familyMembers.map((m) => (
              <option key={m.user_id} value={m.user_id}>
                {m.display_name}
              </option>
            ))}
            <option value="__other__">Someone not on FamilyCircle...</option>
          </select>
        </div>

        {selectValue === '__other__' && (
          <div>
            <label className="block text-sm font-medium text-fc-text mb-2">
              Their Name *
            </label>
            <input
              type="text"
              value={config.birthday_person_name}
              onChange={(e) =>
                setConfig({ ...config, birthday_person_name: e.target.value })
              }
              className="w-full px-4 py-3 bg-fc-bg border border-fc-border rounded-xl text-fc-text focus:outline-none focus:ring-2 focus:ring-primary"
              placeholder="e.g., Uncle Bob"
            />
          </div>
        )}

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-fc-text mb-2">
              Birth Date
            </label>
            <input
              type="date"
              value={config.birth_date}
              onChange={(e) => handleBirthDateChange(e.target.value)}
              className="w-full px-4 py-3 bg-fc-bg border border-fc-border rounded-xl text-fc-text focus:outline-none focus:ring-2 focus:ring-primary"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-fc-text mb-2">
              Age Turning
            </label>
            <input
              type="number"
              value={config.age_turning}
              onChange={(e) =>
                setConfig({ ...config, age_turning: e.target.value })
              }
              className="w-full px-4 py-3 bg-fc-bg border border-fc-border rounded-xl text-fc-text focus:outline-none focus:ring-2 focus:ring-primary"
              placeholder="e.g., 30"
              min="1"
            />
            {config.birth_date && (
              <p className="text-xs text-fc-text-muted mt-1">
                Auto-calculated from birth date
              </p>
            )}
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-fc-text mb-2">
            Party Theme
          </label>
          <input
            type="text"
            value={config.theme}
            onChange={(e) => setConfig({ ...config, theme: e.target.value })}
            className="w-full px-4 py-3 bg-fc-bg border border-fc-border rounded-xl text-fc-text focus:outline-none focus:ring-2 focus:ring-primary"
            placeholder="e.g., Luau, 80s, Superhero"
          />
        </div>

        {/* Secret Birthday Toggle */}
        {config.birthday_person_id && (
          <div className="bg-fc-bg rounded-xl p-4 border border-fc-border">
            <label className="flex items-start gap-3 cursor-pointer">
              <input
                type="checkbox"
                checked={config.is_secret}
                onChange={(e) =>
                  setConfig({ ...config, is_secret: e.target.checked })
                }
                className="mt-1 w-5 h-5 text-primary border-fc-border rounded"
              />
              <div>
                <div className="font-medium text-fc-text flex items-center gap-2">
                  <EyeOff className="w-4 h-4" />
                  Surprise Party
                </div>
                <div className="text-sm text-fc-text-muted mt-1">
                  The birthday person won't be able to see this event anywhere
                  in FamilyCircle — not in the events list, dashboard, or via
                  direct link.
                </div>
              </div>
            </label>
          </div>
        )}
      </div>

      <div className="flex gap-3 justify-end pt-6">
        <button
          onClick={onBack}
          className="px-4 py-2 text-fc-text-muted hover:text-fc-text transition-colors"
        >
          Back
        </button>
        <button
          onClick={handleNext}
          className="px-6 py-2 bg-primary text-white rounded-xl hover:bg-primary-hover transition-colors"
        >
          Next
        </button>
      </div>
    </>
  )
}
