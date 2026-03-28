import { Loader2 } from 'lucide-react'
import type { EventBasics, FeatureConfig } from './types'

interface PotluckSetupStepProps {
  basics: EventBasics
  config: FeatureConfig['potluck']
  giftExchangeEnabled: boolean
  onChange: (c: FeatureConfig['potluck']) => void
  onBack: () => void
  onNext: () => void
  saving: boolean
  bigMode: boolean
}

export default function PotluckSetupStep({
  basics,
  config,
  giftExchangeEnabled,
  onChange,
  onBack,
  onNext,
  saving,
  bigMode,
}: PotluckSetupStepProps) {
  return (
    <>
      <h2
        className={`font-bold text-fc-text mb-2 ${bigMode ? 'text-2xl' : 'text-xl'}`}
      >
        Potluck Configuration
      </h2>
      <p className="text-fc-text-muted mb-6">Choose how to manage this potluck</p>

      <form
        onSubmit={(e) => {
          e.preventDefault()
          onNext()
        }}
        className="space-y-6"
      >
        {/* Potluck Mode Selection */}
        <div className="space-y-3">
          <label className="block text-sm font-medium text-fc-text mb-3">
            Signup Method
          </label>

          {/* Organized Mode */}
          <label className="flex items-start gap-3 cursor-pointer p-4 rounded-xl border-2 transition-colors bg-fc-surface hover:bg-fc-surface-hover"
            style={{
              borderColor: config.mode === 'organized' ? 'var(--color-primary)' : 'var(--color-fc-border)',
            }}
          >
            <input
              type="radio"
              name="potluck-mode"
              checked={config.mode === 'organized'}
              onChange={() => onChange({ ...config, mode: 'organized' })}
              className="mt-1 w-5 h-5 text-primary"
            />
            <div className="flex-1">
              <div className="font-medium text-fc-text">Organized Signup</div>
              <div className="text-sm text-fc-text-muted mt-1">
                You'll create a list of items needed. Family members choose what to bring.
              </div>
            </div>
          </label>

          {/* Open Mode */}
          <label className="flex items-start gap-3 cursor-pointer p-4 rounded-xl border-2 transition-colors bg-fc-surface hover:bg-fc-surface-hover"
            style={{
              borderColor: config.mode === 'open' ? 'var(--color-primary)' : 'var(--color-fc-border)',
            }}
          >
            <input
              type="radio"
              name="potluck-mode"
              checked={config.mode === 'open'}
              onChange={() => onChange({ ...config, mode: 'open' })}
              className="mt-1 w-5 h-5 text-primary"
            />
            <div className="flex-1">
              <div className="font-medium text-fc-text">Open Signup</div>
              <div className="text-sm text-fc-text-muted mt-1">
                Family members add their own items. Best for casual potlucks.
              </div>
            </div>
          </label>
        </div>

        {/* Host Providing (optional) */}
        <div>
          <label className="block text-sm font-medium text-fc-text mb-2">
            What are you providing? (Optional)
          </label>
          <textarea
            value={config.hostProviding}
            onChange={(e) => onChange({ ...config, hostProviding: e.target.value })}
            rows={3}
            className="w-full px-4 py-3 bg-fc-bg border border-fc-border rounded-xl text-fc-text focus:outline-none focus:ring-2 focus:ring-primary resize-none"
            placeholder={config.mode === 'organized'
              ? "e.g., Ham, corn on the cob, mashed potatoes"
              : "e.g., I'm providing the turkey and ham, please bring sides and desserts"}
          />
          <p className="text-xs text-fc-text-muted mt-2">
            This will be shown to attendees when they view the potluck.
          </p>
        </div>

        {/* Location Selection - only show when both features are enabled */}
        {basics.location_name && giftExchangeEnabled && (
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
                Potluck Location
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
            {saving ? 'Creating...' : 'Create Event'}
          </button>
        </div>
      </form>
    </>
  )
}
