import { toast } from 'sonner'
import type { BabyShowerConfig } from './types'

const GENDER_OPTIONS = [
  { value: '', label: 'Not sharing' },
  { value: 'boy', label: 'Boy' },
  { value: 'girl', label: 'Girl' },
  { value: 'surprise', label: "It's a Surprise!" },
  { value: 'unknown', label: "Don't Know Yet" },
]

interface BabyShowerConfigStepProps {
  config: BabyShowerConfig
  setConfig: (c: BabyShowerConfig) => void
  onBack: () => void
  onNext: () => void
  bigMode: boolean
}

export default function BabyShowerConfigStep({
  config,
  setConfig,
  onBack,
  onNext,
  bigMode,
}: BabyShowerConfigStepProps) {
  const handleNext = () => {
    if (!config.parent1_name.trim()) {
      toast.error('At least one parent name is required')
      return
    }
    onNext()
  }

  return (
    <>
      <h2
        className={`font-bold text-fc-text mb-2 ${bigMode ? 'text-2xl' : 'text-xl'}`}
      >
        Baby Shower Details
      </h2>
      <p className="text-fc-text-muted mb-6">
        Tell us about the parents-to-be
      </p>

      <div className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-fc-text mb-2">
              Parent 1 Name *
            </label>
            <input
              type="text"
              value={config.parent1_name}
              onChange={(e) => setConfig({ ...config, parent1_name: e.target.value })}
              className="w-full px-4 py-3 bg-fc-bg border border-fc-border rounded-xl text-fc-text focus:outline-none focus:ring-2 focus:ring-primary"
              placeholder="e.g., Sarah"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-fc-text mb-2">
              Parent 2 Name
            </label>
            <input
              type="text"
              value={config.parent2_name}
              onChange={(e) => setConfig({ ...config, parent2_name: e.target.value })}
              className="w-full px-4 py-3 bg-fc-bg border border-fc-border rounded-xl text-fc-text focus:outline-none focus:ring-2 focus:ring-primary"
              placeholder="e.g., Mike"
            />
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-fc-text mb-2">
              Baby Name
            </label>
            <input
              type="text"
              value={config.baby_name}
              onChange={(e) => setConfig({ ...config, baby_name: e.target.value })}
              className="w-full px-4 py-3 bg-fc-bg border border-fc-border rounded-xl text-fc-text focus:outline-none focus:ring-2 focus:ring-primary"
              placeholder="If decided"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-fc-text mb-2">
              Gender
            </label>
            <select
              value={config.gender}
              onChange={(e) => setConfig({ ...config, gender: e.target.value })}
              className="w-full px-4 py-3 bg-fc-bg border border-fc-border rounded-xl text-fc-text focus:outline-none focus:ring-2 focus:ring-primary"
            >
              {GENDER_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>{opt.label}</option>
              ))}
            </select>
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-fc-text mb-2">
            Due Date
          </label>
          <input
            type="date"
            value={config.due_date}
            onChange={(e) => setConfig({ ...config, due_date: e.target.value })}
            className="w-full px-4 py-3 bg-fc-bg border border-fc-border rounded-xl text-fc-text focus:outline-none focus:ring-2 focus:ring-primary"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-fc-text mb-2">
            Registry URL
          </label>
          <input
            type="url"
            value={config.registry_url}
            onChange={(e) => setConfig({ ...config, registry_url: e.target.value })}
            className="w-full px-4 py-3 bg-fc-bg border border-fc-border rounded-xl text-fc-text focus:outline-none focus:ring-2 focus:ring-primary"
            placeholder="https://..."
          />
        </div>

        {/* Gender Reveal Toggle */}
        <div className="bg-fc-bg rounded-xl p-4 border border-fc-border">
          <label className="flex items-start gap-3 cursor-pointer">
            <input
              type="checkbox"
              checked={config.is_gender_reveal}
              onChange={(e) =>
                setConfig({ ...config, is_gender_reveal: e.target.checked })
              }
              className="mt-1 w-5 h-5 text-primary border-fc-border rounded"
            />
            <div>
              <div className="font-medium text-fc-text">This is also a Gender Reveal</div>
              <div className="text-sm text-fc-text-muted mt-1">
                Mark this event as a gender reveal party
              </div>
            </div>
          </label>
        </div>
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
