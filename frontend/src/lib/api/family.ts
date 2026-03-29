import { api } from './client'
import type { FamilyMember } from './types'

export const familyApi = {
  listMembers: () => api.get<{ members: FamilyMember[] }>('/family/members'),

  getMember: (userId: string) => api.get<FamilyMember>(`/family/members/${userId}`),

  getAddressBook: () => api.get<{ members: FamilyMember[] }>('/family/address-book'),

  // Admin functions
  invite: (data: { name: string; email: string }) =>
    api.post<{ message: string; dev_token?: string }>('/family/invite', {
      display_name: data.name,
      email: data.email,
    }),

  setRole: (userId: string, role: 'admin' | 'member') =>
    api.post<{ message: string }>(`/family/members/${userId}/role`, { role }),

  removeMember: (userId: string) =>
    api.delete<{ message: string }>(`/family/members/${userId}`),

  adminResetPassword: (userId: string, newPassword: string) =>
    api.post<{ message: string }>('/auth/admin/reset-password', {
      user_id: userId,
      new_password: newPassword,
    }),
}
