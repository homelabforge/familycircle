import { api } from './client'
import type { BabyShowerUpdate } from './types'

export const babyShowerUpdatesApi = {
  list: (eventId: string) =>
    api.get<{ updates: BabyShowerUpdate[] }>(`/events/${eventId}/baby-shower-updates`),

  create: (eventId: string, data: {
    update_type: string
    title: string
    update_date?: string
    notes?: string
    photo_id?: string
  }) => api.post<BabyShowerUpdate>(`/events/${eventId}/baby-shower-updates`, data),

  delete: (eventId: string, updateId: string) =>
    api.delete<void>(`/events/${eventId}/baby-shower-updates/${updateId}`),
}
