import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'

// Mock fetch globally
const mockFetch = vi.fn()
globalThis.fetch = mockFetch

// Import after mock is set
import { api, clearToken, setToken, getToken } from '@/lib/api/client'

describe('API Client', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockFetch.mockReset()
    clearToken()
  })

  afterEach(() => {
    clearToken()
  })

  describe('request() credentials', () => {
    it('adds credentials: include to all requests', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => ({ data: 'test' }),
      })

      await api.get('/test')

      expect(mockFetch).toHaveBeenCalledWith(
        '/api/test',
        expect.objectContaining({
          credentials: 'include',
        }),
      )
    })

    it('adds Content-Type: application/json header', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => ({}),
      })

      await api.get('/test')

      expect(mockFetch).toHaveBeenCalledWith(
        '/api/test',
        expect.objectContaining({
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
          }),
        }),
      )
    })
  })

  describe('request() error handling', () => {
    it('throws on 401 and calls clearToken()', async () => {
      mockFetch.mockResolvedValue({
        ok: false,
        status: 401,
        json: async () => ({ detail: null }),
      })

      await expect(api.get('/protected')).rejects.toThrow(
        'Session expired. Please log in again.',
      )

      // Token functions are no-ops — auth is via httpOnly cookies
      expect(getToken()).toBeNull()
    })

    it('uses backend error message on 401 when available', async () => {
      mockFetch.mockResolvedValue({
        ok: false,
        status: 401,
        json: async () => ({ detail: 'Token revoked by admin' }),
      })

      await expect(api.get('/protected')).rejects.toThrow('Token revoked by admin')
    })

    it('throws with backend error message on 403', async () => {
      mockFetch.mockResolvedValue({
        ok: false,
        status: 403,
        json: async () => ({ detail: 'Admin access required' }),
      })

      await expect(api.get('/admin')).rejects.toThrow('Admin access required')
    })

    it('throws with default message on 403 when no backend message', async () => {
      mockFetch.mockResolvedValue({
        ok: false,
        status: 403,
        json: async () => ({ detail: null }),
      })

      await expect(api.get('/admin')).rejects.toThrow(
        'You do not have permission to perform this action.',
      )
    })

    it('throws with backend error message on 404', async () => {
      mockFetch.mockResolvedValue({
        ok: false,
        status: 404,
        json: async () => ({ detail: 'Event not found' }),
      })

      await expect(api.get('/events/missing')).rejects.toThrow('Event not found')
    })

    it('throws with backend error message on 400', async () => {
      mockFetch.mockResolvedValue({
        ok: false,
        status: 400,
        json: async () => ({ detail: 'Email already registered' }),
      })

      await expect(api.post('/auth/register', {})).rejects.toThrow(
        'Email already registered',
      )
    })

    it('falls back to generic message on unknown error status', async () => {
      mockFetch.mockResolvedValue({
        ok: false,
        status: 500,
        json: async () => ({ detail: null }),
      })

      await expect(api.get('/failing')).rejects.toThrow(
        'Request failed. Please try again.',
      )
    })

    it('handles non-JSON error response gracefully', async () => {
      mockFetch.mockResolvedValue({
        ok: false,
        status: 500,
        json: async () => {
          throw new Error('not JSON')
        },
      })

      await expect(api.get('/crash')).rejects.toThrow(
        'Request failed. Please try again.',
      )
    })
  })

  describe('HTTP methods', () => {
    it('api.get sends GET request', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => ({ result: 'ok' }),
      })

      const result = await api.get<{ result: string }>('/items')

      expect(result).toEqual({ result: 'ok' })
      expect(mockFetch).toHaveBeenCalledWith(
        '/api/items',
        expect.not.objectContaining({ method: 'POST' }),
      )
    })

    it('api.post sends POST request with JSON body', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => ({ id: '123' }),
      })

      const data = { title: 'New Event', event_date: '2026-12-25' }
      await api.post('/events', data)

      expect(mockFetch).toHaveBeenCalledWith(
        '/api/events',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify(data),
        }),
      )
    })

    it('api.put sends PUT request', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => ({ message: 'updated' }),
      })

      await api.put('/events/1', { title: 'Updated' })

      expect(mockFetch).toHaveBeenCalledWith(
        '/api/events/1',
        expect.objectContaining({
          method: 'PUT',
          body: JSON.stringify({ title: 'Updated' }),
        }),
      )
    })

    it('api.delete sends DELETE request', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => ({ message: 'deleted' }),
      })

      await api.delete('/events/1')

      expect(mockFetch).toHaveBeenCalledWith(
        '/api/events/1',
        expect.objectContaining({
          method: 'DELETE',
        }),
      )
    })
  })

  describe('Token management (no-ops — auth via httpOnly cookies)', () => {
    it('getToken always returns null', () => {
      expect(getToken()).toBeNull()
    })

    it('setToken is a no-op', () => {
      setToken('any-token')
      expect(getToken()).toBeNull()
    })

    it('clearToken is a no-op', () => {
      clearToken()
      expect(getToken()).toBeNull()
    })
  })
})
