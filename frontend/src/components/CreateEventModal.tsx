import { useEffect, useState } from 'react'
import {
  X, Loader2, TreePine, UtensilsCrossed, Check, Calendar, Cake,
  EyeOff, ChevronRight, Baby, Heart,
} from 'lucide-react'
import { toast } from 'sonner'
import { useBigMode } from '@/contexts/BigModeContext'
import { eventsApi, familyApi } from '@/lib/api'
import type { EventType, FamilyMember } from '@/lib/api'
import WeddingTemplateSelector from '@/components/events/WeddingTemplateSelector'
import RecurrenceSelector from '@/components/events/RecurrenceSelector'
import EventTemplateSelector from '@/components/events/EventTemplateSelector'

interface CreateEventModalProps {
  isOpen: boolean
  onClose: () => void
  onEventCreated?: () => void
}

type WizardStep =
  | 'event-type'
  | 'basics'
  | 'holiday-config'
  | 'birthday-config'
  | 'baby-shower-config'
  | 'wedding-config'
  | 'features'
  | 'gift-exchange'
  | 'potluck'

interface EventBasics {
  title: string
  description: string
  event_date: string
  location_name: string
  location_address: string
  has_rsvp: boolean
}

interface HolidayConfig {
  holiday_name: string
  custom_holiday_name: string
  year: string
}

