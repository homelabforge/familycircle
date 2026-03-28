import { TreePine, UtensilsCrossed, Check } from 'lucide-react'
import RecurrenceSelector from '@/components/events/RecurrenceSelector'
import type { FeatureConfig } from './types'

interface FeatureSelectionStepProps {
  features: FeatureConfig
  setFeatures: (f: FeatureConfig) => void
  recurrenceType: string
  recurrenceEndDate: string
  recurrenceMaxOccurrences: string
  onRecurrenceChange: (field: string, value: string) => void
  onBack: () => void
  onNext: () => void
  bigMode: boolean
}

export default function FeatureSelectionStep({
  features,
  setFeatures,
  recurrenceType,
  recurrenceEndDate,
  recurrenceMaxOccurrences,
  onRecurrenceChange,
  onBack,
  onNext,
  bigMode,
}: FeatureSelectionStepProps) {
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

      {/* Recurrence option */}
      <div className="mb-6 p-4 bg-fc-bg border border-fc-border rounded-xl">
        <RecurrenceSelector
          recurrenceType={recurrenceType}
          endDate={recurrenceEndDate}
          maxOccurrences={recurrenceMaxOccurrences}
          onChange={onRecurrenceChange}
        />
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
