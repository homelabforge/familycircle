import {
  TreePine, Check, Calendar, Cake, Baby, Heart,
} from 'lucide-react'
import type { EventType } from '@/lib/api'
import EventTemplateSelector from '@/components/events/EventTemplateSelector'

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

interface EventTypeStepProps {
  eventType: EventType
  setEventType: (t: EventType) => void
  onNext: () => void
  onTemplateSelect: (json: string) => void
  bigMode: boolean
}

export default function EventTypeStep({
  eventType,
  setEventType,
  onNext,
  onTemplateSelect,
  bigMode,
}: EventTypeStepProps) {
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
