import { api } from './client'

export const calendarApi = {
  getFeedUrl: () =>
    api.get<{ feed_token: string; feed_url: string }>('/calendar/feed-url'),

  regenerateToken: () =>
    api.post<{ feed_token: string; feed_url: string; message: string }>('/calendar/regenerate-token'),
}
