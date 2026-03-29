import { api } from './client'
import type { PotluckInfo, PotluckItem } from './types'

export const potluckApi = {
  get: (eventId: string) => api.get<PotluckInfo>(`/potluck/${eventId}`),

  listItems: (eventId: string) => api.get<{ items: PotluckItem[] }>(`/potluck/${eventId}/items`),

  addItem: (eventId: string, data: {
    name: string
    category?: string
    description?: string
    serves?: number
    dietary_info?: string
    allergens?: string
  }) => api.post<{ message: string; id: string }>(`/potluck/${eventId}/items`, data),

  updateItem: (eventId: string, itemId: string, data: Partial<PotluckItem>) =>
    api.put<{ message: string }>(`/potluck/${eventId}/items/${itemId}`, data),

  deleteItem: (eventId: string, itemId: string) =>
    api.delete<{ message: string }>(`/potluck/${eventId}/items/${itemId}`),

  claim: (eventId: string, itemId: string) =>
    api.post<{ message: string }>(`/potluck/${eventId}/claim/${itemId}`),

  unclaim: (eventId: string, itemId: string) =>
    api.delete<{ message: string }>(`/potluck/${eventId}/claim/${itemId}`),

  getMyItems: (eventId: string) =>
    api.get<{ items: PotluckItem[] }>(`/potluck/${eventId}/my-items`),
}
