import { toast } from 'sonner'
import WeddingTemplateSelector from '@/components/events/WeddingTemplateSelector'
import type { WeddingConfig } from './types'

interface WeddingConfigStepProps {
  config: WeddingConfig
  setConfig: (c: WeddingConfig) => void
  onBack: () => void
  onNext: () => void
  bigMode: boolean
}

export default function WeddingConfigStep({
  config,
  setConfig,
  onBack,
  onNext,
  bigMode,
}: WeddingConfigStepProps) {
  const handleNext = () => {
    if (!config.partner1_name.trim() || !config.partner2_name.trim()) {
      toast.error('Both partner names are required')
      return
    }
    onNext()
  }

  return (
    <>
      <h2
        className={`font-bold text-fc-text mb-2 ${bigMode ? 'text-2xl' : 'text-xl'}`}
      >
        Wedding Details
      </h2>
      <p className="text-fc-text-muted mb-6">
        Tell us about the happy couple
      </p>

      <div className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-fc-text mb-2">
              Partner 1 Name *
            </label>
            <input
              type="text"
              value={config.partner1_name}
              onChange={(e) => setConfig({ ...config, partner1_name: e.target.value })}
              className="w-full px-4 py-3 bg-fc-bg border border-fc-border rounded-xl text-fc-text focus:outline-none focus:ring-2 focus:ring-primary"
              placeholder="e.g., Alex"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-fc-text mb-2">
              Partner 2 Name *
            </label>
            <input
              type="text"
              value={config.partner2_name}
              onChange={(e) => setConfig({ ...config, partner2_name: e.target.value })}
              className="w-full px-4 py-3 bg-fc-bg border border-fc-border rounded-xl text-fc-text focus:outline-none focus:ring-2 focus:ring-primary"
              placeholder="e.g., Jordan"
            />
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-fc-text mb-2">
            Wedding Date
          </label>
          <input
            type="date"
            value={config.wedding_date}
            onChange={(e) => setConfig({ ...config, wedding_date: e.target.value })}
            className="w-full px-4 py-3 bg-fc-bg border border-fc-border rounded-xl text-fc-text focus:outline-none focus:ring-2 focus:ring-primary"
          />
          <p className="text-xs text-fc-text-muted mt-1">
            If different from the event date
          </p>
        </div>

        <div>
          <label className="block text-sm font-medium text-fc-text mb-2">
            Venue Name
          </label>
          <input
            type="text"
            value={config.venue_name}
            onChange={(e) => setConfig({ ...config, venue_name: e.target.value })}
            className="w-full px-4 py-3 bg-fc-bg border border-fc-border rounded-xl text-fc-text focus:outline-none focus:ring-2 focus:ring-primary"
            placeholder="e.g., Rose Garden Estate"
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

        <div>
          <label className="block text-sm font-medium text-fc-text mb-2">
            Color Theme
          </label>
          <input
            type="text"
            value={config.color_theme}
            onChange={(e) => setConfig({ ...config, color_theme: e.target.value })}
            className="w-full px-4 py-3 bg-fc-bg border border-fc-border rounded-xl text-fc-text focus:outline-none focus:ring-2 focus:ring-primary"
            placeholder="e.g., Blush pink & sage green"
          />
        </div>

        {/* Wedding Template Selector */}
        <WeddingTemplateSelector
          selected={config.sub_event_template}
          onSelect={(template) => setConfig({ ...config, sub_event_template: template })}
        />
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
