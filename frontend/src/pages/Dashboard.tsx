import { useEffect, useState } from 'react'
import {
  TreePine,
  UtensilsCrossed,
  Calendar,
  Gift,
  Users,
  MessageCircle,
  Wrench,
  User,
} from 'lucide-react'
import DashboardCard from '@/components/DashboardCard'
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
  const [hasSecretSanta, setHasSecretSanta] = useState(false)
  const [hasPotluck, setHasPotluck] = useState(false)

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
      }))

      setUpcomingEvents(formatted)
      setEventCount(eventsRes.events.length)
      setMemberCount(membersRes.members.length)
      setHasSecretSanta(eventsRes.events.some((e) => e.has_secret_santa))
      setHasPotluck(eventsRes.events.some((e) => e.has_potluck))
    } catch {
      // Silently fail - dashboard will show empty state
    }
  }

  useEffect(() => {
    loadDashboardData()
  }, [])

  const cards = [
    ...(hasSecretSanta
      ? [
          {
            to: '/secret-santa',
            icon: TreePine,
            title: 'Secret Santa',
            badge: undefined,
            badgeColor: 'success' as const,
          },
        ]
      : []),
    ...(hasPotluck
      ? [
          {
            to: '/potluck',
            icon: UtensilsCrossed,
            title: 'Potluck',
            badge: undefined,
            badgeColor: 'warning' as const,
          },
        ]
      : []),
    {
      to: '/events',
      icon: Calendar,
      title: 'Events',
      badge: eventCount > 0 ? String(eventCount) : undefined,
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
            key={card.to}
            to={card.to}
            icon={card.icon}
            title={card.title}
            badge={card.badge}
            badgeColor={card.badgeColor}
          />
        ))}
      </div>

      {/* Upcoming Events */}
      <UpcomingEvents events={upcomingEvents} />
    </div>
  )
}
