import type { EventType } from '@/lib/api'
import type { EventBasics } from './types'

const TYPE_LABELS: Record<EventType, string> = {
  general: 'Event',
  holiday: 'Holiday Event',
  birthday: 'Birthday Party',
  baby_shower: 'Baby Shower',
  wedding: 'Wedding',
}

interface EventBasicsStepProps {
  eventType: EventType
  basics: EventBasics
  setBasics: (b: EventBasics) => void
  onBack: () => void
  onNext: () => void
  bigMode: boolean
}

export default function EventBasicsStep({
  eventType,
  basics,
  setBasics,
  onBack,
  onNext,
  bigMode,
}: EventBasicsStepProps) {
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
