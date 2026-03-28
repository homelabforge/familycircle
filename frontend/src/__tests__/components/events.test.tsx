import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter } from 'react-router-dom'
import { BigModeProvider } from '@/contexts/BigModeContext'
import type { Event } from '@/lib/api/types'

// Mock fetch globally
const mockFetch = vi.fn()
globalThis.fetch = mockFetch

// Mock AuthContext
vi.mock('@/contexts/AuthContext', () => ({
  AuthProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  useAuth: () => ({
    user: null,
    isAuthenticated: true,
    isFamilyAdmin: false,
    isOrganizer: false,
    isSuperAdmin: false,
    isLoading: false,
    needsSetup: false,
    currentFamily: null,
    families: [],
    login: vi.fn(),
    register: vi.fn(),
    setup: vi.fn(),
    switchFamily: vi.fn(),
    createFamily: vi.fn(),
    forgotPassword: vi.fn(),
    resetPassword: vi.fn(),
    logout: vi.fn(),
    refresh: vi.fn(),
  }),
}))

import Events from '@/pages/Events'
import UpcomingEvents from '@/components/UpcomingEvents'

function createQueryClient(): QueryClient {
  return new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  })
}

function renderWithProviders(ui: React.ReactElement) {
  const queryClient = createQueryClient()
  return render(
    <QueryClientProvider client={queryClient}>
      <BigModeProvider>
        <MemoryRouter>{ui}</MemoryRouter>
      </BigModeProvider>
    </QueryClientProvider>,
  )
}

function makeEvent(overrides: Partial<Event> = {}): Event {
  return {
    id: 'evt-1',
    family_id: 'fam-1',
    created_by_id: 'user-1',
    title: 'Thanksgiving Dinner',
    event_date: '2026-11-26T18:00:00',
    event_type: 'holiday',
    has_gift_exchange: false,
    has_potluck: true,
    has_rsvp: true,
    gift_exchange_assigned: false,
    is_cancelled: false,
    rsvp_counts: { yes: 5, no: 1, maybe: 2 },
    can_manage: false,
    ...overrides,
  }
}

