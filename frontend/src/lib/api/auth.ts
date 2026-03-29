import { api } from './client'
import type { AdminFamilyInfo, AuthResponse, MagicLinkResponse, SetupResponse, SetupStatus, User } from './types'

export const authApi = {
  checkSetupStatus: () => api.get<SetupStatus>('/auth/setup-status'),

  setup: (data: { email: string; password: string; display_name: string; family_name: string }) =>
    api.post<SetupResponse>('/auth/setup', data),

  login: (data: { email: string; password: string }) =>
    api.post<AuthResponse>('/auth/login', data),

  register: (data: { family_code: string; email: string; password: string; display_name: string }) =>
    api.post<AuthResponse>('/auth/register', data),

  me: () => api.get<User>('/auth/me'),

  logout: () => api.post<{ message: string }>('/auth/logout'),

  switchFamily: (familyId: string) =>
    api.post<{ message: string; user: User }>('/auth/switch-family', { family_id: familyId }),

  // Password management
  forgotPassword: (email: string) =>
    api.post<MagicLinkResponse>('/auth/forgot-password', { email }),

  resetPassword: (token: string, newPassword: string) =>
    api.post<AuthResponse>('/auth/reset-password', { token, new_password: newPassword }),

  changePassword: (currentPassword: string, newPassword: string) =>
    api.post<{ message: string }>('/auth/change-password', {
      current_password: currentPassword,
      new_password: newPassword,
    }),

  // Family code
  getFamilyCode: () => api.get<{ code: string; family_name: string }>('/auth/family-code'),

  regenerateFamilyCode: () => api.post<{ code: string; message: string }>('/auth/family-code/regenerate'),

  // Super admin only
  listAllFamilies: () => api.get<{ families: AdminFamilyInfo[] }>('/auth/families'),

  createFamily: (name: string, displayName: string) =>
    api.post<{ message: string; family: { id: string; name: string; family_code: string } }>('/auth/families', {
      name,
      display_name: displayName,
    }),

  deleteFamily: (familyId: string) =>
    api.delete<{ message: string }>(`/auth/families/${familyId}`),
}
