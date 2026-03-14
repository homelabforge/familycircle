import { useQuery } from '@tanstack/react-query'
import { eventsApi, type EventType } from '@/lib/api'

export function useEvents(typeFilter?: EventType) {
  return useQuery({
    queryKey: ['events', typeFilter ?? 'all'],
    queryFn: () => eventsApi.list(typeFilter),
  })
}

export function useUpcomingEvents(limit = 5) {
  return useQuery({
    queryKey: ['events', 'upcoming', limit],
    queryFn: () => eventsApi.listUpcoming(limit),
  })
}

export function useEvent(id: string) {
  return useQuery({
    queryKey: ['events', id],
    queryFn: () => eventsApi.get(id),
    enabled: !!id,
  })
}
