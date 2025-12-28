import { useState } from 'react'
import { X, Loader2, TreePine, UtensilsCrossed, Check } from 'lucide-react'
import { toast } from 'sonner'
import { useBigMode } from '@/contexts/BigModeContext'
import { eventsApi } from '@/lib/api'

interface CreateEventModalProps {
  isOpen: boolean
  onClose: () => void
  onEventCreated?: () => void
}

type WizardStep = 'basics' | 'features' | 'gift-exchange' | 'potluck'

interface EventBasics {
  title: string
  description: string
  event_date: string
  location_name: string
  location_address: string
  has_rsvp: boolean
}

interface FeatureConfig {
  giftExchange: {
    enabled: boolean
    useDefaultLocation: boolean
    location_name: string
    location_address: string
    budget_min: string
    budget_max: string
    notes: string
  }
  potluck: {
    enabled: boolean
    mode: 'organized' | 'open'
    hostProviding: string
    useDefaultLocation: boolean
    location_name: string
    location_address: string
  }
}

const emptyBasics: EventBasics = {
  title: '',
  description: '',
  event_date: '',
  location_name: '',
  location_address: '',
  has_rsvp: true,
}

const emptyFeatureConfig: FeatureConfig = {
  giftExchange: {
    enabled: false,
    useDefaultLocation: true,
    location_name: '',
    location_address: '',
    budget_min: '',
    budget_max: '',
    notes: '',
  },
  potluck: {
    enabled: false,
    mode: 'organized',
    hostProviding: '',
    useDefaultLocation: true,
    location_name: '',
    location_address: '',
  },
}

export default function CreateEventModal({
  isOpen,
  onClose,
  onEventCreated,
}: CreateEventModalProps) {
  const { bigMode } = useBigMode()
  const [currentStep, setCurrentStep] = useState<WizardStep>('basics')
  const [basics, setBasics] = useState<EventBasics>(emptyBasics)
  const [features, setFeatures] = useState<FeatureConfig>(emptyFeatureConfig)
  const [saving, setSaving] = useState(false)

  const handleClose = () => {
    setCurrentStep('basics')
    setBasics(emptyBasics)
    setFeatures(emptyFeatureConfig)
    onClose()
  }

  const handleBasicsNext = () => {
    if (!basics.title.trim() || !basics.event_date) {
      toast.error('Title and date are required')
      return
    }
    setCurrentStep('features')
  }

  const handleFeatureSelection = () => {
    const enabled = []
    if (features.giftExchange.enabled) enabled.push('gift-exchange')
    if (features.potluck.enabled) enabled.push('potluck')

    if (enabled.length === 0) {
      // No features, create basic event
      handleSubmit()
    } else {
      // Go to first feature setup
      setCurrentStep(enabled[0] as WizardStep)
    }
  }

  const handleFeatureNext = (feature: 'giftExchange' | 'potluck') => {
    if (feature === 'giftExchange' && features.potluck.enabled) {
      setCurrentStep('potluck')
    } else {
      handleSubmit()
    }
  }

  const handleSubmit = async () => {
    try {
      setSaving(true)

      const payload: any = {
        title: basics.title,
        description: basics.description || undefined,
        event_date: basics.event_date,
        location_name: basics.location_name || undefined,
        location_address: basics.location_address || undefined,
        has_secret_santa: features.giftExchange.enabled,
        has_potluck: features.potluck.enabled,
        has_rsvp: basics.has_rsvp,
      }

      if (features.giftExchange.enabled) {
        payload.secret_santa_budget_min = features.giftExchange.budget_min
          ? parseInt(features.giftExchange.budget_min)
          : undefined
        payload.secret_santa_budget_max = features.giftExchange.budget_max
          ? parseInt(features.giftExchange.budget_max)
          : undefined
        payload.secret_santa_notes = features.giftExchange.notes || undefined
      }

      if (features.potluck.enabled) {
        payload.potluck_mode = features.potluck.mode
        payload.potluck_host_providing = features.potluck.hostProviding || undefined
      }

      await eventsApi.create(payload)
      toast.success('Event created successfully!')
      handleClose()
      onEventCreated?.()
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to create event')
    } finally {
      setSaving(false)
    }
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/50 backdrop-blur-sm"
        onClick={handleClose}
      />

      {/* Modal */}
      <div
        className={`
          relative bg-fc-surface border border-fc-border rounded-2xl
          w-full max-w-2xl mx-4 shadow-xl max-h-[90vh] overflow-y-auto
          ${bigMode ? 'p-8' : 'p-6'}
        `}
      >
        {/* Close button */}
        <button
          onClick={handleClose}
          className="absolute top-4 right-4 p-2 text-fc-text-muted hover:text-fc-text transition-colors"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Step 1: Event Basics */}
        {currentStep === 'basics' && (
          <EventBasicsStep
            basics={basics}
            setBasics={setBasics}
            onNext={handleBasicsNext}
            bigMode={bigMode}
          />
        )}

        {/* Step 2: Feature Selection */}
        {currentStep === 'features' && (
          <FeatureSelectionStep
            features={features}
            setFeatures={setFeatures}
            onBack={() => setCurrentStep('basics')}
            onNext={handleFeatureSelection}
            bigMode={bigMode}
          />
        )}

        {/* Step 3: Gift Exchange Setup */}
        {currentStep === 'gift-exchange' && (
          <GiftExchangeSetupStep
            basics={basics}
            config={features.giftExchange}
            potluckEnabled={features.potluck.enabled}
            onChange={(updated) =>
              setFeatures({ ...features, giftExchange: updated })
            }
            onBack={() => setCurrentStep('features')}
            onNext={() => handleFeatureNext('giftExchange')}
            saving={saving}
            bigMode={bigMode}
          />
        )}

        {/* Step 4: Potluck Setup */}
        {currentStep === 'potluck' && (
          <PotluckSetupStep
            basics={basics}
            config={features.potluck}
            giftExchangeEnabled={features.giftExchange.enabled}
            onChange={(updated) =>
              setFeatures({ ...features, potluck: updated })
            }
            onBack={() =>
              features.giftExchange.enabled
                ? setCurrentStep('gift-exchange')
                : setCurrentStep('features')
            }
            onNext={handleSubmit}
            saving={saving}
            bigMode={bigMode}
          />
        )}
      </div>
    </div>
  )
}

