import { Calendar, CheckCircle, HelpCircle, XCircle } from 'lucide-react'
import { useBigMode } from '@/contexts/BigModeContext'
import { Link } from 'react-router-dom'

interface UpcomingEvent {
  id: string
  title: string
  date: string
  time: string
  rsvpStatus?: 'yes' | 'no' | 'maybe' | null
}

interface UpcomingEventsProps {
  events: UpcomingEvent[]
}

export default function UpcomingEvents({ events }: UpcomingEventsProps) {
  const { bigMode } = useBigMode()

  if (events.length === 0) {
    return null
  }

  const getRsvpIcon = (status: UpcomingEvent['rsvpStatus']) => {
    switch (status) {
      case 'yes':
        return <CheckCircle className="w-5 h-5 text-success" />
      case 'no':
        return <XCircle className="w-5 h-5 text-error" />
      case 'maybe':
        return <HelpCircle className="w-5 h-5 text-warning" />
      default:
        return null
    }
  }

  const getRsvpLabel = (status: UpcomingEvent['rsvpStatus']) => {
    switch (status) {
      case 'yes':
        return 'Going'
      case 'no':
        return 'Not Going'
      case 'maybe':
        return 'Maybe'
      default:
        return 'RSVP Needed'
    }
  }

  return (
    <div className={`mt-8 ${bigMode ? 'mt-10' : ''}`}>
      <h2
        className={`
          flex items-center gap-2 font-semibold text-fc-text mb-4
          ${bigMode ? 'text-xl' : 'text-lg'}
        `}
      >
        <Calendar className={bigMode ? 'w-6 h-6' : 'w-5 h-5'} />
        Upcoming Events
      </h2>

      <div className="space-y-3">
        {events.map((event) => (
          <Link
            key={event.id}
            to={`/event/${event.id}`}
            className={`
              block bg-fc-surface border border-fc-border rounded-xl
              hover:bg-fc-surface-hover transition-colors
              ${bigMode ? 'p-5' : 'p-4'}
            `}
          >
            <div className="flex items-center justify-between">
              <div>
                <h3
                  className={`
                    font-medium text-fc-text
                    ${bigMode ? 'text-lg' : 'text-base'}
                  `}
                >
                  {event.title}
                </h3>
                <p
                  className={`
                    text-fc-text-muted
                    ${bigMode ? 'text-base' : 'text-sm'}
                  `}
                >
                  {event.date} @ {event.time}
                </p>
              </div>

              <div className="flex items-center gap-2">
                {getRsvpIcon(event.rsvpStatus)}
                <span
                  className={`
                    text-fc-text-muted
                    ${bigMode ? 'text-base' : 'text-sm'}
                    ${!event.rsvpStatus ? 'text-warning font-medium' : ''}
                  `}
                >
                  {getRsvpLabel(event.rsvpStatus)}
                </span>
              </div>
            </div>
          </Link>
        ))}
      </div>
    </div>
  )
}
