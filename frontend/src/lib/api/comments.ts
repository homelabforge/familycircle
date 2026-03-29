import { api } from './client'
import type { CommentReaction, EventComment } from './types'

export const eventCommentsApi = {
  list: (eventId: string) =>
    api.get<{ comments: EventComment[] }>(`/events/${eventId}/comments`),

  create: (eventId: string, content: string) =>
    api.post<EventComment>(`/events/${eventId}/comments`, { content }),

  update: (eventId: string, commentId: string, content: string) =>
    api.put<EventComment>(`/events/${eventId}/comments/${commentId}`, { content }),

  delete: (eventId: string, commentId: string) =>
    api.delete<void>(`/events/${eventId}/comments/${commentId}`),

  pin: (eventId: string, commentId: string) =>
    api.post<EventComment>(`/events/${eventId}/comments/${commentId}/pin`),

  unpin: (eventId: string, commentId: string) =>
    api.delete<EventComment>(`/events/${eventId}/comments/${commentId}/pin`),

  toggleReaction: (eventId: string, commentId: string, emoji: string) =>
    api.post<{ action: string; reactions: CommentReaction[] }>(
      `/events/${eventId}/comments/${commentId}/reactions`,
      { emoji }
    ),
}
