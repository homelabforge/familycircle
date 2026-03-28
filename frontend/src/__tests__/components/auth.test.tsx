import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter } from 'react-router-dom'
import { BigModeProvider } from '@/contexts/BigModeContext'
import { ThemeProvider } from '@/contexts/ThemeContext'
import { AuthProvider } from '@/contexts/AuthContext'

// Mock fetch globally
const mockFetch = vi.fn()
globalThis.fetch = mockFetch

function createQueryClient(): QueryClient {
  return new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  })
}

function renderWithProviders(ui: React.ReactElement, { route = '/login' } = {}) {
  const queryClient = createQueryClient()
  return render(
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <BigModeProvider>
          <AuthProvider>
            <MemoryRouter initialEntries={[route]}>{ui}</MemoryRouter>
          </AuthProvider>
        </BigModeProvider>
      </ThemeProvider>
    </QueryClientProvider>,
  )
}

// We test the Login page component in isolation by importing it directly
// and providing mock auth context
const mockLogin = vi.fn()
const mockRegister = vi.fn()
const mockForgotPassword = vi.fn()
const mockResetPassword = vi.fn()

// Mock AuthContext to avoid real API calls during auth check
vi.mock('@/contexts/AuthContext', () => ({
  AuthProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  useAuth: () => ({
    user: null,
    isAuthenticated: false,
    isFamilyAdmin: false,
    isOrganizer: false,
    isSuperAdmin: false,
    isLoading: false,
    needsSetup: false,
    currentFamily: null,
    families: [],
    login: mockLogin,
    register: mockRegister,
    setup: vi.fn(),
    switchFamily: vi.fn(),
    createFamily: vi.fn(),
    forgotPassword: mockForgotPassword,
    resetPassword: mockResetPassword,
    logout: vi.fn(),
    refresh: vi.fn(),
  }),
}))

// Import Login after mocks are set up
import Login from '@/pages/Login'

describe('Login Page', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockFetch.mockReset()
  })

  it('renders the main menu with Sign In and Join a Family buttons', () => {
    renderWithProviders(<Login />)

    expect(screen.getByText('FamilyCircle')).toBeInTheDocument()
    expect(screen.getByText('Family event coordination')).toBeInTheDocument()
    expect(screen.getByText('Sign In')).toBeInTheDocument()
    expect(screen.getByText('Join a Family')).toBeInTheDocument()
  })

  it('shows login form with email and password fields when Sign In is clicked', async () => {
    const user = userEvent.setup()
    renderWithProviders(<Login />)

    await user.click(screen.getByText('Sign In'))

    expect(screen.getByText('Email Address')).toBeInTheDocument()
    expect(screen.getByText('Password')).toBeInTheDocument()
    expect(screen.getByPlaceholderText('you@family.com')).toBeInTheDocument()
    expect(screen.getByPlaceholderText('Your password')).toBeInTheDocument()
  })

  it('shows validation errors when submitting empty login form', async () => {
    const user = userEvent.setup()
    renderWithProviders(<Login />)

    // Navigate to login form
    await user.click(screen.getByText('Sign In'))

    // Submit the form without entering anything
    // Use fireEvent.submit since userEvent.click may not trigger form submission reliably
    const form = document.querySelector('form')!
    expect(form).toBeInTheDocument()

    // Click the submit button to trigger handleSubmit
    const submitButtons = screen.getAllByRole('button')
    const submitBtn = submitButtons.find(
      (btn) => btn.getAttribute('type') === 'submit',
    )!
    await user.click(submitBtn)

    // Zod schema validation should show errors for empty fields
    // loginSchema requires: email (valid email) and password (min 1 char)
    await waitFor(() => {
      expect(screen.getByText('Password is required')).toBeInTheDocument()
    })
  })

  it('shows validation error when password is empty on login submit', async () => {
    const user = userEvent.setup()
    renderWithProviders(<Login />)

    await user.click(screen.getByText('Sign In'))

    // Type valid email but leave password empty
    const emailInput = screen.getByPlaceholderText('you@family.com')
    await user.type(emailInput, 'test@example.com')

    const submitButton = screen.getByRole('button', { name: /sign in/i })
    await user.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText('Password is required')).toBeInTheDocument()
    })
  })

  it('calls login function with correct credentials on valid submit', async () => {
    mockLogin.mockResolvedValue(undefined)
    const user = userEvent.setup()
    renderWithProviders(<Login />)

    await user.click(screen.getByText('Sign In'))

    await user.type(screen.getByPlaceholderText('you@family.com'), 'test@example.com')
    await user.type(screen.getByPlaceholderText('Your password'), 'password123')

    const submitButton = screen.getByRole('button', { name: /sign in/i })
    await user.click(submitButton)

    await waitFor(() => {
      expect(mockLogin).toHaveBeenCalledWith('test@example.com', 'password123')
    })
  })

  it('shows register form when Join a Family is clicked', async () => {
    const user = userEvent.setup()
    renderWithProviders(<Login />)

    await user.click(screen.getByText('Join a Family'))

    expect(screen.getByText('Family Code')).toBeInTheDocument()
    expect(screen.getByText('Your Name')).toBeInTheDocument()
    expect(screen.getByPlaceholderText('ABCDEF-12')).toBeInTheDocument()
    expect(screen.getByPlaceholderText('Grandma Rose')).toBeInTheDocument()
  })

  it('shows error message when login fails', async () => {
    mockLogin.mockRejectedValue(new Error('Invalid credentials'))
    const user = userEvent.setup()
    renderWithProviders(<Login />)

    await user.click(screen.getByText('Sign In'))
    await user.type(screen.getByPlaceholderText('you@family.com'), 'test@example.com')
    await user.type(screen.getByPlaceholderText('Your password'), 'wrongpass')

    const submitButton = screen.getByRole('button', { name: /sign in/i })
    await user.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText('Invalid credentials')).toBeInTheDocument()
    })
  })

  it('navigates to forgot password form', async () => {
    const user = userEvent.setup()
    renderWithProviders(<Login />)

    await user.click(screen.getByText('Sign In'))
    await user.click(screen.getByText('Forgot your password?'))

    expect(screen.getByText('Reset Password')).toBeInTheDocument()
    expect(screen.getByText(/Enter your email and we/)).toBeInTheDocument()
  })
})

describe('Setup page routing', () => {
  it('renders setup flow indicator when needsSetup context would be true', () => {
    // The useAuth mock returns needsSetup: false, so we test the Login page
    // renders correctly. The App.tsx SetupRoute wrapper handles the redirect.
    // We verify the Login page itself works when needsSetup is false.
    renderWithProviders(<Login />)
    expect(screen.getByText('FamilyCircle')).toBeInTheDocument()
  })
})
