import { useEffect, useState } from 'react'
import { useParams, Link, useNavigate } from 'react-router-dom'
import { Calendar, MapPin, Clock, Check, X, HelpCircle, Loader2, TreePine, UtensilsCrossed, AlertTriangle, Ban, Heart, ChevronDown, ChevronUp } from 'lucide-react'
import BackButton from '@/components/BackButton'
import { useBigMode } from '@/contexts/BigModeContext'
import { eventsApi, type EventDetail as EventDetailType } from '@/lib/api'

// Cancel confirmation modal
function CancelEventModal({
  isOpen,
  onClose,
  onConfirm,
  loading,
}: {
  isOpen: boolean
  onClose: () => void
  onConfirm: (reason: string) => void
  loading: boolean
}) {
  const [reason, setReason] = useState('')

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-fc-surface border border-fc-border rounded-2xl p-6 max-w-md w-full">
        <div className="flex items-center gap-3 mb-4">
          <AlertTriangle className="w-6 h-6 text-error" />
          <h2 className="text-xl font-bold text-fc-text">Cancel Event</h2>
        </div>

        <p className="text-fc-text-muted mb-4">
          Are you sure you want to cancel this event? This action cannot be undone.
        </p>

        <div className="mb-6">
          <label className="block text-sm font-medium text-fc-text mb-2">
            Cancellation Reason (optional)
          </label>
          <textarea
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            className="w-full px-4 py-3 bg-fc-bg border border-fc-border rounded-xl text-fc-text focus:outline-none focus:ring-2 focus:ring-primary"
            rows={3}
            placeholder="e.g., Weather conditions, scheduling conflict..."
          />
        </div>

        <div className="flex gap-3 justify-end">
          <button
            onClick={onClose}
            disabled={loading}
            className="px-4 py-2 text-fc-text-muted hover:text-fc-text transition-colors"
          >
            Keep Event
          </button>
          <button
            onClick={() => onConfirm(reason)}
            disabled={loading}
            className="px-4 py-2 bg-error text-white rounded-xl hover:bg-error/90 transition-colors disabled:opacity-50"
          >
            {loading ? 'Cancelling...' : 'Cancel Event'}
          </button>
        </div>
      </div>
    </div>
  )
}

// Health summary type
interface HealthSummary {
  event_id: string
  attendee_count: number
  shared_count: number
  allergies: string[]
  dietary_restrictions: string[]
  medical_needs: string[]
  mobility_notes: string[]
}

