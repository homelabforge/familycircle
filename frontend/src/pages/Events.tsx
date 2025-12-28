import { useEffect, useState } from 'react'
import { Calendar, ChevronRight, Loader2 } from 'lucide-react'
import { Link } from 'react-router-dom'
import BackButton from '@/components/BackButton'
import { useBigMode } from '@/contexts/BigModeContext'
import { eventsApi, type Event } from '@/lib/api'

export default function Events() {
  const { bigMode } = useBigMode()
  const [events, setEvents] = useState<Event[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadEvents()
  }, [])

  const loadEvents = async () => {
    try {
      setLoading(true)
      setError(null)
      const response = await eventsApi.list()
      setEvents(response.events)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load events')
    } finally {
      setLoading(false)
    }
  }

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
            flex items-center gap-3 font-bold text-fc-text mb-6
            ${bigMode ? 'text-3xl' : 'text-2xl'}
          `}
        >
          <Calendar className={bigMode ? 'w-9 h-9' : 'w-7 h-7'} />
          Family Events
        </h1>

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
                  <div className="flex items-center gap-2 mb-2">
                    <h2
                      className={`
                        font-semibold
                        ${bigMode ? 'text-xl' : 'text-lg'}
                        ${event.is_cancelled ? 'text-fc-text-muted line-through' : 'text-fc-text'}
                      `}
                    >
                      {event.title}
                    </h2>
                    {event.is_cancelled && (
                      <span className="text-xs bg-error/10 text-error px-2 py-1 rounded-full font-medium">
                        Cancelled
                      </span>
                    )}
                  </div>
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
                      {event.has_secret_santa && (
                        <span className="text-xs bg-primary/10 text-primary px-2 py-1 rounded-full">
                          Secret Santa
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
