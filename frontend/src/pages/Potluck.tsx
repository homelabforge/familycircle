import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { UtensilsCrossed, Plus, Check, Loader2, X } from 'lucide-react'
import BackButton from '@/components/BackButton'
import { useBigMode } from '@/contexts/BigModeContext'
import { useAuth } from '@/contexts/AuthContext'
import { potluckApi, eventsApi, type PotluckItem, type Event } from '@/lib/api'

export default function Potluck() {
  const { eventId } = useParams()
  const { bigMode } = useBigMode()
  const { user } = useAuth()
  const [items, setItems] = useState<PotluckItem[]>([])
  const [eventTitle, setEventTitle] = useState('')
  const [events, setEvents] = useState<Event[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [claimingId, setClaimingId] = useState<string | null>(null)

  useEffect(() => {
    if (eventId) {
      loadPotluck(eventId)
    } else {
      loadEventsWithPotluck()
    }
  }, [eventId])

  const loadEventsWithPotluck = async () => {
    try {
      setLoading(true)
      setError(null)
      const response = await eventsApi.list()
      const potluckEvents = response.events.filter((e) => e.has_potluck)
      setEvents(potluckEvents)

      // If there's only one potluck event, load it automatically
      if (potluckEvents.length === 1) {
        await loadPotluck(potluckEvents[0].id)
        setEventTitle(potluckEvents[0].title)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load events')
    } finally {
      setLoading(false)
    }
  }

  const loadPotluck = async (id: string) => {
    try {
      setLoading(true)
      setError(null)
      const response = await potluckApi.get(id)
      setItems(response.items)
      setEventTitle(response.event_title)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load potluck')
    } finally {
      setLoading(false)
    }
  }

  const handleClaim = async (itemId: string) => {
    if (!eventId && events.length !== 1) return
    const eid = eventId || events[0]?.id
    if (!eid) return

    try {
      setClaimingId(itemId)
      await potluckApi.claim(eid, itemId)
      await loadPotluck(eid)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to claim item')
    } finally {
      setClaimingId(null)
    }
  }

  const handleUnclaim = async (itemId: string) => {
    if (!eventId && events.length !== 1) return
    const eid = eventId || events[0]?.id
    if (!eid) return

    try {
      setClaimingId(itemId)
      await potluckApi.unclaim(eid, itemId)
      await loadPotluck(eid)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to unclaim item')
    } finally {
      setClaimingId(null)
    }
  }

  const unclaimedItems = items.filter((i) => !i.claimed_by_id)
  const claimedItems = items.filter((i) => i.claimed_by_id)
  const myItems = items.filter((i) => i.claimed_by_id === user?.id)

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

  // Show event selection if no eventId and multiple potluck events
  if (!eventId && events.length > 1) {
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
            <UtensilsCrossed className={bigMode ? 'w-9 h-9' : 'w-7 h-7'} />
            Potluck
          </h1>

          <p className={`text-fc-text-muted mb-6 ${bigMode ? 'text-lg' : ''}`}>
            Choose an event:
          </p>

          <div className="space-y-3">
            {events.map((event) => (
              <Link
                key={event.id}
                to={`/potluck/${event.id}`}
                className={`
                  block bg-fc-surface border border-fc-border rounded-xl
                  hover:bg-fc-surface-hover transition-colors
                  ${bigMode ? 'p-5' : 'p-4'}
                `}
              >
                <h3 className={`font-medium text-fc-text ${bigMode ? 'text-lg' : ''}`}>
                  {event.title}
                </h3>
                <p className={`text-fc-text-muted ${bigMode ? 'text-base' : 'text-sm'}`}>
                  {new Date(event.event_date).toLocaleDateString()}
                </p>
              </Link>
            ))}
          </div>
        </div>
      </div>
    )
  }

  // No potluck events
  if (!eventId && events.length === 0 && !eventTitle) {
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
            <UtensilsCrossed className={bigMode ? 'w-9 h-9' : 'w-7 h-7'} />
            Potluck
          </h1>

          <div className="text-center py-12">
            <UtensilsCrossed className="w-16 h-16 text-fc-text-muted mx-auto mb-4" />
            <p className={`text-fc-text-muted ${bigMode ? 'text-lg' : ''}`}>
              No potluck events yet.
            </p>
          </div>
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
          <UtensilsCrossed className={bigMode ? 'w-9 h-9' : 'w-7 h-7'} />
          Potluck - {eventTitle}
        </h1>

        {error && (
          <div className="bg-error/10 text-error px-4 py-3 rounded-xl mb-6">
            {error}
          </div>
        )}

        {/* My Items */}
        {myItems.length > 0 && (
          <div className="mb-6 bg-primary/5 border border-primary/20 rounded-2xl p-4">
            <h2
              className={`
                font-semibold text-primary mb-3
                ${bigMode ? 'text-lg' : 'text-base'}
              `}
            >
              You're bringing:
            </h2>
            <div className="space-y-2">
              {myItems.map((item) => (
                <div
                  key={item.id}
                  className={`flex items-center justify-between ${bigMode ? 'text-lg' : ''}`}
                >
                  <span className="text-fc-text">{item.name}</span>
                  <button
                    onClick={() => handleUnclaim(item.id)}
                    disabled={claimingId === item.id}
                    className="text-fc-text-muted hover:text-error transition-colors p-1"
                    title="Cancel"
                  >
                    <X className="w-5 h-5" />
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Items Needed */}
        {unclaimedItems.length > 0 && (
          <div className="mb-6">
            <h2
              className={`
                font-semibold text-fc-text mb-4
                ${bigMode ? 'text-xl' : 'text-lg'}
              `}
            >
              Items Still Needed ({unclaimedItems.length})
            </h2>
            <div className="space-y-3">
              {unclaimedItems.map((item) => (
                <div
                  key={item.id}
                  className={`
                    flex items-center justify-between
                    bg-fc-surface border border-fc-border rounded-xl
                    ${bigMode ? 'p-5' : 'p-4'}
                  `}
                >
                  <div>
                    <span className={`font-medium text-fc-text ${bigMode ? 'text-lg' : ''}`}>
                      {item.name}
                    </span>
                    {item.category && (
                      <span className="ml-2 text-sm text-fc-text-muted">({item.category})</span>
                    )}
                    {item.description && (
                      <p className={`text-fc-text-muted ${bigMode ? 'text-base' : 'text-sm'}`}>
                        {item.description}
                      </p>
                    )}
                    {item.serves && (
                      <p className={`text-fc-text-muted ${bigMode ? 'text-sm' : 'text-xs'}`}>
                        Serves {item.serves}
                      </p>
                    )}
                    {item.dietary_info && (
                      <p className={`text-primary ${bigMode ? 'text-sm' : 'text-xs'}`}>
                        {item.dietary_info}
                      </p>
                    )}
                    {item.allergens && (
                      <p className={`text-warning ${bigMode ? 'text-sm' : 'text-xs'}`}>
                        Contains: {item.allergens}
                      </p>
                    )}
                  </div>
                  <button
                    onClick={() => handleClaim(item.id)}
                    disabled={claimingId === item.id}
                    className={`
                      flex items-center gap-2
                      bg-primary text-white rounded-lg
                      hover:bg-primary-hover transition-colors
                      disabled:opacity-50 disabled:cursor-not-allowed
                      ${bigMode ? 'px-5 py-3 text-lg' : 'px-4 py-2'}
                    `}
                  >
                    {claimingId === item.id ? (
                      <Loader2 className={`${bigMode ? 'w-5 h-5' : 'w-4 h-4'} animate-spin`} />
                    ) : (
                      <Plus className={bigMode ? 'w-5 h-5' : 'w-4 h-4'} />
                    )}
                    I'll Bring This
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Claimed Items */}
        {claimedItems.length > 0 && (
          <div>
            <h2
              className={`
                font-semibold text-fc-text mb-4
                ${bigMode ? 'text-xl' : 'text-lg'}
              `}
            >
              Already Claimed ({claimedItems.length})
            </h2>
            <div className="space-y-3">
              {claimedItems.map((item) => (
                <div
                  key={item.id}
                  className={`
                    flex items-center justify-between
                    bg-fc-surface border border-fc-border rounded-xl
                    ${bigMode ? 'p-5' : 'p-4'}
                  `}
                >
                  <div className="flex items-center gap-3">
                    <Check className="w-5 h-5 text-success" />
                    <div>
                      <span className={`font-medium text-fc-text ${bigMode ? 'text-lg' : ''}`}>
                        {item.name}
                      </span>
                      {item.category && (
                        <span className="ml-2 text-sm text-fc-text-muted">({item.category})</span>
                      )}
                    </div>
                  </div>
                  <span className={`text-fc-text-muted ${bigMode ? 'text-base' : 'text-sm'}`}>
                    {item.claimed_by_name}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {items.length === 0 && !error && (
          <div className="text-center py-12">
            <UtensilsCrossed className="w-16 h-16 text-fc-text-muted mx-auto mb-4" />
            <p className={`text-fc-text-muted ${bigMode ? 'text-lg' : ''}`}>
              No items added to the potluck yet.
            </p>
          </div>
        )}
      </div>
    </div>
  )
}