interface BirthdayConfig {
  birthday_person_id: string
  birthday_person_name: string
  birth_date: string
  age_turning: string
  is_secret: boolean
  theme: string
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

const emptyHolidayConfig: HolidayConfig = {
  holiday_name: '',
  custom_holiday_name: '',
  year: '',
}

interface BabyShowerConfig {
  parent1_name: string
  parent2_name: string
  baby_name: string
  gender: string
  due_date: string
  registry_url: string
  is_gender_reveal: boolean
}

interface WeddingConfig {
  partner1_name: string
  partner2_name: string
  wedding_date: string
  venue_name: string
  registry_url: string
  color_theme: string
  sub_event_template: string
}

const emptyBirthdayConfig: BirthdayConfig = {
  birthday_person_id: '',
  birthday_person_name: '',
  birth_date: '',
  age_turning: '',
  is_secret: false,
  theme: '',
}

const emptyBabyShowerConfig: BabyShowerConfig = {
  parent1_name: '',
  parent2_name: '',
  baby_name: '',
  gender: '',
  due_date: '',
  registry_url: '',
  is_gender_reveal: false,
}

const emptyWeddingConfig: WeddingConfig = {
  partner1_name: '',
  partner2_name: '',
  wedding_date: '',
  venue_name: '',
  registry_url: '',
  color_theme: '',
  sub_event_template: '',
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

function getStepLabels(eventType: EventType, features: FeatureConfig): string[] {
  const steps = ['Type', 'Details']
  if (eventType === 'holiday') steps.push('Holiday')
  if (eventType === 'birthday') steps.push('Birthday')
  if (eventType === 'baby_shower') steps.push('Baby Shower')
  if (eventType === 'wedding') steps.push('Wedding')
  steps.push('Features')
  if (features.giftExchange.enabled) steps.push('Gift Exchange')
  if (features.potluck.enabled) steps.push('Potluck')
  return steps
}

function getStepIndex(
  step: WizardStep,
  eventType: EventType,
  features: FeatureConfig
): number {
  const map: Record<string, number> = { 'event-type': 0, basics: 1 }
  let idx = 2
  if (eventType === 'holiday') {
    map['holiday-config'] = idx++
  }
  if (eventType === 'birthday') {
    map['birthday-config'] = idx++
  }
  if (eventType === 'baby_shower') {
    map['baby-shower-config'] = idx++
  }
  if (eventType === 'wedding') {
    map['wedding-config'] = idx++
  }
  map['features'] = idx++
  if (features.giftExchange.enabled) {
    map['gift-exchange'] = idx++
  }
  if (features.potluck.enabled) {
    map['potluck'] = idx
  }
  return map[step] ?? 0
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

      const payload: Parameters<typeof eventsApi.create>[0] = {
        title: basics.title,
        description: basics.description || undefined,
        event_date: basics.event_date,
        location_name: basics.location_name || undefined,
        location_address: basics.location_address || undefined,
        has_secret_santa: features.giftExchange.enabled,
        has_potluck: features.potluck.enabled,
        has_rsvp: basics.has_rsvp,
        event_type: eventType,
        ...(features.giftExchange.enabled && {
          secret_santa_budget_min: features.giftExchange.budget_min
            ? parseInt(features.giftExchange.budget_min)
            : undefined,
          secret_santa_budget_max: features.giftExchange.budget_max
            ? parseInt(features.giftExchange.budget_max)
            : undefined,
          secret_santa_notes: features.giftExchange.notes || undefined,
        }),
        ...(features.potluck.enabled && {
          potluck_mode: features.potluck.mode,
          potluck_host_providing: features.potluck.hostProviding || undefined,
        }),
      }

      // Add recurrence if set
      if (recurrenceType) {
        payload.recurrence_type = recurrenceType
        if (recurrenceEndDate) {
          payload.recurrence_end_date = recurrenceEndDate
        }
        if (recurrenceMaxOccurrences) {
          payload.recurrence_max_occurrences = parseInt(recurrenceMaxOccurrences)
        }
      }

      // Add type-specific details
      if (eventType === 'holiday' && holidayConfig.holiday_name) {
        payload.holiday_detail = {
          holiday_name: holidayConfig.holiday_name,
          custom_holiday_name:
            holidayConfig.holiday_name === 'custom'
              ? holidayConfig.custom_holiday_name || undefined
              : undefined,
          year: holidayConfig.year ? parseInt(holidayConfig.year) : undefined,
        }
      }

      if (eventType === 'birthday' && birthdayConfig.birthday_person_name) {
        payload.birthday_detail = {
          birthday_person_id: birthdayConfig.birthday_person_id || undefined,
          birthday_person_name: birthdayConfig.birthday_person_name,
          birth_date: birthdayConfig.birth_date || undefined,
          age_turning: birthdayConfig.age_turning
            ? parseInt(birthdayConfig.age_turning)
            : undefined,
          is_secret: birthdayConfig.is_secret,
          theme: birthdayConfig.theme || undefined,
        }
      }

      if (eventType === 'baby_shower' && babyShowerConfig.parent1_name) {
        payload.baby_shower_detail = {
          parent1_name: babyShowerConfig.parent1_name,
          parent2_name: babyShowerConfig.parent2_name || undefined,
          baby_name: babyShowerConfig.baby_name || undefined,
          gender: babyShowerConfig.gender || undefined,
          due_date: babyShowerConfig.due_date || undefined,
          registry_url: babyShowerConfig.registry_url || undefined,
          is_gender_reveal: babyShowerConfig.is_gender_reveal,
        }
      }

      if (eventType === 'wedding' && weddingConfig.partner1_name) {
        payload.wedding_detail = {
          partner1_name: weddingConfig.partner1_name,
          partner2_name: weddingConfig.partner2_name,
          wedding_date: weddingConfig.wedding_date || undefined,
          venue_name: weddingConfig.venue_name || undefined,
          registry_url: weddingConfig.registry_url || undefined,
          color_theme: weddingConfig.color_theme || undefined,
          sub_event_template: weddingConfig.sub_event_template || undefined,
        }
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
                if (data.has_secret_santa || data.has_potluck) {
                  setFeatures(prev => ({
                    ...prev,
                    giftExchange: { ...prev.giftExchange, enabled: !!data.has_secret_santa },
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

// ============================================================================
// Event Type Selection Step
// ============================================================================

const EVENT_TYPE_CARDS = [
  {
    type: 'general' as EventType,
    icon: Calendar,
    title: 'General',
    description: 'Family gathering, game night, or any occasion',
    color: 'text-blue-500',
    bgColor: 'bg-blue-500/10',
    borderColor: 'border-blue-500',
  },
  {
    type: 'holiday' as EventType,
    icon: TreePine,
    title: 'Holiday',
    description: 'Christmas, Thanksgiving, Easter, and more',
    color: 'text-emerald-500',
    bgColor: 'bg-emerald-500/10',
    borderColor: 'border-emerald-500',
  },
  {
    type: 'birthday' as EventType,
    icon: Cake,
    title: 'Birthday',
    description: 'Celebrate a family member with optional surprise mode',
    color: 'text-amber-500',
    bgColor: 'bg-amber-500/10',
    borderColor: 'border-amber-500',
  },
  {
    type: 'baby_shower' as EventType,
    icon: Baby,
    title: 'Baby Shower',
    description: 'Celebrate an upcoming arrival',
    color: 'text-rose-500',
    bgColor: 'bg-rose-500/10',
    borderColor: 'border-rose-500',
  },
  {
    type: 'wedding' as EventType,
    icon: Heart,
    title: 'Wedding',
    description: 'Plan the big day with sub-events',
    color: 'text-violet-500',
    bgColor: 'bg-violet-500/10',
    borderColor: 'border-violet-500',
  },
]

function EventTypeStep({
  eventType,
  setEventType,
  onNext,
  onTemplateSelect,
  bigMode,
}: {
  eventType: EventType
  setEventType: (t: EventType) => void
  onNext: () => void
  onTemplateSelect: (json: string) => void
  bigMode: boolean
}) {
  return (
    <>
      <h2
        className={`font-bold text-fc-text mb-2 ${bigMode ? 'text-2xl' : 'text-xl'}`}
      >
        What kind of event?
      </h2>
      <p className="text-fc-text-muted mb-6">
        Choose the type of event you're planning
      </p>

      {/* Template selector */}
      <div className="mb-6">
        <EventTemplateSelector
          onSelect={(json) => {
            if (json) onTemplateSelect(json)
          }}
        />
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 mb-6">
        {EVENT_TYPE_CARDS.map((card) => {
          const Icon = card.icon
          const isSelected = eventType === card.type
          return (
            <button
              key={card.type}
              onClick={() => setEventType(card.type)}
              className={`
                relative p-5 rounded-2xl border-2 transition-all text-left
                ${isSelected
                  ? `${card.borderColor} ${card.bgColor}`
                  : 'border-fc-border bg-fc-surface hover:bg-fc-surface-hover'
                }
              `}
            >
              {isSelected && (
                <div className="absolute top-3 right-3 w-6 h-6 bg-primary rounded-full flex items-center justify-center">
                  <Check className="w-4 h-4 text-white" />
                </div>
              )}
              <Icon
                className={`w-8 h-8 mb-2 ${isSelected ? card.color : 'text-fc-text-muted'}`}
              />
              <h3 className="font-semibold text-fc-text mb-1 text-sm">{card.title}</h3>
              <p className="text-xs text-fc-text-muted leading-tight">{card.description}</p>
            </button>
          )
        })}
      </div>

      <div className="flex justify-end">
        <button
          onClick={onNext}
          className="px-6 py-2 bg-primary text-white rounded-xl hover:bg-primary-hover transition-colors"
        >
          Next
        </button>
      </div>
    </>
  )
}

// ============================================================================
// Event Basics Step
// ============================================================================

const TYPE_LABELS: Record<EventType, string> = {
  general: 'Event',
  holiday: 'Holiday Event',
  birthday: 'Birthday Party',
  baby_shower: 'Baby Shower',
  wedding: 'Wedding',
}

function EventBasicsStep({
  eventType,
  basics,
  setBasics,
  onBack,
  onNext,
  bigMode,
}: {
  eventType: EventType
  basics: EventBasics
  setBasics: (b: EventBasics) => void
  onBack: () => void
  onNext: () => void
  bigMode: boolean
}) {
  return (
    <>
      <h2
        className={`font-bold text-fc-text mb-6 ${bigMode ? 'text-2xl' : 'text-xl'}`}
      >
        {TYPE_LABELS[eventType]} Details
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
            placeholder={
              eventType === 'holiday'
                ? 'e.g., Family Christmas Party'
                : eventType === 'birthday'
                  ? "e.g., Mom's 60th Birthday"
                  : 'e.g., Family Game Night'
            }
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

        <div className="flex gap-3 justify-end pt-4">
          <button
            type="button"
            onClick={onBack}
            className="px-4 py-2 text-fc-text-muted hover:text-fc-text transition-colors"
          >
            Back
          </button>
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

// ============================================================================
// Holiday Config Step
// ============================================================================

function HolidayConfigStep({
  config,
  setConfig,
  holidays,
  onBack,
  onNext,
  bigMode,
}: {
  config: HolidayConfig
  setConfig: (c: HolidayConfig) => void
  holidays: string[]
  onBack: () => void
  onNext: () => void
  bigMode: boolean
}) {
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

// ============================================================================
// Birthday Config Step
// ============================================================================

function BirthdayConfigStep({
  config,
  setConfig,
  familyMembers,
  eventDate,
  onBack,
  onNext,
  bigMode,
}: {
  config: BirthdayConfig
  setConfig: (c: BirthdayConfig) => void
  familyMembers: FamilyMember[]
  eventDate: string
  onBack: () => void
  onNext: () => void
  bigMode: boolean
}) {
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

// ============================================================================
// Baby Shower Config Step
// ============================================================================

const GENDER_OPTIONS = [
  { value: '', label: 'Not sharing' },
  { value: 'boy', label: 'Boy' },
  { value: 'girl', label: 'Girl' },
  { value: 'surprise', label: "It's a Surprise!" },
  { value: 'unknown', label: "Don't Know Yet" },
]

function BabyShowerConfigStep({
  config,
  setConfig,
  onBack,
  onNext,
  bigMode,
}: {
  config: BabyShowerConfig
  setConfig: (c: BabyShowerConfig) => void
  onBack: () => void
  onNext: () => void
  bigMode: boolean
}) {
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

// ============================================================================
// Wedding Config Step
// ============================================================================

function WeddingConfigStep({
  config,
  setConfig,
  onBack,
  onNext,
  bigMode,
}: {
  config: WeddingConfig
  setConfig: (c: WeddingConfig) => void
  onBack: () => void
  onNext: () => void
  bigMode: boolean
}) {
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

// ============================================================================
// Feature Selection Step
// ============================================================================

function FeatureSelectionStep({
  features,
  setFeatures,
  recurrenceType,
  recurrenceEndDate,
  recurrenceMaxOccurrences,
  onRecurrenceChange,
  onBack,
  onNext,
  bigMode,
}: {
  features: FeatureConfig
  setFeatures: (f: FeatureConfig) => void
  recurrenceType: string
  recurrenceEndDate: string
  recurrenceMaxOccurrences: string
  onRecurrenceChange: (field: string, value: string) => void
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

// ============================================================================
// Gift Exchange Setup Step
// ============================================================================

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
            {saving ? 'Creating...' : potluckEnabled ? 'Next' : 'Create Event'}
          </button>
        </div>
      </form>
    </>
  )
}

// ============================================================================
// Potluck Setup Step
// ============================================================================

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
