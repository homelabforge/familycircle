import { api } from './client'
import type { EventTemplate, WeddingTemplate } from './types'

export const eventTemplatesApi = {
  list: () =>
    api.get<{ templates: EventTemplate[] }>('/event-templates'),

  create: (data: {
    name: string
    description?: string
    template_json: string
  }) => api.post<EventTemplate>('/event-templates', data),

  delete: (id: string) =>
    api.delete<void>(`/event-templates/${id}`),
}

export const WEDDING_TEMPLATES: WeddingTemplate[] = [
  {
    name: 'full_wedding',
    label: 'Full Wedding',
    sub_events: [
      { title: 'Rehearsal Dinner', offset_days: '-1' },
      { title: 'Ceremony', offset_days: '0' },
      { title: 'Reception', offset_days: '0' },
      { title: 'After-Party', offset_days: '0' },
    ],
  },
  {
    name: 'simple_wedding',
    label: 'Simple Wedding',
    sub_events: [
      { title: 'Ceremony', offset_days: '0' },
      { title: 'Reception', offset_days: '0' },
    ],
  },
]