// Health Summary Section Component
function HealthSummarySection({
  eventId,
  canManage,
  bigMode,
}: {
  eventId: string
  canManage: boolean
  bigMode: boolean
}) {
  const [healthSummary, setHealthSummary] = useState<HealthSummary | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [isExpanded, setIsExpanded] = useState(false)

  // Only show for managers
  if (!canManage) return null

  const loadHealthSummary = async () => {
    if (healthSummary) {
      // Toggle visibility if already loaded
      setIsExpanded(!isExpanded)
      return
    }

    try {
      setLoading(true)
      setError(null)
      const data = await eventsApi.getHealthSummary(eventId)
      setHealthSummary(data)
      setIsExpanded(true)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load health summary')
    } finally {
      setLoading(false)
    }
  }

  const hasHealthInfo = healthSummary && (
    healthSummary.allergies.length > 0 ||
    healthSummary.dietary_restrictions.length > 0 ||
    healthSummary.medical_needs.length > 0 ||
    healthSummary.mobility_notes.length > 0
  )

  return (
    <div className="bg-fc-surface border border-fc-border rounded-2xl p-6 mb-6">
      <button
        onClick={loadHealthSummary}
        disabled={loading}
        className={`
          w-full flex items-center justify-between
          ${bigMode ? 'text-xl' : 'text-lg'}
        `}
      >
        <div className="flex items-center gap-3">
          <Heart className={`text-primary ${bigMode ? 'w-6 h-6' : 'w-5 h-5'}`} />
          <span className="font-semibold text-fc-text">Health Notes</span>
          {healthSummary && (
            <span className="text-sm text-fc-text-muted">
              ({healthSummary.shared_count} of {healthSummary.attendee_count} attendees shared)
            </span>
          )}
        </div>
        {loading ? (
          <Loader2 className="w-5 h-5 animate-spin text-primary" />
        ) : isExpanded ? (
          <ChevronUp className="w-5 h-5 text-fc-text-muted" />
        ) : (
          <ChevronDown className="w-5 h-5 text-fc-text-muted" />
        )}
      </button>

      {error && (
        <div className="mt-4 text-error text-sm">{error}</div>
      )}

      {isExpanded && healthSummary && (
        <div className={`mt-4 pt-4 border-t border-fc-border ${bigMode ? 'text-base' : 'text-sm'}`}>
          {!hasHealthInfo ? (
            <p className="text-fc-text-muted italic">
              No health information shared by attendees.
            </p>
          ) : (
            <div className="space-y-4">
              {healthSummary.allergies.length > 0 && (
                <div>
                  <h4 className="font-medium text-fc-text mb-2">Allergies</h4>
                  <div className="flex flex-wrap gap-2">
                    {healthSummary.allergies.map((item, idx) => (
                      <span
                        key={idx}
                        className="px-3 py-1 bg-error/10 text-error rounded-full text-sm"
                      >
                        Someone has: {item}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {healthSummary.dietary_restrictions.length > 0 && (
                <div>
                  <h4 className="font-medium text-fc-text mb-2">Dietary Restrictions</h4>
                  <div className="flex flex-wrap gap-2">
                    {healthSummary.dietary_restrictions.map((item, idx) => (
                      <span
                        key={idx}
                        className="px-3 py-1 bg-warning/10 text-warning rounded-full text-sm"
                      >
                        Someone is: {item}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {healthSummary.medical_needs.length > 0 && (
                <div>
                  <h4 className="font-medium text-fc-text mb-2">Medical Needs</h4>
                  <ul className="space-y-1 text-fc-text-muted">
                    {healthSummary.medical_needs.map((item, idx) => (
                      <li key={idx} className="flex items-start gap-2">
                        <span className="text-primary">•</span>
                        <span>Someone has: {item}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {healthSummary.mobility_notes.length > 0 && (
                <div>
                  <h4 className="font-medium text-fc-text mb-2">Mobility Notes</h4>
                  <ul className="space-y-1 text-fc-text-muted">
                    {healthSummary.mobility_notes.map((item, idx) => (
                      <li key={idx} className="flex items-start gap-2">
                        <span className="text-primary">•</span>
                        <span>Someone needs: {item}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              <p className="text-xs text-fc-text-muted italic mt-4">
                Health information is shared anonymously by attendees who opted in.
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default function EventDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { bigMode } = useBigMode()
  const [event, setEvent] = useState<EventDetailType | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [rsvpLoading, setRsvpLoading] = useState(false)
  const [showCancelModal, setShowCancelModal] = useState(false)
  const [cancelLoading, setCancelLoading] = useState(false)

  useEffect(() => {
    if (id) {
      loadEvent()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id])

  const loadEvent = async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await eventsApi.get(id!)
      setEvent(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load event')
    } finally {
      setLoading(false)
    }
  }

  const handleRsvp = async (status: 'yes' | 'no' | 'maybe') => {
    if (!event || event.is_cancelled) return
    try {
      setRsvpLoading(true)
      // If clicking the same status, remove RSVP
      if (event.user_rsvp === status) {
        await eventsApi.removeRsvp(event.id)
      } else {
        await eventsApi.rsvp(event.id, status)
      }
      await loadEvent() // Reload to get updated counts
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update RSVP')
    } finally {
      setRsvpLoading(false)
    }
  }

  const handleCancelEvent = async (reason: string) => {
    if (!event) return
    try {
      setCancelLoading(true)
      await eventsApi.cancel(event.id, reason || undefined)
      setShowCancelModal(false)
      // Redirect to dashboard after canceling
      navigate('/')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to cancel event')
    } finally {
      setCancelLoading(false)
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
        <BackButton to="/events" label="Back to Events" />
        <div className="flex items-center justify-center py-12">
          <Loader2 className="w-8 h-8 animate-spin text-primary" />
        </div>
      </div>
    )
  }

  if (error || !event) {
    return (
      <div className="container mx-auto px-4 py-6">
        <BackButton to="/events" label="Back to Events" />
        <div className="bg-error/10 text-error px-4 py-3 rounded-xl mt-4">
          {error || 'Event not found'}
        </div>
      </div>
    )
  }

  return (
    <div className="container mx-auto px-4 py-6">
      <BackButton to="/events" label="Back to Events" />

      <div className="mt-4">
        {/* Title with Cancel Button */}
        <div className="flex items-start justify-between gap-4 mb-6">
          <h1
            className={`
              font-bold text-fc-text
              ${bigMode ? 'text-3xl' : 'text-2xl'}
              ${event.is_cancelled ? 'line-through opacity-60' : ''}
            `}
          >
            {event.title}
          </h1>

          {/* Cancel button for admins - only show if not cancelled */}
          {event.can_manage && !event.is_cancelled && (
            <button
              onClick={() => setShowCancelModal(true)}
              className={`
                flex items-center gap-2 px-4 py-2
                border-2 border-error text-error rounded-xl
                hover:bg-error hover:text-white transition-colors
                flex-shrink-0
                ${bigMode ? 'text-lg' : 'text-sm'}
              `}
            >
              <Ban className={bigMode ? 'w-5 h-5' : 'w-4 h-4'} />
              Cancel Event
            </button>
          )}
        </div>

        {/* Cancelled Banner */}
        {event.is_cancelled && (
          <div className={`
            bg-error/10 border border-error/30 rounded-xl p-4 mb-6
            ${bigMode ? 'text-lg' : ''}
          `}>
            <div className="flex items-center gap-3">
              <Ban className="w-6 h-6 text-error flex-shrink-0" />
              <div>
                <p className="font-semibold text-error">This event has been cancelled</p>
                {event.cancellation_reason && (
                  <p className="text-fc-text-muted mt-1">
                    Reason: {event.cancellation_reason}
                  </p>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Event Details Card */}
        <div className="bg-fc-surface border border-fc-border rounded-2xl p-6 mb-6">
          <div className={`space-y-4 ${bigMode ? 'text-lg' : ''}`}>
            <div className="flex items-center gap-3 text-fc-text">
              <Calendar className="w-5 h-5 text-primary" />
              <span>{formatDate(event.event_date)}</span>
            </div>
            <div className="flex items-center gap-3 text-fc-text">
              <Clock className="w-5 h-5 text-primary" />
              <span>{formatTime(event.event_date)}</span>
            </div>
            {(event.location_name || event.location_address) && (
              <div className="flex items-start gap-3 text-fc-text">
                <MapPin className="w-5 h-5 text-primary flex-shrink-0 mt-0.5" />
                <div>
                  {event.location_name && <p>{event.location_name}</p>}
                  {event.location_address && (
                    <p className="text-fc-text-muted text-sm">{event.location_address}</p>
                  )}
                </div>
              </div>
            )}
          </div>

          {event.description && (
            <p className={`mt-6 text-fc-text-muted ${bigMode ? 'text-base' : 'text-sm'}`}>
              {event.description}
            </p>
          )}

          <div className="flex flex-wrap gap-2 mt-4">
            {event.has_secret_santa && (
              <span className="text-sm bg-primary/10 text-primary px-3 py-1 rounded-full">
                Gift Exchange
              </span>
            )}
            {event.has_potluck && (
              <span className="text-sm bg-warning/10 text-warning px-3 py-1 rounded-full">
                Potluck
              </span>
            )}
          </div>

          {/* Feature Links */}
          {(event.has_secret_santa || event.has_potluck) && (
            <div className="flex flex-wrap gap-3 mt-6 pt-4 border-t border-fc-border">
              {event.has_secret_santa && (
                <Link
                  to={`/gift-exchange/${event.id}`}
                  className={`
                    flex items-center gap-2 bg-primary/10 text-primary rounded-xl
                    hover:bg-primary/20 transition-colors
                    ${bigMode ? 'px-5 py-3 text-lg' : 'px-4 py-2'}
                  `}
                >
                  <TreePine className={bigMode ? 'w-5 h-5' : 'w-4 h-4'} />
                  Gift Exchange
                </Link>
              )}
              {event.has_potluck && (
                <Link
                  to={`/potluck/${event.id}`}
                  className={`
                    flex items-center gap-2 bg-warning/10 text-warning rounded-xl
                    hover:bg-warning/20 transition-colors
                    ${bigMode ? 'px-5 py-3 text-lg' : 'px-4 py-2'}
                  `}
                >
                  <UtensilsCrossed className={bigMode ? 'w-5 h-5' : 'w-4 h-4'} />
                  Potluck
                </Link>
              )}
            </div>
          )}
        </div>

        {/* RSVP Section - Hide if cancelled */}
        {!event.is_cancelled && (
          <div className="bg-fc-surface border border-fc-border rounded-2xl p-6 mb-6">
            <h2
              className={`
                font-semibold text-fc-text mb-4
                ${bigMode ? 'text-xl' : 'text-lg'}
              `}
            >
              Will you attend?
            </h2>

            <div className={`grid gap-3 ${bigMode ? 'grid-cols-1 sm:grid-cols-3' : 'grid-cols-3'}`}>
              <button
                onClick={() => handleRsvp('yes')}
                disabled={rsvpLoading}
                className={`
                  flex items-center justify-center gap-2
                  border-2 border-success text-success rounded-xl
                  hover:bg-success hover:text-white transition-colors
                  disabled:opacity-50 disabled:cursor-not-allowed
                  ${bigMode ? 'px-6 py-4 text-lg' : 'px-4 py-3'}
                  ${event.user_rsvp === 'yes' ? 'bg-success text-white' : ''}
                `}
              >
                <Check className={bigMode ? 'w-6 h-6' : 'w-5 h-5'} />
                Yes
              </button>
              <button
                onClick={() => handleRsvp('maybe')}
                disabled={rsvpLoading}
                className={`
                  flex items-center justify-center gap-2
                  border-2 border-warning text-warning rounded-xl
                  hover:bg-warning hover:text-white transition-colors
                  disabled:opacity-50 disabled:cursor-not-allowed
                  ${bigMode ? 'px-6 py-4 text-lg' : 'px-4 py-3'}
                  ${event.user_rsvp === 'maybe' ? 'bg-warning text-white' : ''}
                `}
              >
                <HelpCircle className={bigMode ? 'w-6 h-6' : 'w-5 h-5'} />
                Maybe
              </button>
              <button
                onClick={() => handleRsvp('no')}
                disabled={rsvpLoading}
                className={`
                  flex items-center justify-center gap-2
                  border-2 border-error text-error rounded-xl
                hover:bg-error hover:text-white transition-colors
                disabled:opacity-50 disabled:cursor-not-allowed
                ${bigMode ? 'px-6 py-4 text-lg' : 'px-4 py-3'}
                ${event.user_rsvp === 'no' ? 'bg-error text-white' : ''}
              `}
            >
              <X className={bigMode ? 'w-6 h-6' : 'w-5 h-5'} />
              No
            </button>
          </div>
        </div>
        )}

        {/* Attendees */}
        {event.rsvps && event.rsvps.length > 0 && (
          <div className="bg-fc-surface border border-fc-border rounded-2xl p-6 mb-6">
            <h2
              className={`
                font-semibold text-fc-text mb-4
                ${bigMode ? 'text-xl' : 'text-lg'}
              `}
            >
              RSVPs ({event.rsvps.length})
            </h2>
            <div className="space-y-2">
              {event.rsvps.map((rsvp, idx) => (
                <div
                  key={idx}
                  className={`flex items-center justify-between ${bigMode ? 'py-2' : 'py-1'}`}
                >
                  <span className={`text-fc-text ${bigMode ? 'text-lg' : ''}`}>
                    {rsvp.display_name}
                  </span>
                  <span
                    className={`text-sm px-2 py-1 rounded-full ${
                      rsvp.status === 'yes'
                        ? 'bg-success/10 text-success'
                        : rsvp.status === 'maybe'
                          ? 'bg-warning/10 text-warning'
                          : 'bg-error/10 text-error'
                    }`}
                  >
                    {rsvp.status}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Health Summary - Only visible to event managers */}
        <HealthSummarySection
          eventId={event.id}
          canManage={event.can_manage}
          bigMode={bigMode}
        />
      </div>

      {/* Cancel Event Modal */}
      <CancelEventModal
        isOpen={showCancelModal}
        onClose={() => setShowCancelModal(false)}
        onConfirm={handleCancelEvent}
        loading={cancelLoading}
      />
    </div>
  )
}
