import { api } from './client'
import type { Event, EventDetail, EventType, WeddingPartyMember } from './types'

export const eventsApi = {
  list: (eventType?: EventType) =>
    api.get<{ events: Event[] }>(eventType ? `/events?event_type=${eventType}` : '/events'),

  listUpcoming: (limit = 5) => api.get<{ events: Event[] }>(`/events/upcoming?limit=${limit}`),

  listHolidays: () => api.get<{ holidays: string[] }>('/events/holidays'),

  get: (id: string) => api.get<EventDetail>(`/events/${id}`),

  create: (data: {
    title: string
    description?: string
    event_date: string
    location_name?: string
    location_address?: string
    has_gift_exchange?: boolean
    has_potluck?: boolean
    has_rsvp?: boolean
    potluck_mode?: string
    potluck_host_providing?: string
    gift_exchange_budget_min?: number
    gift_exchange_budget_max?: number
    gift_exchange_notes?: string
    event_type?: EventType
    parent_event_id?: string
    recurrence_type?: string
    recurrence_end_date?: string
    recurrence_max_occurrences?: number
    holiday_detail?: {
      holiday_name: string
      custom_holiday_name?: string
      year?: number
    }
    birthday_detail?: {
      birthday_person_id?: string
      birthday_person_name: string
      birth_date?: string
      age_turning?: number
      is_secret?: boolean
      theme?: string
    }
    baby_shower_detail?: {
      parent1_name: string
      parent2_name?: string
      baby_name?: string
      gender?: string
      due_date?: string
      registry_url?: string
      is_gender_reveal?: boolean
    }
    wedding_detail?: {
      partner1_name: string
      partner2_name: string
      wedding_date?: string
      venue_name?: string
      registry_url?: string
      color_theme?: string
      sub_event_template?: string
    }
  }) => api.post<{ message: string; id: string }>('/events', data),

  update: (id: string, data: Partial<Event>) =>
    api.put<{ message: string }>(`/events/${id}`, data),

  delete: (id: string) => api.delete<{ message: string }>(`/events/${id}`),

  cancel: (id: string, reason?: string) =>
    api.post<{ message: string }>(`/events/${id}/cancel`, { reason }),

  rsvp: (id: string, status: 'yes' | 'no' | 'maybe') =>
    api.post<{ message: string; conflicts?: Event[] }>(`/events/${id}/rsvp`, { status }),

  removeRsvp: (id: string) => api.delete<{ message: string }>(`/events/${id}/rsvp`),

  getHealthSummary: (id: string) =>
    api.get<{
      event_id: string
      attendee_count: number
      guest_count: number
      shared_count: number
      allergies: string[]
      dietary_restrictions: string[]
      medical_needs: string[]
      mobility_notes: string[]
    }>(`/events/${id}/health-summary`),

  // Sub-events
  listSubEvents: (parentId: string) =>
    api.get<{ sub_events: Event[] }>(`/events/${parentId}/sub-events`),

  createSubEvent: (parentId: string, data: Record<string, unknown>) =>
    api.post<{ message: string; id: string }>(`/events/${parentId}/sub-events`, data),

  // Wedding party
  listWeddingParty: (eventId: string) =>
    api.get<{ members: WeddingPartyMember[] }>(`/events/${eventId}/wedding-party`),

  addWeddingPartyMember: (eventId: string, data: {
    name: string
    role: string
    side?: string
    user_id?: string
  }) => api.post<{ message: string; member: WeddingPartyMember }>(`/events/${eventId}/wedding-party`, data),

  removeWeddingPartyMember: (eventId: string, memberId: string) =>
    api.delete<{ message: string }>(`/events/${eventId}/wedding-party/${memberId}`),
}
