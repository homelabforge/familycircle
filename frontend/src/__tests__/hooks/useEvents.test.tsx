import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import type { ReactNode } from 'react'

// Mock fetch globally
const mockFetch = vi.fn()
globalThis.fetch = mockFetch

import { useEvents, useUpcomingEvents } from '@/hooks/queries/useEvents'

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  })
  return function Wrapper({ children }: { children: ReactNode }) {
    return (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    )
  }
}

describe('useEvents', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockFetch.mockReset()
  })

  it('returns event data from the API', async () => {
    const mockEvents = [
      {
        id: 'evt-1',
        title: 'Thanksgiving',
        event_date: '2026-11-26T18:00:00',
        event_type: 'holiday',
      },
      {
        id: 'evt-2',
        title: 'Birthday',
        event_date: '2026-12-01T14:00:00',
        event_type: 'birthday',
      },
    ]

    mockFetch.mockResolvedValue({
      ok: true,
      json: async () => ({ events: mockEvents }),
    })

    const { result } = renderHook(() => useEvents(), {
      wrapper: createWrapper(),
    })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(result.current.data?.events).toHaveLength(2)
    expect(result.current.data?.events[0].title).toBe('Thanksgiving')
    expect(result.current.data?.events[1].title).toBe('Birthday')

    // Verify the correct endpoint was called
    expect(mockFetch).toHaveBeenCalledWith(
      '/api/events',
      expect.objectContaining({
        credentials: 'include',
      }),
    )
  })

  it('passes event type filter to the API', async () => {
    mockFetch.mockResolvedValue({
      ok: true,
      json: async () => ({ events: [] }),
    })

    const { result } = renderHook(() => useEvents('holiday'), {
      wrapper: createWrapper(),
    })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(mockFetch).toHaveBeenCalledWith(
      '/api/events?event_type=holiday',
      expect.objectContaining({
        credentials: 'include',
      }),
    )
  })

  it('returns error state when API fails', async () => {
    mockFetch.mockResolvedValue({
      ok: false,
      status: 500,
      json: async () => ({ detail: 'Internal server error' }),
    })

    const { result } = renderHook(() => useEvents(), {
      wrapper: createWrapper(),
    })

    await waitFor(() => {
      expect(result.current.isError).toBe(true)
    })

    expect(result.current.error).toBeInstanceOf(Error)
    expect(result.current.error?.message).toBe('Internal server error')
  })
})

describe('useUpcomingEvents', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockFetch.mockReset()
  })

  it('calls upcoming endpoint with default limit of 5', async () => {
    mockFetch.mockResolvedValue({
      ok: true,
      json: async () => ({ events: [] }),
    })

    const { result } = renderHook(() => useUpcomingEvents(), {
      wrapper: createWrapper(),
    })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(mockFetch).toHaveBeenCalledWith(
      '/api/events/upcoming?limit=5',
      expect.objectContaining({
        credentials: 'include',
      }),
    )
  })

  it('respects custom limit parameter', async () => {
    mockFetch.mockResolvedValue({
      ok: true,
      json: async () => ({ events: [] }),
    })

    const { result } = renderHook(() => useUpcomingEvents(3), {
      wrapper: createWrapper(),
    })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(mockFetch).toHaveBeenCalledWith(
      '/api/events/upcoming?limit=3',
      expect.objectContaining({
        credentials: 'include',
      }),
    )
  })

  it('returns upcoming events data', async () => {
    const mockEvents = [
      { id: 'evt-1', title: 'Next Event', event_date: '2026-04-01T10:00:00' },
    ]

    mockFetch.mockResolvedValue({
      ok: true,
      json: async () => ({ events: mockEvents }),
    })

    const { result } = renderHook(() => useUpcomingEvents(10), {
      wrapper: createWrapper(),
    })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(result.current.data?.events).toHaveLength(1)
    expect(result.current.data?.events[0].title).toBe('Next Event')
  })
})