// Event Basics Step
function EventBasicsStep({
  basics,
  setBasics,
  onNext,
  bigMode,
}: {
  basics: EventBasics
  setBasics: (b: EventBasics) => void
  onNext: () => void
  bigMode: boolean
}) {
  return (
    <>
      <h2
        className={`font-bold text-fc-text mb-6 ${bigMode ? 'text-2xl' : 'text-xl'}`}
      >
        Create Event
      </h2>

      <form
        onSubmit={(e) => {
          e.preventDefault()
          onNext()
        }}
        className="space-y-4"
      >
        <div>
          <label className="block text-sm font-medium text-fc-text mb-2">
            Event Title *
          </label>
          <input
            type="text"
            value={basics.title}
            onChange={(e) => setBasics({ ...basics, title: e.target.value })}
            className="w-full px-4 py-3 bg-fc-bg border border-fc-border rounded-xl text-fc-text focus:outline-none focus:ring-2 focus:ring-primary"
            placeholder="e.g., Family Christmas Party"
            required
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-fc-text mb-2">
            Date & Time *
          </label>
          <input
            type="datetime-local"
            value={basics.event_date}
            onChange={(e) =>
              setBasics({ ...basics, event_date: e.target.value })
            }
            className="w-full px-4 py-3 bg-fc-bg border border-fc-border rounded-xl text-fc-text focus:outline-none focus:ring-2 focus:ring-primary"
            required
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-fc-text mb-2">
            Description
          </label>
          <textarea
            value={basics.description}
            onChange={(e) =>
              setBasics({ ...basics, description: e.target.value })
            }
            className="w-full px-4 py-3 bg-fc-bg border border-fc-border rounded-xl text-fc-text focus:outline-none focus:ring-2 focus:ring-primary"
            rows={3}
            placeholder="What's this event about?"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-fc-text mb-2">
            Location Name
          </label>
          <input
            type="text"
            value={basics.location_name}
            onChange={(e) =>
              setBasics({ ...basics, location_name: e.target.value })
            }
            className="w-full px-4 py-3 bg-fc-bg border border-fc-border rounded-xl text-fc-text focus:outline-none focus:ring-2 focus:ring-primary"
            placeholder="e.g., Grandma's House"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-fc-text mb-2">
            Address
          </label>
          <input
            type="text"
            value={basics.location_address}
            onChange={(e) =>
              setBasics({ ...basics, location_address: e.target.value })
            }
            className="w-full px-4 py-3 bg-fc-bg border border-fc-border rounded-xl text-fc-text focus:outline-none focus:ring-2 focus:ring-primary"
            placeholder="Full address"
          />
        </div>

        <div className="pt-4 border-t border-fc-border">
          <label className="flex items-start gap-3 cursor-pointer">
            <input
              type="checkbox"
              checked={basics.has_rsvp}
              onChange={(e) =>
                setBasics({ ...basics, has_rsvp: e.target.checked })
              }
              className="mt-1 w-5 h-5 text-primary border-fc-border rounded focus:ring-2 focus:ring-primary"
            />
            <div>
              <div className="font-medium text-fc-text">RSVP Tracking</div>
              <div className="text-sm text-fc-text-muted">
                Track who's attending this event
              </div>
            </div>
          </label>
        </div>

        <div className="flex justify-end pt-4">
          <button
            type="submit"
            className="px-6 py-2 bg-primary text-white rounded-xl hover:bg-primary-hover transition-colors"
          >
            Next
          </button>
        </div>
      </form>
    </>
  )
}

