import { api, API_BASE } from './client'
import type { Poll, PollTemplate } from './types'

export const pollsApi = {
  list: (eventId?: string) =>
    api.get<{ polls: Poll[] }>(eventId ? `/polls?event_id=${eventId}` : '/polls'),

  get: (pollId: string) => api.get<Poll>(`/polls/${pollId}`),

  create: (data: {
    title: string
    description?: string
    event_id?: string
    allow_multiple?: boolean
    is_anonymous?: boolean
    close_date?: string
    options: { text: string; display_order?: number }[]
  }) => api.post<Poll>('/polls', data),

  vote: (pollId: string, optionIds: string[]) =>
    api.post<Poll>(`/polls/${pollId}/vote`, { option_ids: optionIds }),

  close: (pollId: string) => api.post<Poll>(`/polls/${pollId}/close`),

  delete: (pollId: string) => api.delete<void>(`/polls/${pollId}`),

  exportCsv: async (pollId: string): Promise<void> => {
    const response = await fetch(`${API_BASE}/polls/${pollId}/export`, {
      credentials: 'include',
    })
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: null }))
      throw new Error(error.detail || 'Failed to export poll')
    }
    const blob = await response.blob()
    const disposition = response.headers.get('Content-Disposition')
    const filename = disposition?.match(/filename="(.+)"/)?.[1] || 'poll-export.csv'
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    a.click()
    URL.revokeObjectURL(url)
  },
}

export const pollTemplatesApi = {
  list: () =>
    api.get<{ templates: PollTemplate[] }>('/poll-templates'),

  create: (data: { name: string; description?: string; options: string[]; allow_multiple?: boolean }) =>
    api.post<PollTemplate>('/poll-templates', data),

  delete: (templateId: string) =>
    api.delete<{ message: string }>(`/poll-templates/${templateId}`),
}
