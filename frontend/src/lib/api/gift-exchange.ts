import { api } from './client'
import type { GiftExchangeAssignment, GiftExchangeExclusion, GiftExchangeMessage, GiftExchangeStatus } from './types'

export const giftExchangeApi = {
  getStatus: (eventId: string) =>
    api.get<GiftExchangeStatus>(`/gift-exchange/${eventId}`),

  getAssignment: (eventId: string) =>
    api.get<GiftExchangeAssignment>(`/gift-exchange/${eventId}/assignment`),

  runAssignment: (eventId: string) =>
    api.post<{ message: string; assignment_count: number }>(`/gift-exchange/${eventId}/run`),

  getExclusions: (eventId: string) =>
    api.get<{ exclusions: GiftExchangeExclusion[] }>(`/gift-exchange/${eventId}/exclusions`),

  addExclusion: (eventId: string, user1Id: string, user2Id: string) =>
    api.post<{ message: string; id: string }>(`/gift-exchange/${eventId}/exclusions`, {
      user1_id: user1Id,
      user2_id: user2Id,
    }),

  removeExclusion: (eventId: string, exclusionId: string) =>
    api.delete<{ message: string }>(`/gift-exchange/${eventId}/exclusions/${exclusionId}`),

  sendMessage: (eventId: string, content: string) =>
    api.post<{ message: string }>(`/gift-exchange/${eventId}/message`, { content }),

  getMessages: (eventId: string) =>
    api.get<{ messages: GiftExchangeMessage[] }>(`/gift-exchange/${eventId}/messages`),

  getParticipants: (eventId: string) =>
    api.get<{ participants: { id: string; display_name: string; email: string }[] }>(
      `/gift-exchange/${eventId}/participants`
    ),
}
