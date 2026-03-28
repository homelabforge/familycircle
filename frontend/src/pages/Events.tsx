import { useState } from 'react'
import { Calendar, ChevronRight, Loader2, TreePine, Cake, Baby, Heart } from 'lucide-react'
import { Link } from 'react-router-dom'
import BackButton from '@/components/BackButton'
import SubEventBadge from '@/components/events/SubEventBadge'
import { useBigMode } from '@/contexts/BigModeContext'
import { useEvents } from '@/hooks/queries/useEvents'
import { type Event, type EventType } from '@/lib/api'

const TYPE_FILTERS: { value: EventType | 'all'; label: string }[] = [
  { value: 'all', label: 'All' },
  { value: 'general', label: 'General' },
  { value: 'holiday', label: 'Holiday' },
  { value: 'birthday', label: 'Birthday' },
  { value: 'baby_shower', label: 'Baby Shower' },
  { value: 'wedding', label: 'Wedding' },
]

function EventTypeBadge({ event }: { event: Event }) {
  if (event.event_type === 'holiday') {
    return (
      <span className="flex items-center gap-1 text-xs bg-emerald-500/10 text-emerald-600 px-2 py-0.5 rounded-full font-medium">
        <TreePine className="w-3 h-3" />
        Holiday
      </span>
    )
  }
  if (event.event_type === 'birthday') {
    return (
      <span className="flex items-center gap-1 text-xs bg-amber-500/10 text-amber-600 px-2 py-0.5 rounded-full font-medium">
        <Cake className="w-3 h-3" />
        Birthday
      </span>
    )
  }
  if (event.event_type === 'baby_shower') {
    return (
      <span className="flex items-center gap-1 text-xs bg-rose-500/10 text-rose-600 px-2 py-0.5 rounded-full font-medium">
        <Baby className="w-3 h-3" />
        Baby Shower
      </span>
    )
  }
  if (event.event_type === 'wedding') {
    return (
      <span className="flex items-center gap-1 text-xs bg-violet-500/10 text-violet-600 px-2 py-0.5 rounded-full font-medium">
        <Heart className="w-3 h-3" />
        Wedding
      </span>
    )
  }
  return null
}

function getEventSubtitle(event: Event): string | null {
  if (event.event_type === 'holiday' && event.holiday_detail) {
    return event.holiday_detail.display_name
  }
  if (event.event_type === 'birthday' && event.birthday_detail) {
    const name = event.birthday_detail.birthday_person_name
    const age = event.birthday_detail.age_turning
    return age ? `${name} turns ${age}` : `${name}'s birthday`
  }
  if (event.event_type === 'baby_shower' && event.baby_shower_detail) {
    return event.baby_shower_detail.display_parents
  }
  if (event.event_type === 'wedding' && event.wedding_detail) {
    return event.wedding_detail.display_couple
  }
  return null
}

