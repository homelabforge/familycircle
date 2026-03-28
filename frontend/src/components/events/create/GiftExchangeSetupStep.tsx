import { Loader2 } from 'lucide-react'
import type { EventBasics, FeatureConfig } from './types'

interface GiftExchangeSetupStepProps {
  basics: EventBasics
  config: FeatureConfig['giftExchange']
  potluckEnabled: boolean
  onChange: (c: FeatureConfig['giftExchange']) => void
  onBack: () => void
  onNext: () => void
  saving: boolean
  bigMode: boolean
}

export default function GiftExchangeSetupStep({
  basics,
  config,
  potluckEnabled,
  onChange,
  onBack,
  onNext,
  saving,
  bigMode,
}: GiftExchangeSetupStepProps) {
  return (
    <>
      <h2
        className={`font-bold text-fc-text mb-2 ${bigMode ? 'text-2xl' : 'text-xl'}`}
      >
        Gift Exchange Setup
      </h2>
      <p className="text-fc-text-muted mb-6">Configure gift exchange details</p>

      <form
        onSubmit={(e) => {
          e.preventDefault()
          onNext()
        }}
        className="space-y-4"
      >
        {/* Location Selection - only show when both features are enabled */}
        {basics.location_name && potluckEnabled && (
          <div className="bg-fc-bg rounded-xl p-4 border border-fc-border">
            <label className="flex items-start gap-3 cursor-pointer">
              <input
                type="checkbox"
                checked={config.useDefaultLocation}
                onChange={(e) =>
                  onChange({ ...config, useDefaultLocation: e.target.checked })
                }
                className="mt-1 w-5 h-5 text-primary border-fc-border rounded"
              />
              <div>
                <div className="font-medium text-fc-text">
                  Same location as event
                </div>
                <div className="text-sm text-fc-text-muted mt-1">
                  {basics.location_name}
                  {basics.location_address && ` - ${basics.location_address}`}
                </div>
              </div>
            </label>
          </div>
        )}

        {!config.useDefaultLocation && (
          <>
            <div>
              <label className="block text-sm font-medium text-fc-text mb-2">
                Gift Exchange Location
              </label>
              <input
                type="text"
                value={config.location_name}
                onChange={(e) =>
                  onChange({ ...config, location_name: e.target.value })
                }
                className="w-full px-4 py-3 bg-fc-bg border border-fc-border rounded-xl text-fc-text focus:outline-none focus:ring-2 focus:ring-primary"
                placeholder="e.g., Community Center"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-fc-text mb-2">
                Address
              </label>
              <input
                type="text"
                value={config.location_address}
                onChange={(e) =>
                  onChange({ ...config, location_address: e.target.value })
                }
                className="w-full px-4 py-3 bg-fc-bg border border-fc-border rounded-xl text-fc-text focus:outline-none focus:ring-2 focus:ring-primary"
                placeholder="Full address"
              />
            </div>
          </>
        )}

        {/* Budget */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-fc-text mb-2">
              Budget Min ($)
            </label>
            <input
              type="number"
              value={config.budget_min}
              onChange={(e) =>
                onChange({ ...config, budget_min: e.target.value })
              }
              className="w-full px-4 py-3 bg-fc-bg border border-fc-border rounded-xl text-fc-text focus:outline-none focus:ring-2 focus:ring-primary"
              placeholder="20"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-fc-text mb-2">
              Budget Max ($)
            </label>
            <input
              type="number"
              value={config.budget_max}
              onChange={(e) =>
                onChange({ ...config, budget_max: e.target.value })
              }
              className="w-full px-4 py-3 bg-fc-bg border border-fc-border rounded-xl text-fc-text focus:outline-none focus:ring-2 focus:ring-primary"
              placeholder="50"
            />
          </div>
        </div>

        {/* Notes */}
        <div>
          <label className="block text-sm font-medium text-fc-text mb-2">
            Additional Notes
          </label>
          <textarea
            value={config.notes}
            onChange={(e) => onChange({ ...config, notes: e.target.value })}
            className="w-full px-4 py-3 bg-fc-bg border border-fc-border rounded-xl text-fc-text focus:outline-none focus:ring-2 focus:ring-primary"
            rows={3}
            placeholder="Any special rules or instructions"
          />
        </div>

        <div className="flex gap-3 justify-end pt-4">
          <button
            type="button"
            onClick={onBack}
            disabled={saving}
            className="px-4 py-2 text-fc-text-muted hover:text-fc-text transition-colors disabled:opacity-50"
          >
            Back
          </button>
          <button
            type="submit"
            disabled={saving}
            className="px-6 py-2 bg-primary text-white rounded-xl hover:bg-primary-hover transition-colors disabled:opacity-50 flex items-center gap-2"
          >
            {saving && <Loader2 className="w-4 h-4 animate-spin" />}
            {saving ? 'Creating...' : potluckEnabled ? 'Next' : 'Create Event'}
          </button>
        </div>
      </form>
    </>
  )
}
