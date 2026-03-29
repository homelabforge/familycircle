import { api } from './client'
import type { NotificationSettings, Settings, UserPreferences } from './types'

export const settingsApi = {
  getSettings: () => api.get<{ settings: Settings }>('/settings'),

  // Generic update that routes to global settings endpoint
  updateSettings: (data: Partial<Settings>) =>
    api.put<{ message: string }>('/settings/global', data),

  updateGlobalSettings: (data: Partial<Settings>) =>
    api.put<{ message: string }>('/settings/global', data),

  updateFamilySettings: (data: { theme_color?: string }) =>
    api.put<{ message: string }>('/settings/family', data),

  getFamilyCode: () => api.get<{ code: string; family_name: string }>('/settings/family-code'),

  regenerateFamilyCode: () => api.post<{ code: string }>('/settings/family-code/regenerate'),

  getUserPreferences: () => api.get<UserPreferences>('/settings/user-preferences'),

  updateUserPreferences: (data: Partial<UserPreferences>) =>
    api.put<{ message: string } & UserPreferences>('/settings/user-preferences', data),
}

export const notificationsApi = {
  getSettings: () =>
    api.get<{ settings: NotificationSettings }>('/notifications'),

  updateSettings: (data: Partial<NotificationSettings>) =>
    api.put<{ message: string }>('/notifications', data),

  testService: (service: string) =>
    api.post<{ success: boolean; message: string }>('/notifications/test', { service }),
}
