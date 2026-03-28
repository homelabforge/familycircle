import { useEffect, useState } from 'react'
import { X, Check, ChevronRight } from 'lucide-react'
import { toast } from 'sonner'
import { useBigMode } from '@/contexts/BigModeContext'
import { eventsApi, familyApi } from '@/lib/api'
import type { EventType, FamilyMember } from '@/lib/api'
import type { WizardStep } from './types'
import {
  emptyBasics,
  emptyHolidayConfig,
  emptyBirthdayConfig,
  emptyBabyShowerConfig,
  emptyWeddingConfig,
  emptyFeatureConfig,
  getStepLabels,
  getStepIndex,
} from './types'
import type {
  EventBasics,
  HolidayConfig,
  BirthdayConfig,
  BabyShowerConfig,
  WeddingConfig,
  FeatureConfig,
} from './types'
import EventTypeStep from './EventTypeStep'
import EventBasicsStep from './EventBasicsStep'
import HolidayConfigStep from './HolidayConfigStep'
import BirthdayConfigStep from './BirthdayConfigStep'
import BabyShowerConfigStep from './BabyShowerConfigStep'
import WeddingConfigStep from './WeddingConfigStep'
import FeatureSelectionStep from './FeatureSelectionStep'
import GiftExchangeSetupStep from './GiftExchangeSetupStep'
import PotluckSetupStep from './PotluckSetupStep'
import { buildEventPayload } from './buildEventPayload'

interface CreateEventModalProps {
  isOpen: boolean
  onClose: () => void
  onEventCreated?: () => void
}

