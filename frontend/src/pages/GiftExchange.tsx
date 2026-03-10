import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { TreePine, MessageCircle, Loader2, ExternalLink } from 'lucide-react'
import BackButton from '@/components/BackButton'
import { useBigMode } from '@/contexts/BigModeContext'
import {
  giftExchangeApi,
  wishlistApi,
  eventsApi,
  type GiftExchangeStatus,
  type GiftExchangeAssignment,
  type WishlistItem,
  type Event,
} from '@/lib/api'

export default function GiftExchange() {
  const { eventId: urlEventId } = useParams()
  const { bigMode } = useBigMode()
  const [status, setStatus] = useState<GiftExchangeStatus | null>(null)
  const [assignment, setAssignment] = useState<GiftExchangeAssignment | null>(null)
  const [myWishlist, setMyWishlist] = useState<WishlistItem[]>([])
  const [events, setEvents] = useState<Event[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showMessageModal, setShowMessageModal] = useState(false)
  const [activeEventId, setActiveEventId] = useState<string | null>(null)

  // Use URL eventId if available, otherwise use the auto-loaded activeEventId
  const eventId = urlEventId || activeEventId

  useEffect(() => {
    if (urlEventId) {
      setActiveEventId(urlEventId)
      loadGiftExchange(urlEventId)
    } else {
      loadEventsWithGiftExchange()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [urlEventId])

  const loadEventsWithGiftExchange = async () => {
    try {
      setLoading(true)
      setError(null)
      const response = await eventsApi.list()
      const ssEvents = response.events.filter((e) => e.has_secret_santa)
      setEvents(ssEvents)

      // If only one event, load it and set activeEventId
      if (ssEvents.length === 1) {
        setActiveEventId(ssEvents[0].id)
        await loadGiftExchange(ssEvents[0].id)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load events')
    } finally {
      setLoading(false)
    }
  }

  const loadGiftExchange = async (id: string) => {
    try {
      setLoading(true)
      setError(null)

      // Load status and my wishlist in parallel
      const [statusRes, wishlistRes] = await Promise.all([
        giftExchangeApi.getStatus(id),
        wishlistApi.get(),
      ])

      setStatus(statusRes)
      setMyWishlist(wishlistRes.items)

      // If assigned, load assignment
      if (statusRes.status === 'assigned') {
        try {
          const assignmentRes = await giftExchangeApi.getAssignment(id)
          setAssignment(assignmentRes)
        } catch {
          // No assignment for this user
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load Gift Exchange')
    } finally {
      setLoading(false)
    }
  }

  const getInitials = (name: string) => {
    return name
      .split(' ')
      .map((n) => n[0])
      .join('')
      .toUpperCase()
      .slice(0, 2)
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

  // Show event selection if multiple events
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
            <TreePine className={bigMode ? 'w-9 h-9' : 'w-7 h-7'} />
            Gift Exchange
          </h1>

          <p className={`text-fc-text-muted mb-6 ${bigMode ? 'text-lg' : ''}`}>
            Choose an event:
          </p>

          <div className="space-y-3">
            {events.map((event) => (
              <Link
                key={event.id}
                to={`/gift-exchange/${event.id}`}
                className={`
                  block bg-fc-surface border border-fc-border rounded-xl
                  hover:bg-fc-surface-hover transition-colors
                  ${bigMode ? 'p-5' : 'p-4'}
                `}
              >
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className={`font-medium text-fc-text ${bigMode ? 'text-lg' : ''}`}>
                      {event.title}
                    </h3>
                    <p className={`text-fc-text-muted ${bigMode ? 'text-base' : 'text-sm'}`}>
                      {new Date(event.event_date).toLocaleDateString()}
                    </p>
                  </div>
                  {event.secret_santa_assigned ? (
                    <span className="text-xs bg-success/10 text-success px-2 py-1 rounded-full">
                      Assigned
                    </span>
                  ) : (
                    <span className="text-xs bg-warning/10 text-warning px-2 py-1 rounded-full">
                      Not yet assigned
                    </span>
                  )}
                </div>
              </Link>
            ))}
          </div>
        </div>
      </div>
    )
  }

  // No gift exchange events
  if (!eventId && events.length === 0 && !status) {
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
            <TreePine className={bigMode ? 'w-9 h-9' : 'w-7 h-7'} />
            Gift Exchange
          </h1>

          <div className="text-center py-12">
            <TreePine className="w-16 h-16 text-fc-text-muted mx-auto mb-4" />
            <p className={`text-fc-text-muted ${bigMode ? 'text-lg' : ''}`}>
              No Gift Exchange events yet.
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
          <TreePine className={bigMode ? 'w-9 h-9' : 'w-7 h-7'} />
          Gift Exchange
        </h1>

        {error && (
          <div className="bg-error/10 text-error px-4 py-3 rounded-xl mb-6">
            {error}
          </div>
        )}

        {/* Status Banner */}
        {status && status.status === 'not_assigned' && (
          <div className="bg-warning/10 border border-warning/30 text-warning-dark rounded-2xl p-6 mb-6">
            <h2 className={`font-semibold mb-2 ${bigMode ? 'text-xl' : 'text-lg'}`}>
              Waiting for Assignment
            </h2>
            <p className={bigMode ? 'text-base' : 'text-sm'}>
              Names haven't been drawn yet. Check back later or ask an organizer to run the
              assignment.
            </p>
            <p className={`mt-2 ${bigMode ? 'text-base' : 'text-sm'}`}>
              {status.participant_count} participant{status.participant_count !== 1 ? 's' : ''}{' '}
              registered
            </p>
          </div>
        )}

        {/* Assignment Card */}
        {status?.status === 'assigned' && assignment?.giftee_name && (
          <div className="bg-fc-surface border border-fc-border rounded-2xl p-6 mb-6">
            <h2
              className={`
                font-semibold text-fc-text mb-4
                ${bigMode ? 'text-xl' : 'text-lg'}
              `}
            >
              Your Assignment
            </h2>
            <p className={`text-fc-text-muted mb-4 ${bigMode ? 'text-lg' : ''}`}>
              You're buying a gift for:
            </p>
            <div
              className={`
                flex items-center gap-4 bg-fc-bg rounded-xl p-4
                ${bigMode ? 'text-xl' : 'text-lg'}
              `}
            >
              <div className="w-12 h-12 bg-primary/10 rounded-full flex items-center justify-center">
                <span className="text-primary font-bold">{getInitials(assignment.giftee_name)}</span>
              </div>
              <span className="font-medium text-fc-text">{assignment.giftee_name}</span>
            </div>

            {/* Giftee's Wishlist */}
            {assignment.wishlist && assignment.wishlist.length > 0 && (
              <div className="mt-6 pt-4 border-t border-fc-border">
                <h3 className={`font-medium text-fc-text mb-3 ${bigMode ? 'text-lg' : ''}`}>
                  Their Wishlist:
                </h3>
                <ul className={`space-y-3 ${bigMode ? 'text-base' : 'text-sm'}`}>
                  {assignment.wishlist.map((item) => (
                    <li key={item.id} className="flex items-start gap-3 text-fc-text">
                      <span className="text-primary mt-1">•</span>
                      <div className="flex-1">
                        <span className="font-medium">{item.name}</span>
                        {item.description && (
                          <p className="text-fc-text-muted text-sm">{item.description}</p>
                        )}
                        {item.url && (
                          <a
                            href={item.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center gap-1 text-primary hover:text-primary-hover text-sm mt-1"
                          >
                            <ExternalLink className="w-3 h-3" />
                            View Link
                          </a>
                        )}
                      </div>
                      {item.price_range && (
                        <span className="text-fc-text-muted text-sm">{item.price_range}</span>
                      )}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            <div className={`flex gap-4 mt-6 ${bigMode ? 'flex-col sm:flex-row' : ''}`}>
              <button
                onClick={() => setShowMessageModal(true)}
                className={`
                  flex items-center justify-center gap-2
                  bg-fc-surface-hover text-fc-text rounded-xl
                  hover:bg-fc-border transition-colors
                  ${bigMode ? 'px-6 py-4 text-lg' : 'px-4 py-3'}
                `}
              >
                <MessageCircle className={bigMode ? 'w-6 h-6' : 'w-5 h-5'} />
                Send Anonymous Message
              </button>
            </div>
          </div>
        )}

        {/* My Wishlist */}
        <div className="bg-fc-surface border border-fc-border rounded-2xl p-6">
          <h2
            className={`
              font-semibold text-fc-text mb-4
              ${bigMode ? 'text-xl' : 'text-lg'}
            `}
          >
            Your Wishlist
          </h2>
          {myWishlist.length > 0 ? (
            <ul className={`space-y-3 ${bigMode ? 'text-lg' : ''}`}>
              {myWishlist.slice(0, 5).map((item) => (
                <li key={item.id} className="flex items-center gap-3 text-fc-text">
                  <span className="text-primary">•</span>
                  {item.name}
                </li>
              ))}
              {myWishlist.length > 5 && (
                <li className="text-fc-text-muted">...and {myWishlist.length - 5} more</li>
              )}
            </ul>
          ) : (
            <p className={`text-fc-text-muted ${bigMode ? 'text-base' : 'text-sm'}`}>
              Your wishlist is empty. Add some items to help your Gift Exchange match!
            </p>
          )}
          <Link
            to="/wishlist"
            className={`
              inline-block mt-4 text-primary hover:text-primary-hover transition-colors
              ${bigMode ? 'text-lg py-2' : ''}
            `}
          >
            {myWishlist.length > 0 ? 'Edit Wishlist' : '+ Add Items'}
          </Link>
        </div>
      </div>

      {/* Message Modal */}
      {showMessageModal && eventId && (
        <SendMessageModal
          eventId={eventId}
          onClose={() => setShowMessageModal(false)}
          bigMode={bigMode}
        />
      )}
    </div>
  )
}

interface SendMessageModalProps {
  eventId: string
  onClose: () => void
  bigMode: boolean
}

function SendMessageModal({ eventId, onClose, bigMode }: SendMessageModalProps) {
  const [message, setMessage] = useState('')
  const [sending, setSending] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)

  const handleSend = async () => {
    if (!message.trim()) return

    try {
      setSending(true)
      setError(null)
      await giftExchangeApi.sendMessage(eventId, message.trim())
      setSuccess(true)
      setTimeout(onClose, 1500)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to send message')
    } finally {
      setSending(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
      <div
        className={`
          bg-fc-surface rounded-2xl w-full max-w-md
          ${bigMode ? 'p-6' : 'p-5'}
        `}
      >
        <h2
          className={`
            font-semibold text-fc-text mb-4
            ${bigMode ? 'text-xl' : 'text-lg'}
          `}
        >
          Send Anonymous Message
        </h2>

        {success ? (
          <div className="text-center py-6">
            <div className="text-success text-lg font-medium">Message sent!</div>
          </div>
        ) : (
          <>
            <p className={`text-fc-text-muted mb-4 ${bigMode ? 'text-base' : 'text-sm'}`}>
              Your giftee will receive this message without knowing who sent it.
            </p>

            {error && (
              <div className="bg-error/10 text-error px-4 py-3 rounded-xl mb-4 text-sm">
                {error}
              </div>
            )}

            <textarea
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              placeholder="Write your message..."
              rows={4}
              className={`
                w-full bg-fc-bg border border-fc-border rounded-xl text-fc-text
                placeholder:text-fc-text-muted focus:outline-none focus:ring-2 focus:ring-primary resize-none
                ${bigMode ? 'px-4 py-3 text-lg' : 'px-3 py-2'}
              `}
            />

            <div className="flex gap-3 mt-4">
              <button
                onClick={onClose}
                className={`
                  flex-1 border border-fc-border text-fc-text rounded-xl
                  hover:bg-fc-surface-hover transition-colors
                  ${bigMode ? 'px-4 py-3 text-lg' : 'px-3 py-2'}
                `}
              >
                Cancel
              </button>
              <button
                onClick={handleSend}
                disabled={sending || !message.trim()}
                className={`
                  flex-1 bg-primary text-white rounded-xl
                  hover:bg-primary-hover transition-colors
                  disabled:opacity-50 disabled:cursor-not-allowed
                  ${bigMode ? 'px-4 py-3 text-lg' : 'px-3 py-2'}
                `}
              >
                {sending ? 'Sending...' : 'Send'}
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  )
}
