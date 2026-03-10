import { useState } from 'react'
import { Bell, ChevronDown, ChevronRight, Settings2 } from 'lucide-react'

interface EventTogglesProps {
  settings: Record<string, string>
  onToggle: (key: string, value: boolean) => void
  onTextChange: (key: string, value: string) => void
  saving: boolean
  hasEnabledService: boolean
}

interface EventItem {
  key: string
  label: string
  description: string
  daysKey?: string
}

interface EventGroup {
  id: string
  label: string
  events: EventItem[]
}

const eventGroups: EventGroup[] = [
  {
    id: 'events',
    label: 'Events',
    events: [
      { key: 'notify_event_created', label: 'Event Created', description: 'New event added to the family' },
      { key: 'notify_event_updated', label: 'Event Updated', description: 'Changes to event details' },
      { key: 'notify_event_cancelled', label: 'Event Cancelled', description: 'Event was cancelled' },
      {
        key: 'notify_event_reminder',
        label: 'Event Reminder',
        description: 'Reminder before upcoming events',
        daysKey: 'event_reminder_days',
      },
      { key: 'notify_rsvp_received', label: 'RSVP Received', description: 'Someone RSVPs to an event' },
    ],
  },
  {
    id: 'engagement',
    label: 'Polls & Comments',
    events: [
      { key: 'notify_poll_created', label: 'Poll Created', description: 'New poll posted' },
      { key: 'notify_poll_closing_soon', label: 'Poll Closing Soon', description: 'Poll is about to close' },
      { key: 'notify_comment_added', label: 'Comment Added', description: 'New comment on an event' },
      { key: 'notify_comment_mention', label: '@Mention', description: 'You were mentioned in a comment' },
    ],
  },
  {
    id: 'family',
    label: 'Family',
    events: [
      {
        key: 'notify_family_member_joined',
        label: 'Member Joined',
        description: 'New member joined the family',
      },
    ],
  },
]

