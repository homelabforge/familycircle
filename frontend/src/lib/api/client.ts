/**
 * API client core - request helper, token management
 */

const API_BASE = '/api'

// Token stored in memory (not localStorage for security, but we persist to sessionStorage for page refresh)
let sessionToken: string | null = null

export function getToken(): string | null {
  if (!sessionToken) {
    sessionToken = sessionStorage.getItem('fc_session')
  }
  return sessionToken
}

export function setToken(token: string | null) {
  sessionToken = token
  if (token) {
    sessionStorage.setItem('fc_session', token)
  } else {
    sessionStorage.removeItem('fc_session')
  }
}

export function clearToken() {
  setToken(null)
}

async function request<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...options.headers,
  }

  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers,
    credentials: 'include',
  })

  if (!response.ok) {
    // Try to get the specific error message from the backend
    const error = await response.json().catch(() => ({ detail: null }))
    const backendMessage = error.detail

    // Handle specific status codes with fallbacks (prefer backend message)
    if (response.status === 401) {
      clearToken()
      throw new Error(backendMessage || 'Session expired. Please log in again.')
    }
    if (response.status === 403) {
      throw new Error(backendMessage || 'You do not have permission to perform this action.')
    }
    if (response.status === 404) {
      throw new Error(backendMessage || 'The requested resource was not found.')
    }
    if (response.status === 400) {
      throw new Error(backendMessage || 'Invalid request. Please check your input.')
    }

    throw new Error(backendMessage || 'Request failed. Please try again.')
  }

  return response.json()
}

export const api = {
  get: <T>(endpoint: string) => request<T>(endpoint),
  post: <T>(endpoint: string, data?: unknown) =>
    request<T>(endpoint, { method: 'POST', body: data ? JSON.stringify(data) : undefined }),
  put: <T>(endpoint: string, data?: unknown) =>
    request<T>(endpoint, { method: 'PUT', body: data ? JSON.stringify(data) : undefined }),
  delete: <T>(endpoint: string) => request<T>(endpoint, { method: 'DELETE' }),
}

export { API_BASE }
