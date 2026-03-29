import { API_BASE } from './client'
import { api } from './client'
import type { EventPhoto } from './types'

export const eventPhotosApi = {
  list: (eventId: string) =>
    api.get<{ photos: EventPhoto[] }>(`/events/${eventId}/photos`),

  upload: async (eventId: string, file: File, caption?: string): Promise<EventPhoto> => {
    const formData = new FormData()
    formData.append('file', file)
    if (caption) {
      formData.append('caption', caption)
    }

    const response = await fetch(`${API_BASE}/events/${eventId}/photos`, {
      method: 'POST',
      credentials: 'include',
      body: formData,
    })

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: null }))
      throw new Error(error.detail || 'Failed to upload photo')
    }

    return response.json()
  },

  delete: (eventId: string, photoId: string) =>
    api.delete<{ message: string }>(`/events/${eventId}/photos/${photoId}`),

  reorder: (eventId: string, photoIds: string[]) =>
    api.put<{ message: string }>(`/events/${eventId}/photos/reorder`, { photo_ids: photoIds }),
}