export function EventToggles({
  settings,
  onToggle,
  onTextChange,
  saving,
  hasEnabledService,
}: EventTogglesProps) {
  const [expandedGroups, setExpandedGroups] = useState<Set<string>>(new Set(['events', 'engagement']))
  const [showAdvanced, setShowAdvanced] = useState(false)

  const toggleGroup = (groupId: string) => {
    setExpandedGroups((prev) => {
      const next = new Set(prev)
      if (next.has(groupId)) {
        next.delete(groupId)
      } else {
        next.add(groupId)
      }
      return next
    })
  }

  const getEnabledCount = (events: EventItem[]): number =>
    events.filter((e) => settings[e.key] === 'true').length

  if (!hasEnabledService) {
    return (
      <div className="bg-fc-surface border border-fc-border rounded-2xl p-6">
        <div className="flex items-center gap-3 mb-4">
          <Bell className="w-6 h-6 text-fc-text-muted" />
          <h2 className="text-lg font-semibold text-fc-text">Event Notifications</h2>
        </div>
        <p className="text-sm text-fc-text-muted">
          Enable at least one notification service above to configure event notifications.
        </p>
      </div>
    )
  }

  return (
    <div className="bg-fc-surface border border-fc-border rounded-2xl p-6">
      <div className="flex items-center gap-3 mb-4">
        <Bell className="w-6 h-6 text-primary" />
        <div>
          <h2 className="text-lg font-semibold text-fc-text">Event Notifications</h2>
          <p className="text-sm text-fc-text-muted">Choose which events trigger notifications</p>
        </div>
      </div>

      <div className="space-y-2">
        {eventGroups.map((group) => {
          const isExpanded = expandedGroups.has(group.id)
          const enabledCount = getEnabledCount(group.events)

          return (
            <div key={group.id} className="border border-fc-border rounded-lg overflow-hidden">
              <button
                onClick={() => toggleGroup(group.id)}
                className="flex items-center gap-3 w-full p-3 bg-fc-bg/50 hover:bg-fc-bg text-left transition-colors"
              >
                {isExpanded ? (
                  <ChevronDown className="w-4 h-4 text-fc-text-muted" />
                ) : (
                  <ChevronRight className="w-4 h-4 text-fc-text-muted" />
                )}
                <div className="flex-1">
                  <span className="text-sm font-medium text-fc-text">{group.label}</span>
                  {!isExpanded && (
                    <span className="ml-2 text-xs text-fc-text-muted">
                      ({enabledCount}/{group.events.length} enabled)
                    </span>
                  )}
                </div>
              </button>

              {isExpanded && (
                <div className="p-3 space-y-3 bg-fc-surface">
                  {group.events.map((event) => (
                    <div key={event.key} className="flex items-start justify-between gap-4">
                      <div className="flex-1 min-w-0">
                        <label className="flex items-center cursor-pointer">
                          <input
                            type="checkbox"
                            checked={settings[event.key] === 'true'}
                            onChange={(e) => onToggle(event.key, e.target.checked)}
                            disabled={saving}
                            className="w-4 h-4 text-primary bg-fc-bg border-fc-border rounded focus:ring-primary focus:ring-2 disabled:opacity-50"
                          />
                          <span className="ml-2 text-sm text-fc-text font-medium">{event.label}</span>
                        </label>
                        <p className="mt-1 ml-6 text-xs text-fc-text-muted">{event.description}</p>
                      </div>
                      {event.daysKey && (
                        <div className="flex items-center gap-2">
                          <input
                            type="number"
                            value={settings[event.daysKey] ?? '3'}
                            onChange={(e) => onTextChange(event.daysKey!, e.target.value)}
                            disabled={saving || settings[event.key] !== 'true'}
                            min="1"
                            max="30"
                            className="w-16 px-2 py-1 text-sm bg-fc-bg border border-fc-border rounded text-fc-text disabled:opacity-50"
                          />
                          <span className="text-xs text-fc-text-muted whitespace-nowrap">days before</span>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )
        })}

        {/* Advanced Settings */}
        <div className="mt-4 border border-fc-border rounded-lg overflow-hidden">
          <button
            onClick={() => setShowAdvanced(!showAdvanced)}
            className="flex items-center gap-3 w-full p-3 bg-fc-bg/50 hover:bg-fc-bg text-left transition-colors"
          >
            {showAdvanced ? (
              <ChevronDown className="w-4 h-4 text-fc-text-muted" />
            ) : (
              <ChevronRight className="w-4 h-4 text-fc-text-muted" />
            )}
            <Settings2 className="w-4 h-4 text-fc-text-muted" />
            <div className="flex-1">
              <span className="text-sm font-medium text-fc-text">Advanced</span>
              <p className="text-xs text-fc-text-muted">Retry settings for high-priority notifications</p>
            </div>
          </button>

          {showAdvanced && (
            <div className="p-3 space-y-3 bg-fc-surface">
              <div className="flex items-center justify-between gap-4">
                <div className="flex-1 min-w-0">
                  <label className="text-sm text-fc-text">Retry Attempts</label>
                  <p className="text-xs text-fc-text-muted">Max retries for urgent/high priority events</p>
                </div>
                <input
                  type="number"
                  min="1"
                  max="10"
                  value={settings.notification_retry_attempts ?? '3'}
                  onChange={(e) => onTextChange('notification_retry_attempts', e.target.value)}
                  disabled={saving}
                  className="w-20 px-2 py-1 text-sm bg-fc-bg border border-fc-border rounded text-fc-text disabled:opacity-50"
                />
              </div>
              <div className="flex items-center justify-between gap-4">
                <div className="flex-1 min-w-0">
                  <label className="text-sm text-fc-text">Retry Delay (seconds)</label>
                  <p className="text-xs text-fc-text-muted">Base delay between retry attempts</p>
                </div>
                <input
                  type="number"
                  min="0.5"
                  max="30"
                  step="0.5"
                  value={settings.notification_retry_delay ?? '2.0'}
                  onChange={(e) => onTextChange('notification_retry_delay', e.target.value)}
                  disabled={saving}
                  className="w-20 px-2 py-1 text-sm bg-fc-bg border border-fc-border rounded text-fc-text disabled:opacity-50"
                />
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