describe('Events Page', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockFetch.mockReset()
  })

  it('renders loading spinner while fetching events', () => {
    // Never resolve the fetch so it stays loading
    mockFetch.mockReturnValue(new Promise(() => {}))
    renderWithProviders(<Events />)

    // The Events page shows a Loader2 spinner when loading
    // It uses Loader2 from lucide-react with class "animate-spin"
    const spinner = document.querySelector('.animate-spin')
    expect(spinner).toBeInTheDocument()
  })

  it('renders event cards when data is available', async () => {
    const events = [
      makeEvent({ id: 'evt-1', title: 'Thanksgiving Dinner', event_type: 'holiday' }),
      makeEvent({ id: 'evt-2', title: 'Mom Birthday', event_type: 'birthday' }),
    ]

    mockFetch.mockResolvedValue({
      ok: true,
      json: async () => ({ events }),
    })

    renderWithProviders(<Events />)

    await waitFor(() => {
      expect(screen.getByText('Thanksgiving Dinner')).toBeInTheDocument()
    })
    expect(screen.getByText('Mom Birthday')).toBeInTheDocument()
    // "Holiday" and "Birthday" appear in both filter pills and event type badges
    expect(screen.getAllByText('Holiday').length).toBeGreaterThanOrEqual(2)
    expect(screen.getAllByText('Birthday').length).toBeGreaterThanOrEqual(2)
  })

  it('renders empty state when no events exist', async () => {
    mockFetch.mockResolvedValue({
      ok: true,
      json: async () => ({ events: [] }),
    })

    renderWithProviders(<Events />)

    await waitFor(() => {
      expect(screen.getByText('No events scheduled yet.')).toBeInTheDocument()
    })
  })

  it('renders event badges for potluck and gift exchange', async () => {
    const events = [
      makeEvent({
        id: 'evt-1',
        title: 'Holiday Party',
        has_potluck: true,
        has_gift_exchange: true,
      }),
    ]

    mockFetch.mockResolvedValue({
      ok: true,
      json: async () => ({ events }),
    })

    renderWithProviders(<Events />)

    await waitFor(() => {
      expect(screen.getByText('Holiday Party')).toBeInTheDocument()
    })
    expect(screen.getByText('Potluck')).toBeInTheDocument()
    expect(screen.getByText('Gift Exchange')).toBeInTheDocument()
  })

  it('renders cancelled event with strikethrough styling', async () => {
    const events = [
      makeEvent({
        id: 'evt-1',
        title: 'Cancelled Event',
        is_cancelled: true,
      }),
    ]

    mockFetch.mockResolvedValue({
      ok: true,
      json: async () => ({ events }),
    })

    renderWithProviders(<Events />)

    await waitFor(() => {
      expect(screen.getByText('Cancelled Event')).toBeInTheDocument()
    })
    expect(screen.getByText('Cancelled')).toBeInTheDocument()
  })

  it('shows RSVP status on event cards', async () => {
    const events = [
      makeEvent({
        id: 'evt-1',
        title: 'Family BBQ',
        user_rsvp: 'yes',
      }),
    ]

    mockFetch.mockResolvedValue({
      ok: true,
      json: async () => ({ events }),
    })

    renderWithProviders(<Events />)

    await waitFor(() => {
      expect(screen.getByText('Family BBQ')).toBeInTheDocument()
    })
    expect(screen.getByText('RSVP: yes')).toBeInTheDocument()
  })

  it('shows type filter pills', async () => {
    mockFetch.mockResolvedValue({
      ok: true,
      json: async () => ({ events: [] }),
    })

    renderWithProviders(<Events />)

    await waitFor(() => {
      expect(screen.getByText('All')).toBeInTheDocument()
    })
    expect(screen.getByText('General')).toBeInTheDocument()
    expect(screen.getByText('Holiday')).toBeInTheDocument()
    expect(screen.getByText('Birthday')).toBeInTheDocument()
    expect(screen.getByText('Baby Shower')).toBeInTheDocument()
    expect(screen.getByText('Wedding')).toBeInTheDocument()
  })
})

describe('UpcomingEvents Component', () => {
  it('renders nothing when events array is empty', () => {
    const { container } = renderWithProviders(<UpcomingEvents events={[]} />)
    expect(container.innerHTML).toBe('')
  })

  it('renders upcoming event cards with RSVP status', () => {
    const events = [
      {
        id: 'evt-1',
        title: 'Easter Brunch',
        date: 'Sunday, April 5, 2026',
        time: '10:00 AM',
        rsvpStatus: 'yes' as const,
        eventType: 'holiday' as const,
      },
      {
        id: 'evt-2',
        title: 'Birthday Party',
        date: 'Saturday, May 1, 2026',
        time: '3:00 PM',
        rsvpStatus: null,
        eventType: 'birthday' as const,
      },
    ]

    renderWithProviders(<UpcomingEvents events={events} />)

    expect(screen.getByText('Upcoming Events')).toBeInTheDocument()
    expect(screen.getByText('Easter Brunch')).toBeInTheDocument()
    expect(screen.getByText('Birthday Party')).toBeInTheDocument()
    expect(screen.getByText('Going')).toBeInTheDocument()
    expect(screen.getByText('RSVP Needed')).toBeInTheDocument()
  })

  it('shows cancelled badge for cancelled events', () => {
    const events = [
      {
        id: 'evt-1',
        title: 'Cancelled Gathering',
        date: 'Friday, June 5, 2026',
        time: '6:00 PM',
        isCancelled: true,
      },
    ]

    renderWithProviders(<UpcomingEvents events={events} />)

    expect(screen.getByText('Cancelled Gathering')).toBeInTheDocument()
    expect(screen.getByText('Cancelled')).toBeInTheDocument()
  })
})
