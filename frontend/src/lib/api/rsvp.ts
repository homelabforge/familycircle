import { api } from './client'
import type { RSVPGuest } from './types'

export const rsvpGuestsApi = {
  list: (eventId: string) =>
    api.get<{ guests: RSVPGuest[] }>(`/events/${eventId}/rsvp/guests`),

  add: (eventId: string, data: {
    guest_name: string
    dietary_restrictions?: string
    allergies?: string
  }) => api.post<RSVPGuest>(`/events/${eventId}/rsvp/guests`, data),

  update: (eventId: string, guestId: string, data: {
    guest_name?: string
    dietary_restrictions?: string
    allergies?: string
  }) => api.put<RSVPGuest>(`/events/${eventId}/rsvp/guests/${guestId}`, data),

  delete: (eventId: string, guestId: string) =>
    api.delete<void>(`/events/${eventId}/rsvp/guests/${guestId}`),
}