export default function Events() {
  const { bigMode } = useBigMode()
  const [typeFilter, setTypeFilter] = useState<EventType | 'all'>('all')
  const { data, isLoading: loading, error: queryError } = useEvents(
    typeFilter === 'all' ? undefined : typeFilter
  )
  const events = data?.events ?? []
  const error = queryError ? (queryError instanceof Error ? queryError.message : 'Failed to load events') : null

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr)
    return date.toLocaleDateString('en-US', {
      weekday: 'long',
      month: 'long',
      day: 'numeric',
      year: 'numeric',
    })
  }

  const formatTime = (dateStr: string) => {
    const date = new Date(dateStr)
    return date.toLocaleTimeString('en-US', {
      hour: 'numeric',
      minute: '2-digit',
    })
  }

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-6">
        <BackButton />
        <div className="flex items-center justify-center py-12">
          <Loader2 className="w-8 h-8 animate-spin text-primary" />
        </div>
      </div>
    )
  }

  return (
    <div className="container mx-auto px-4 py-6">
      <BackButton />

      <div className="mt-4">
        <h1
          className={`
            flex items-center gap-3 font-bold text-fc-text mb-4
            ${bigMode ? 'text-3xl' : 'text-2xl'}
          `}
        >
          <Calendar className={bigMode ? 'w-9 h-9' : 'w-7 h-7'} />
          Family Events
        </h1>

        {/* Type Filter Pills */}
        <div className="flex gap-2 mb-6 overflow-x-auto">
          {TYPE_FILTERS.map((f) => (
            <button
              key={f.value}
              onClick={() => setTypeFilter(f.value)}
              className={`
                px-3 py-1.5 rounded-full text-sm font-medium transition-colors whitespace-nowrap
                ${typeFilter === f.value
                  ? 'bg-primary text-white'
                  : 'bg-fc-surface border border-fc-border text-fc-text-muted hover:text-fc-text'
                }
              `}
            >
              {f.label}
            </button>
          ))}
        </div>

        {error && (
          <div className="bg-error/10 text-error px-4 py-3 rounded-xl mb-6">
            {error}
          </div>
        )}

        {events.length === 0 && !error && (
          <div className="text-center py-12">
            <Calendar className="w-16 h-16 text-fc-text-muted mx-auto mb-4" />
            <p className={`text-fc-text-muted ${bigMode ? 'text-lg' : ''}`}>
              No events scheduled yet.
            </p>
          </div>
        )}

        <div className="space-y-4">
          {events.map((event) => (
            <Link
              key={event.id}
              to={`/event/${event.id}`}
              className={`
                block bg-fc-surface rounded-2xl
                hover:bg-fc-surface-hover transition-colors relative
                ${bigMode ? 'p-6' : 'p-5'}
                ${event.is_cancelled
                  ? 'border-2 border-error/50 opacity-75'
                  : 'border border-fc-border'
                }
              `}
            >
              {/* Strikethrough line for cancelled events */}
              {event.is_cancelled && (
                <div className="absolute inset-0 flex items-center pointer-events-none">
                  <div className="w-full h-0.5 bg-error/40" />
                </div>
              )}

              <div className="flex items-center justify-between">
                <div>
                  <div className="flex items-center gap-2 mb-2 flex-wrap">
                    <h2
                      className={`
                        font-semibold
                        ${bigMode ? 'text-xl' : 'text-lg'}
                        ${event.is_cancelled ? 'text-fc-text-muted line-through' : 'text-fc-text'}
                      `}
                    >
                      {event.title}
                    </h2>
                    <EventTypeBadge event={event} />
                    {(event.sub_event_count ?? 0) > 0 && (
                      <SubEventBadge count={event.sub_event_count!} />
                    )}
                    {event.is_cancelled && (
                      <span className="text-xs bg-error/10 text-error px-2 py-1 rounded-full font-medium">
                        Cancelled
                      </span>
                    )}
                  </div>
                  {(() => {
                    const subtitle = getEventSubtitle(event)
                    return subtitle ? (
                      <p className={`text-fc-text-muted ${bigMode ? 'text-base' : 'text-sm'} ${event.is_cancelled ? 'line-through' : ''} mb-1`}>
                        {subtitle}
                      </p>
                    ) : null
                  })()}
                  <p className={`text-fc-text-muted ${bigMode ? 'text-base' : 'text-sm'} ${event.is_cancelled ? 'line-through' : ''}`}>
                    {formatDate(event.event_date)} @ {formatTime(event.event_date)}
                  </p>
                  {event.location_name && (
                    <p className={`text-fc-text-muted ${bigMode ? 'text-base' : 'text-sm'} ${event.is_cancelled ? 'line-through' : ''}`}>
                      {event.location_name}
                    </p>
                  )}

                  {!event.is_cancelled && (
                    <div className="flex gap-2 mt-3">
                      {event.has_gift_exchange && (
                        <span className="text-xs bg-primary/10 text-primary px-2 py-1 rounded-full">
                          Gift Exchange
                        </span>
                      )}
                      {event.has_potluck && (
                        <span className="text-xs bg-warning/10 text-warning px-2 py-1 rounded-full">
                          Potluck
                        </span>
                      )}
                      {event.user_rsvp && (
                        <span
                          className={`text-xs px-2 py-1 rounded-full ${
                            event.user_rsvp === 'yes'
                              ? 'bg-success/10 text-success'
                              : event.user_rsvp === 'maybe'
                                ? 'bg-warning/10 text-warning'
                                : 'bg-error/10 text-error'
                          }`}
                        >
                          RSVP: {event.user_rsvp}
                        </span>
                      )}
                    </div>
                  )}
                </div>
                <div className="flex items-center gap-3">
                  {!event.is_cancelled && (
                    <div className="text-right">
                      <div className={`text-fc-text-muted ${bigMode ? 'text-sm' : 'text-xs'}`}>
                        {event.rsvp_counts.yes} attending
                      </div>
                    </div>
                  )}
                  <ChevronRight className="w-6 h-6 text-fc-text-muted" />
                </div>
              </div>
            </Link>
          ))}
        </div>
      </div>
    </div>
  )
}