export default function CreateEventModal({
  isOpen,
  onClose,
  onEventCreated,
}: CreateEventModalProps) {
  const { bigMode } = useBigMode()
  const [currentStep, setCurrentStep] = useState<WizardStep>('event-type')
  const [eventType, setEventType] = useState<EventType>('general')
  const [basics, setBasics] = useState<EventBasics>(emptyBasics)
  const [holidayConfig, setHolidayConfig] = useState<HolidayConfig>(emptyHolidayConfig)
  const [birthdayConfig, setBirthdayConfig] = useState<BirthdayConfig>(emptyBirthdayConfig)
  const [babyShowerConfig, setBabyShowerConfig] = useState<BabyShowerConfig>(emptyBabyShowerConfig)
  const [weddingConfig, setWeddingConfig] = useState<WeddingConfig>(emptyWeddingConfig)
  const [features, setFeatures] = useState<FeatureConfig>(emptyFeatureConfig)
  const [recurrenceType, setRecurrenceType] = useState('')
  const [recurrenceEndDate, setRecurrenceEndDate] = useState('')
  const [recurrenceMaxOccurrences, setRecurrenceMaxOccurrences] = useState('')
  const [saving, setSaving] = useState(false)

  // Data fetched from backend
  const [holidays, setHolidays] = useState<string[]>([])
  const [familyMembers, setFamilyMembers] = useState<FamilyMember[]>([])

  useEffect(() => {
    if (!isOpen) return
    eventsApi.listHolidays().then((r) => setHolidays(r.holidays)).catch(() => {})
    familyApi.listMembers().then((r) => setFamilyMembers(r.members)).catch(() => {})
  }, [isOpen])

  const handleClose = () => {
    setCurrentStep('event-type')
    setEventType('general')
    setBasics(emptyBasics)
    setHolidayConfig(emptyHolidayConfig)
    setBirthdayConfig(emptyBirthdayConfig)
    setBabyShowerConfig(emptyBabyShowerConfig)
    setWeddingConfig(emptyWeddingConfig)
    setFeatures(emptyFeatureConfig)
    setRecurrenceType('')
    setRecurrenceEndDate('')
    setRecurrenceMaxOccurrences('')
    onClose()
  }

  const handleTypeNext = () => {
    setCurrentStep('basics')
  }

  const handleBasicsNext = () => {
    if (!basics.title.trim() || !basics.event_date) {
      toast.error('Title and date are required')
      return
    }
    if (eventType === 'holiday') {
      // Auto-populate year from event date if not set
      if (!holidayConfig.year && basics.event_date) {
        const year = new Date(basics.event_date).getFullYear().toString()
        setHolidayConfig((prev) => ({ ...prev, year }))
      }
      setCurrentStep('holiday-config')
    } else if (eventType === 'birthday') {
      setCurrentStep('birthday-config')
    } else if (eventType === 'baby_shower') {
      setCurrentStep('baby-shower-config')
    } else if (eventType === 'wedding') {
      setCurrentStep('wedding-config')
    } else {
      setCurrentStep('features')
    }
  }

  const handleTypeConfigNext = () => {
    setCurrentStep('features')
  }

  const handleFeatureSelection = () => {
    const enabled = []
    if (features.giftExchange.enabled) enabled.push('gift-exchange')
    if (features.potluck.enabled) enabled.push('potluck')

    if (enabled.length === 0) {
      handleSubmit()
    } else {
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

  const getBackStepFromFeatures = (): WizardStep => {
    if (eventType === 'holiday') return 'holiday-config'
    if (eventType === 'birthday') return 'birthday-config'
    if (eventType === 'baby_shower') return 'baby-shower-config'
    if (eventType === 'wedding') return 'wedding-config'
    return 'basics'
  }

  const handleSubmit = async () => {
    try {
      setSaving(true)

      const payload = buildEventPayload({
        basics,
        eventType,
        features,
        recurrence: { recurrenceType, recurrenceEndDate, recurrenceMaxOccurrences },
        holidayConfig,
        birthdayConfig,
        babyShowerConfig,
        weddingConfig,
      })

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

  const stepLabels = getStepLabels(eventType, features)
  const currentIdx = getStepIndex(currentStep, eventType, features)

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

        {/* Step Indicator */}
        {currentStep !== 'event-type' && (
          <div className="flex items-center gap-1 mb-6 overflow-x-auto">
            {stepLabels.map((label, i) => (
              <div key={label} className="flex items-center gap-1 shrink-0">
                <div
                  className={`
                    flex items-center gap-1.5 px-2 py-1 rounded-full text-xs font-medium transition-colors
                    ${i < currentIdx ? 'text-primary' : ''}
                    ${i === currentIdx ? 'bg-primary/10 text-primary' : ''}
                    ${i > currentIdx ? 'text-fc-text-muted' : ''}
                  `}
                >
                  <span
                    className={`
                      w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold
                      ${i < currentIdx ? 'bg-primary text-white' : ''}
                      ${i === currentIdx ? 'bg-primary text-white' : ''}
                      ${i > currentIdx ? 'bg-fc-border text-fc-text-muted' : ''}
                    `}
                  >
                    {i < currentIdx ? (
                      <Check className="w-3 h-3" />
                    ) : (
                      i + 1
                    )}
                  </span>
                  <span className="hidden sm:inline">{label}</span>
                </div>
                {i < stepLabels.length - 1 && (
                  <ChevronRight className="w-3 h-3 text-fc-text-muted shrink-0" />
                )}
              </div>
            ))}
          </div>
        )}

        {/* Step 1: Event Type */}
        {currentStep === 'event-type' && (
          <EventTypeStep
            eventType={eventType}
            setEventType={setEventType}
            onNext={handleTypeNext}
            onTemplateSelect={(json: string) => {
              try {
                const data = JSON.parse(json)
                setBasics(prev => ({
                  ...prev,
                  title: data.title || prev.title,
                  description: data.description || prev.description,
                  location_name: data.location_name || prev.location_name,
                  location_address: data.location_address || prev.location_address,
                  has_rsvp: data.has_rsvp ?? prev.has_rsvp,
                }))
                if (data.event_type) setEventType(data.event_type)
                if (data.has_gift_exchange || data.has_potluck) {
                  setFeatures(prev => ({
                    ...prev,
                    giftExchange: { ...prev.giftExchange, enabled: !!data.has_gift_exchange },
                    potluck: { ...prev.potluck, enabled: !!data.has_potluck },
                  }))
                }
              } catch { /* ignore parse errors */ }
            }}
            bigMode={bigMode}
          />
        )}

        {/* Step 2: Event Basics */}
        {currentStep === 'basics' && (
          <EventBasicsStep
            eventType={eventType}
            basics={basics}
            setBasics={setBasics}
            onBack={() => setCurrentStep('event-type')}
            onNext={handleBasicsNext}
            bigMode={bigMode}
          />
        )}

        {/* Step 3a: Holiday Config */}
        {currentStep === 'holiday-config' && (
          <HolidayConfigStep
            config={holidayConfig}
            setConfig={setHolidayConfig}
            holidays={holidays}
            onBack={() => setCurrentStep('basics')}
            onNext={handleTypeConfigNext}
            bigMode={bigMode}
          />
        )}

        {/* Step 3b: Birthday Config */}
        {currentStep === 'birthday-config' && (
          <BirthdayConfigStep
            config={birthdayConfig}
            setConfig={setBirthdayConfig}
            familyMembers={familyMembers}
            eventDate={basics.event_date}
            onBack={() => setCurrentStep('basics')}
            onNext={handleTypeConfigNext}
            bigMode={bigMode}
          />
        )}

        {/* Step 3c: Baby Shower Config */}
        {currentStep === 'baby-shower-config' && (
          <BabyShowerConfigStep
            config={babyShowerConfig}
            setConfig={setBabyShowerConfig}
            onBack={() => setCurrentStep('basics')}
            onNext={handleTypeConfigNext}
            bigMode={bigMode}
          />
        )}

        {/* Step 3d: Wedding Config */}
        {currentStep === 'wedding-config' && (
          <WeddingConfigStep
            config={weddingConfig}
            setConfig={setWeddingConfig}
            onBack={() => setCurrentStep('basics')}
            onNext={handleTypeConfigNext}
            bigMode={bigMode}
          />
        )}

        {/* Step 4: Feature Selection */}
        {currentStep === 'features' && (
          <FeatureSelectionStep
            features={features}
            setFeatures={setFeatures}
            recurrenceType={recurrenceType}
            recurrenceEndDate={recurrenceEndDate}
            recurrenceMaxOccurrences={recurrenceMaxOccurrences}
            onRecurrenceChange={(field, value) => {
              if (field === 'recurrenceType') setRecurrenceType(value)
              else if (field === 'endDate') setRecurrenceEndDate(value)
              else if (field === 'maxOccurrences') setRecurrenceMaxOccurrences(value)
            }}
            onBack={() => setCurrentStep(getBackStepFromFeatures())}
            onNext={handleFeatureSelection}
            bigMode={bigMode}
          />
        )}

        {/* Step 5: Gift Exchange Setup */}
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

        {/* Step 6: Potluck Setup */}
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
