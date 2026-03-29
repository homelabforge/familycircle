import { api } from './client'
import type { RegistryItem, RegistryStats } from './types'

export const registryApi = {
  list: (eventId: string) =>
    api.get<{ items: RegistryItem[]; stats: RegistryStats }>(`/events/${eventId}/registry`),

  create: (eventId: string, data: {
    item_name: string
    item_url?: string
    price?: number
    image_url?: string
    quantity?: number
    notes?: string
  }) => api.post<RegistryItem>(`/events/${eventId}/registry`, data),

  update: (eventId: string, itemId: string, data: {
    item_name?: string
    item_url?: string
    price?: number
    image_url?: string
    quantity?: number
    notes?: string
  }) => api.put<RegistryItem>(`/events/${eventId}/registry/${itemId}`, data),

  delete: (eventId: string, itemId: string) =>
    api.delete<void>(`/events/${eventId}/registry/${itemId}`),

  claim: (eventId: string, itemId: string) =>
    api.post<RegistryItem>(`/events/${eventId}/registry/${itemId}/claim`),

  unclaim: (eventId: string, itemId: string) =>
    api.delete<RegistryItem>(`/events/${eventId}/registry/${itemId}/claim`),

  markPurchased: (eventId: string, itemId: string) =>
    api.post<RegistryItem>(`/events/${eventId}/registry/${itemId}/purchase`),
}
