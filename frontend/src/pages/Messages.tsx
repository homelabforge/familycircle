import { useEffect, useState } from 'react'
import { MessageCircle, Send, Loader2, ChevronDown, ChevronUp } from 'lucide-react'
import { toast } from 'sonner'
import BackButton from '@/components/BackButton'
import { useBigMode } from '@/contexts/BigModeContext'
import {
  eventsApi,
  giftExchangeApi,
  type Event,
  type GiftExchangeMessage,
} from '@/lib/api'

interface EventMessages {
  event: Event
  messages: GiftExchangeMessage[]
  hasAssignment: boolean
}

export default function Messages() {
  const { bigMode } = useBigMode()
  const [loading, setLoading] = useState(true)
  const [eventMessages, setEventMessages] = useState<EventMessages[]>([])
  const [expandedEvent, setExpandedEvent] = useState<string | null>(null)
  const [newMessages, setNewMessages] = useState<Record<string, string>>({})
  const [sending, setSending] = useState<string | null>(null)

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      setLoading(true)
      const eventsRes = await eventsApi.list()

      // Filter to events with Gift Exchange
      const ssEvents = eventsRes.events.filter((e) => e.has_gift_exchange)

      // Load messages for each event
      const messagesPromises = ssEvents.map(async (event) => {
        try {
          const [statusRes, messagesRes] = await Promise.all([
            giftExchangeApi.getStatus(event.id),
            giftExchangeApi.getMessages(event.id),
          ])
          return {
            event,
            messages: messagesRes.messages,
            hasAssignment: statusRes.has_assignment,
          }
        } catch {
          return {
            event,
            messages: [],
            hasAssignment: false,
          }
        }
      })

      const results = await Promise.all(messagesPromises)
      setEventMessages(results)

      // Auto-expand first event with messages
      const firstWithMessages = results.find((r) => r.messages.length > 0 || r.hasAssignment)
      if (firstWithMessages) {
        setExpandedEvent(firstWithMessages.event.id)
      }
    } catch (err) {
      toast.error('Failed to load messages')
    } finally {
      setLoading(false)
    }
  }

  const handleSendMessage = async (eventId: string) => {
    const content = newMessages[eventId]?.trim()
    if (!content) return

    try {
      setSending(eventId)
      await giftExchangeApi.sendMessage(eventId, content)
      toast.success('Message sent!')
      setNewMessages((prev) => ({ ...prev, [eventId]: '' }))
      await loadData()
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to send message')
    } finally {
      setSending(null)
    }
  }

  const formatDate = (dateStr?: string) => {
    if (!dateStr) return ''
    const date = new Date(dateStr)
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: 'numeric',
      minute: '2-digit',
    })
  }

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-6">
        <BackButton />
        <div className="flex justify-center py-12">
          <Loader2 className="w-8 h-8 animate-spin text-primary" />
        </div>
      </div>
    )
  }

  if (eventMessages.length === 0) {
    return (
      <div className="container mx-auto px-4 py-6">
        <BackButton />
        <div className="mt-4 text-center py-12">
          <MessageCircle className="w-12 h-12 mx-auto mb-4 text-fc-text-muted opacity-50" />
          <p className={`text-fc-text-muted ${bigMode ? 'text-lg' : ''}`}>
            No Gift Exchange events available.
          </p>
          <p className={`text-fc-text-muted mt-2 ${bigMode ? 'text-base' : 'text-sm'}`}>
            Messages will appear here once you're part of a Gift Exchange event.
          </p>
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
          <MessageCircle className={bigMode ? 'w-9 h-9' : 'w-7 h-7'} />
          Gift Exchange Messages
        </h1>

        <p className={`text-fc-text-muted mb-6 ${bigMode ? 'text-lg' : ''}`}>
          Send anonymous messages to your Gift Exchange match. Your identity stays hidden!
        </p>

        {/* Event Accordion */}
        <div className="space-y-4">
          {eventMessages.map(({ event, messages, hasAssignment }) => (
            <div
              key={event.id}
              className="bg-fc-surface border border-fc-border rounded-2xl overflow-hidden"
            >
              {/* Event Header */}
              <button
                onClick={() => setExpandedEvent(expandedEvent === event.id ? null : event.id)}
                className={`
                  w-full flex items-center justify-between
                  ${bigMode ? 'p-5' : 'p-4'}
                  hover:bg-fc-bg transition-colors
                `}
              >
                <div className="flex items-center gap-3">
                  <span className={`font-medium text-fc-text ${bigMode ? 'text-lg' : ''}`}>
                    {event.title}
                  </span>
                  {messages.length > 0 && (
                    <span className="bg-primary text-white text-xs px-2 py-1 rounded-full">
                      {messages.length}
                    </span>
                  )}
                </div>
                {expandedEvent === event.id ? (
                  <ChevronUp className="w-5 h-5 text-fc-text-muted" />
                ) : (
                  <ChevronDown className="w-5 h-5 text-fc-text-muted" />
                )}
              </button>

              {/* Expanded Content */}
              {expandedEvent === event.id && (
                <div className={`border-t border-fc-border ${bigMode ? 'p-5' : 'p-4'}`}>
                  {!hasAssignment ? (
                    <div className="text-center py-8 text-fc-text-muted">
                      <MessageCircle className="w-10 h-10 mx-auto mb-3 opacity-50" />
                      <p className={bigMode ? 'text-base' : 'text-sm'}>
                        Assignments haven't been made yet for this event.
                      </p>
                    </div>
                  ) : (
                    <>
                      {/* Messages List */}
                      <div className="min-h-[200px] max-h-[400px] overflow-y-auto mb-4">
                        {messages.length === 0 ? (
                          <div className="flex flex-col items-center justify-center h-48 text-fc-text-muted">
                            <MessageCircle className="w-10 h-10 mb-3 opacity-50" />
                            <p>No messages yet. Start the conversation!</p>
                          </div>
                        ) : (
                          <div className="space-y-4">
                            {messages.map((msg) => (
                              <div key={msg.id} className="flex justify-end">
                                <div
                                  className={`
                                    max-w-[80%] rounded-2xl bg-primary text-white rounded-br-none
                                    ${bigMode ? 'px-5 py-4' : 'px-4 py-3'}
                                  `}
                                >
                                  <p className={bigMode ? 'text-lg' : ''}>{msg.content}</p>
                                  <p
                                    className={`
                                      mt-2 opacity-70
                                      ${bigMode ? 'text-sm' : 'text-xs'}
                                    `}
                                  >
                                    {formatDate(msg.created_at)}
                                  </p>
                                </div>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>

                      {/* Message Input */}
                      <div className="flex gap-3">
                        <input
                          type="text"
                          value={newMessages[event.id] || ''}
                          onChange={(e) =>
                            setNewMessages((prev) => ({
                              ...prev,
                              [event.id]: e.target.value,
                            }))
                          }
                          onKeyDown={(e) => {
                            if (e.key === 'Enter' && !e.shiftKey) {
                              e.preventDefault()
                              handleSendMessage(event.id)
                            }
                          }}
                          placeholder="Type your message..."
                          className={`
                            flex-1 bg-fc-bg border border-fc-border rounded-xl
                            text-fc-text placeholder:text-fc-text-muted
                            focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent
                            ${bigMode ? 'px-5 py-4 text-lg' : 'px-4 py-3'}
                          `}
                        />
                        <button
                          onClick={() => handleSendMessage(event.id)}
                          disabled={sending === event.id || !newMessages[event.id]?.trim()}
                          className={`
                            flex items-center justify-center
                            bg-primary text-white rounded-xl
                            hover:bg-primary-hover transition-colors
                            disabled:opacity-50
                            ${bigMode ? 'px-6' : 'px-4'}
                          `}
                        >
                          {sending === event.id ? (
                            <Loader2 className={`${bigMode ? 'w-6 h-6' : 'w-5 h-5'} animate-spin`} />
                          ) : (
                            <Send className={bigMode ? 'w-6 h-6' : 'w-5 h-5'} />
                          )}
                        </button>
                      </div>
                    </>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
