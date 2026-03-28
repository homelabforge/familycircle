import { useMutation, useQueryClient } from '@tanstack/react-query'
import { eventsApi } from '@/lib/api'

export function useCreateEvent() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: eventsApi.create,
    onSuccess: () => {
      // New event changes all lists
      qc.invalidateQueries({ queryKey: ['events'] })
    },
  })
}

export function useUpdateEvent() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Parameters<typeof eventsApi.update>[1] }) =>
      eventsApi.update(id, data),
    onSuccess: () => {
      // Title/date/type could change — affects lists too
      qc.invalidateQueries({ queryKey: ['events'] })
    },
  })
}

export function useDeleteEvent() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: eventsApi.delete,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['events'] })
    },
  })
}

export function useCancelEvent() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, reason }: { id: string; reason?: string }) =>
      eventsApi.cancel(id, reason),
    onSuccess: (_data, variables) => {
      // Cancel only affects this event and the upcoming list
      qc.invalidateQueries({ queryKey: ['events', variables.id] })
      qc.invalidateQueries({ queryKey: ['events', 'upcoming'] })
    },
  })
}

export function useRsvp() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ eventId, status }: { eventId: string; status: 'yes' | 'no' | 'maybe' }) =>
      eventsApi.rsvp(eventId, status),
    onSuccess: (_data, variables) => {
      // RSVP only affects this event's detail and list RSVP badges
      qc.invalidateQueries({ queryKey: ['events', variables.eventId] })
      qc.invalidateQueries({ queryKey: ['events', 'upcoming'] })
    },
  })
}