// Feature Selection Step
function FeatureSelectionStep({
  features,
  setFeatures,
  onBack,
  onNext,
  bigMode,
}: {
  features: FeatureConfig
  setFeatures: (f: FeatureConfig) => void
  onBack: () => void
  onNext: () => void
  bigMode: boolean
}) {
  const featureCards = [
    {
      id: 'giftExchange',
      icon: TreePine,
      title: 'Gift Exchange',
      description: 'Enable secret gift assignments',
      color: 'primary',
    },
    {
      id: 'potluck',
      icon: UtensilsCrossed,
      title: 'Potluck',
      description: 'Let attendees bring dishes',
      color: 'warning',
    },
  ]

  return (
    <>
      <h2
        className={`font-bold text-fc-text mb-2 ${bigMode ? 'text-2xl' : 'text-xl'}`}
      >
        Select Features
      </h2>
      <p className="text-fc-text-muted mb-6">
        Choose which features to enable for this event
      </p>

      <div className="grid grid-cols-2 gap-4 mb-6">
        {featureCards.map((card) => {
          const Icon = card.icon
          const isSelected =
            card.id === 'giftExchange'
              ? features.giftExchange.enabled
              : features.potluck.enabled

          return (
            <button
              key={card.id}
              onClick={() => {
                if (card.id === 'giftExchange') {
                  setFeatures({
                    ...features,
                    giftExchange: {
                      ...features.giftExchange,
                      enabled: !features.giftExchange.enabled,
                    },
                  })
                } else {
                  setFeatures({
                    ...features,
                    potluck: {
                      ...features.potluck,
                      enabled: !features.potluck.enabled,
                    },
                  })
                }
              }}
              className={`
                relative p-6 rounded-2xl border-2 transition-all
                ${
                  isSelected
                    ? 'border-primary bg-primary/10'
                    : 'border-fc-border bg-fc-surface hover:bg-fc-surface-hover'
                }
              `}
            >
              {isSelected && (
                <div className="absolute top-3 right-3 w-8 h-8 bg-primary rounded-full flex items-center justify-center">
                  <Check className="w-5 h-5 text-white" />
                </div>
              )}
              <Icon
                className={`w-12 h-12 mx-auto mb-3 ${isSelected ? 'text-primary' : 'text-fc-text-muted'}`}
              />
              <h3 className="font-semibold text-fc-text mb-1">{card.title}</h3>
              <p className="text-sm text-fc-text-muted">{card.description}</p>
            </button>
          )
        })}
      </div>

      <div className="flex gap-3 justify-end">
        <button
          onClick={onBack}
          className="px-4 py-2 text-fc-text-muted hover:text-fc-text transition-colors"
        >
          Back
        </button>
        <button
          onClick={onNext}
          className="px-6 py-2 bg-primary text-white rounded-xl hover:bg-primary-hover transition-colors"
        >
          {features.giftExchange.enabled || features.potluck.enabled
            ? 'Next'
            : 'Create Event'}
        </button>
      </div>
    </>
  )
}

// Gift Exchange Setup Step
function GiftExchangeSetupStep({
  basics,
  config,
  potluckEnabled,
  onChange,
  onBack,
  onNext,
  saving,
  bigMode,
}: {
  basics: EventBasics
  config: FeatureConfig['giftExchange']
  potluckEnabled: boolean
  onChange: (c: FeatureConfig['giftExchange']) => void
  onBack: () => void
  onNext: () => void
  saving: boolean
  bigMode: boolean
}) {
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
            {saving ? 'Creating...' : 'Next'}
          </button>
        </div>
      </form>
    </>
  )
}

// Potluck Setup Step
function PotluckSetupStep({
  basics,
  config,
  giftExchangeEnabled,
  onChange,
  onBack,
  onNext,
  saving,
  bigMode,
}: {
  basics: EventBasics
  config: FeatureConfig['potluck']
  giftExchangeEnabled: boolean
  onChange: (c: FeatureConfig['potluck']) => void
  onBack: () => void
  onNext: () => void
  saving: boolean
  bigMode: boolean
}) {
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
