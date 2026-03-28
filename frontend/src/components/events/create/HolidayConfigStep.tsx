import { toast } from 'sonner'
import type { HolidayConfig } from './types'

interface HolidayConfigStepProps {
  config: HolidayConfig
  setConfig: (c: HolidayConfig) => void
  holidays: string[]
  onBack: () => void
  onNext: () => void
  bigMode: boolean
}

export default function HolidayConfigStep({
  config,
  setConfig,
  holidays,
  onBack,
  onNext,
  bigMode,
}: HolidayConfigStepProps) {
  const handleNext = () => {
    if (!config.holiday_name) {
      toast.error('Please select a holiday')
      return
    }
    if (
      config.holiday_name === 'custom' &&
      !config.custom_holiday_name.trim()
    ) {
      toast.error('Please enter a custom holiday name')
      return
    }
    onNext()
  }

  return (
    <>
      <h2
        className={`font-bold text-fc-text mb-2 ${bigMode ? 'text-2xl' : 'text-xl'}`}
      >
        Holiday Details
      </h2>
      <p className="text-fc-text-muted mb-6">
        Which holiday is this event for?
      </p>

      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-fc-text mb-2">
            Holiday *
          </label>
          <select
            value={config.holiday_name}
            onChange={(e) =>
              setConfig({
                ...config,
                holiday_name: e.target.value,
                custom_holiday_name:
                  e.target.value !== 'custom'
                    ? ''
                    : config.custom_holiday_name,
              })
            }
            className="w-full px-4 py-3 bg-fc-bg border border-fc-border rounded-xl text-fc-text focus:outline-none focus:ring-2 focus:ring-primary"
          >
            <option value="">Select a holiday...</option>
            {holidays.map((h) => (
              <option key={h} value={h}>
                {h}
              </option>
            ))}
            <option value="custom">Other (custom)...</option>
          </select>
        </div>

        {config.holiday_name === 'custom' && (
          <div>
            <label className="block text-sm font-medium text-fc-text mb-2">
              Custom Holiday Name *
            </label>
            <input
              type="text"
              value={config.custom_holiday_name}
              onChange={(e) =>
                setConfig({ ...config, custom_holiday_name: e.target.value })
              }
              className="w-full px-4 py-3 bg-fc-bg border border-fc-border rounded-xl text-fc-text focus:outline-none focus:ring-2 focus:ring-primary"
              placeholder="e.g., Festivus, Lunar New Year"
            />
          </div>
        )}

        <div>
          <label className="block text-sm font-medium text-fc-text mb-2">
            Year
          </label>
          <input
            type="number"
            value={config.year}
            onChange={(e) => setConfig({ ...config, year: e.target.value })}
            className="w-full px-4 py-3 bg-fc-bg border border-fc-border rounded-xl text-fc-text focus:outline-none focus:ring-2 focus:ring-primary"
            placeholder={new Date().getFullYear().toString()}
          />
          <p className="text-xs text-fc-text-muted mt-1">
            Auto-filled from the event date if left blank
          </p>
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
