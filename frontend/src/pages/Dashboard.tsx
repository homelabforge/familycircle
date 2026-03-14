import { useState } from 'react'
import {
  Gift,
  Users,
  MessageCircle,
  Wrench,
  User,
  Plus,
  BarChart3,
} from 'lucide-react'
import { useQueryClient } from '@tanstack/react-query'
import DashboardCard from '@/components/DashboardCard'
import CreateEventModal from '@/components/CreateEventModal'
import UpcomingEvents from '@/components/UpcomingEvents'
import { useAuth } from '@/contexts/AuthContext'
import { useBigMode } from '@/contexts/BigModeContext'
import { useUpcomingEvents } from '@/hooks/queries/useEvents'
import { useFamilyMembers } from '@/hooks/queries/useFamily'
import { type EventType } from '@/lib/api'

interface UpcomingEvent {
  id: string
  title: string
  date: string
  time: string
  rsvpStatus: 'yes' | 'no' | 'maybe' | null
  isCancelled?: boolean
  eventType?: EventType
}

export default function Dashboard() {
  const { user, isOrganizer } = useAuth()
  const { bigMode } = useBigMode()
  const queryClient = useQueryClient()
  const [showCreateEventModal, setShowCreateEventModal] = useState(false)

  const { data: eventsData } = useUpcomingEvents(5)
  const { data: membersData } = useFamilyMembers()

  const upcomingEvents: UpcomingEvent[] = (eventsData?.events ?? []).map((e) => ({
    id: e.id,
    title: e.title,
    date: new Date(e.event_date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
    time: new Date(e.event_date).toLocaleTimeString('en-US', {
      hour: 'numeric',
      minute: '2-digit',
    }),
    rsvpStatus: e.user_rsvp as 'yes' | 'no' | 'maybe' | null,
    isCancelled: e.is_cancelled,
    eventType: e.event_type,
  }))
  const memberCount = membersData?.members.length ?? 0

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
      badgeColor: 'primary' as const,
    },
    {
      to: '/polls',
      icon: BarChart3,
      title: 'Polls',
      badge: undefined,
      badgeColor: 'primary' as const,
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
      badgeColor: 'primary' as const,
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
        onEventCreated={() => queryClient.invalidateQueries({ queryKey: ['events'] })}
      />
    </div>
  )
}
