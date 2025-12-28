import { useEffect, useState } from 'react'
import {
  Calendar,
  Gift,
  Users,
  MessageCircle,
  Wrench,
  User,
  Plus,
} from 'lucide-react'
import DashboardCard from '@/components/DashboardCard'
import CreateEventModal from '@/components/CreateEventModal'
import UpcomingEvents from '@/components/UpcomingEvents'
import { useAuth } from '@/contexts/AuthContext'
import { useBigMode } from '@/contexts/BigModeContext'
import { eventsApi, familyApi } from '@/lib/api'

interface UpcomingEvent {
  id: string
  title: string
  date: string
  time: string
  rsvpStatus: 'yes' | 'no' | 'maybe' | null
}

export default function Dashboard() {
  const { user, isOrganizer } = useAuth()
  const { bigMode } = useBigMode()
  const [upcomingEvents, setUpcomingEvents] = useState<UpcomingEvent[]>([])
  const [eventCount, setEventCount] = useState(0)
  const [memberCount, setMemberCount] = useState(0)
  const [showCreateEventModal, setShowCreateEventModal] = useState(false)

  const loadDashboardData = async () => {
    try {
      // Load events and members in parallel
      const [eventsRes, membersRes] = await Promise.all([
        eventsApi.listUpcoming(5),
        familyApi.listMembers(),
      ])

      // Format upcoming events for the component
      const formatted = eventsRes.events.map((e) => ({
        id: e.id,
        title: e.title,
        date: new Date(e.event_date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
        time: new Date(e.event_date).toLocaleTimeString('en-US', {
          hour: 'numeric',
          minute: '2-digit',
        }),
        rsvpStatus: e.user_rsvp as 'yes' | 'no' | 'maybe' | null,
        isCancelled: e.is_cancelled,
      }))

      setUpcomingEvents(formatted)
      setEventCount(eventsRes.events.length)
      setMemberCount(membersRes.members.length)
    } catch {
      // Silently fail - dashboard will show empty state
    }
  }

  useEffect(() => {
    loadDashboardData()
  }, [])

  const cards = [
    {
      onClick: () => setShowCreateEventModal(true),
      icon: Plus,
      title: 'Create Event',
      badge: undefined,
      badgeColor: 'primary' as const,
    },
    {
      to: '/wishlist',
      icon: Gift,
      title: 'Wishlist',
      badge: undefined,
      badgeColor: 'primary' as const,
    },
    {
      to: '/family',
      icon: Users,
      title: 'Family',
      badge: memberCount > 0 ? String(memberCount) : undefined,
      badgeColor: 'muted' as const,
    },
    {
      to: '/messages',
      icon: MessageCircle,
      title: 'Messages',
      badge: undefined,
      badgeColor: 'primary' as const,
    },
    {
      to: '/profile',
      icon: User,
      title: 'My Profile',
      badge: undefined,
      badgeColor: 'muted' as const,
    },
  ]

  // Add admin card if user is an organizer
  if (isOrganizer) {
    cards.push({
      to: '/admin',
      icon: Wrench,
      title: 'Admin',
      badge: undefined,
      badgeColor: 'primary' as const,
    })
  }

  return (
    <div className="container mx-auto px-4 py-6">
      {/* Welcome message */}
      <h1
        className={`
          font-bold text-fc-text mb-6
          ${bigMode ? 'text-3xl' : 'text-2xl'}
        `}
      >
        Welcome{user?.display_name ? `, ${user.display_name}` : ''}!
      </h1>

      {/* Card Grid */}
      <div
        className={`
          grid gap-4
          ${bigMode
            ? 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-3'
            : 'grid-cols-2 md:grid-cols-3 lg:grid-cols-4'
          }
        `}
      >
        {cards.map((card) => (
          <DashboardCard
            key={'to' in card ? card.to : card.title}
            {...card}
          />
        ))}
      </div>

      {/* Upcoming Events */}
      <UpcomingEvents events={upcomingEvents} />

      {/* Create Event Modal */}
      <CreateEventModal
        isOpen={showCreateEventModal}
        onClose={() => setShowCreateEventModal(false)}
        onEventCreated={loadDashboardData}
      />
    </div>
  )
}
