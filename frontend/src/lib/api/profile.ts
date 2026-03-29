import { api } from './client'
import type { ProfileVisibility, UserProfile } from './types'

export const profileApi = {
  get: () => api.get<UserProfile>('/profile'),

  update: (data: Partial<UserProfile>) =>
    api.put<{ message: string }>('/profile', data),

  getVisibility: (familyId: string) =>
    api.get<ProfileVisibility>(`/profile/visibility/${familyId}`),

  updateVisibility: (familyId: string, data: Partial<ProfileVisibility>) =>
    api.put<{ message: string }>(`/profile/visibility/${familyId}`, data),

  getHealthInfo: () =>
    api.get<{
      allergies: string | null
      dietary_restrictions: string | null
      medical_needs: string | null
      mobility_notes: string | null
    }>('/profile/health-info'),
}
