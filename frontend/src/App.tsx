import { lazy, Suspense } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Toaster } from 'sonner'
import { ThemeProvider, useTheme } from '@/contexts/ThemeContext'
import { BigModeProvider } from '@/contexts/BigModeContext'
import { AuthProvider, useAuth } from '@/contexts/AuthContext'
import Layout from '@/components/Layout'
import ErrorBoundary from '@/components/ErrorBoundary'

// Auth pages
const Login = lazy(() => import('@/pages/Login'))
const Setup = lazy(() => import('@/pages/Setup'))

// Lazy load all pages for code splitting
const Dashboard = lazy(() => import('@/pages/Dashboard'))
const GiftExchange = lazy(() => import('@/pages/GiftExchange'))
const Potluck = lazy(() => import('@/pages/Potluck'))
const Events = lazy(() => import('@/pages/Events'))
const EventDetail = lazy(() => import('@/pages/EventDetail'))
const Polls = lazy(() => import('@/pages/Polls'))
const PollDetail = lazy(() => import('@/pages/PollDetail'))
const Wishlist = lazy(() => import('@/pages/Wishlist'))
const Family = lazy(() => import('@/pages/Family'))
const Messages = lazy(() => import('@/pages/Messages'))
const Settings = lazy(() => import('@/pages/Settings'))
const Profile = lazy(() => import('@/pages/Profile'))
const About = lazy(() => import('@/pages/About'))

// Admin pages
const Admin = lazy(() => import('@/pages/Admin'))

// Error pages
const NotFound = lazy(() => import('@/pages/NotFound'))

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      refetchOnMount: true,
      staleTime: 30000,
      retry: 1,
    },
  },
})

// Loading skeleton
function LoadingSkeleton() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-fc-bg">
      <div className="text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-fc-primary mx-auto" />
        <p className="mt-4 text-fc-muted">Loading...</p>
      </div>
    </div>
  )
}

// Protected route wrapper
function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading, needsSetup } = useAuth()

  if (isLoading) {
    return <LoadingSkeleton />
  }

  if (needsSetup) {
    return <Navigate to="/setup" replace />
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  return <>{children}</>
}

// Auth route wrapper (redirects to home if already logged in)
function AuthRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading, needsSetup } = useAuth()

  if (isLoading) {
    return <LoadingSkeleton />
  }

  // For setup page, allow if needs setup
  if (needsSetup) {
    return <>{children}</>
  }

  if (isAuthenticated) {
    return <Navigate to="/" replace />
  }

  return <>{children}</>
}

// Setup route wrapper
function SetupRoute({ children }: { children: React.ReactNode }) {
  const { isLoading, needsSetup, isAuthenticated } = useAuth()

  if (isLoading) {
    return <LoadingSkeleton />
  }

  if (isAuthenticated) {
    return <Navigate to="/" replace />
  }

  if (!needsSetup) {
    return <Navigate to="/login" replace />
  }

  return <>{children}</>
}

// Admin route wrapper (for admin pages - family admin or super admin)
function AdminRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isFamilyAdmin, isLoading, needsSetup } = useAuth()

  if (isLoading) {
    return <LoadingSkeleton />
  }

  if (needsSetup) {
    return <Navigate to="/setup" replace />
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  if (!isFamilyAdmin) {
    return <Navigate to="/" replace />
  }

  return <>{children}</>
}

function AppRoutes() {
  const { resolvedTheme } = useTheme()

  return (
    <>
      <Routes>
        {/* Auth routes */}
        <Route
          path="/login"
          element={
            <AuthRoute>
              <Login />
            </AuthRoute>
          }
        />
        <Route
          path="/setup"
          element={
            <SetupRoute>
              <Setup />
            </SetupRoute>
          }
        />

        {/* Protected routes */}
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <Layout />
            </ProtectedRoute>
          }
        >
          <Route index element={<Dashboard />} />
          <Route path="gift-exchange" element={<GiftExchange />} />
          <Route path="gift-exchange/:eventId" element={<GiftExchange />} />
          <Route path="potluck" element={<Potluck />} />
          <Route path="potluck/:eventId" element={<Potluck />} />
          <Route path="events" element={<Events />} />
          <Route path="event/:id" element={<EventDetail />} />
          <Route path="polls" element={<Polls />} />
          <Route path="polls/:id" element={<PollDetail />} />
          <Route path="wishlist" element={<Wishlist />} />
          <Route path="family" element={<Family />} />
          <Route path="messages" element={<Messages />} />
          <Route path="settings" element={<Settings />} />
          <Route path="profile" element={<Profile />} />
          <Route path="about" element={<About />} />

          {/* Admin route - family admins and super admins only */}
          <Route path="admin" element={<AdminRoute><Admin /></AdminRoute>} />

          {/* 404 catch-all */}
          <Route path="*" element={<NotFound />} />
        </Route>

        {/* Global 404 */}
        <Route path="*" element={<NotFound />} />
      </Routes>

      <Toaster position="bottom-right" richColors theme={resolvedTheme} />
    </>
  )
}

function App() {
  return (
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <ThemeProvider>
          <BigModeProvider>
            <AuthProvider>
              <BrowserRouter>
                <Suspense fallback={<LoadingSkeleton />}>
                  <ErrorBoundary>
                    <AppRoutes />
                  </ErrorBoundary>
                </Suspense>
              </BrowserRouter>
            </AuthProvider>
          </BigModeProvider>
        </ThemeProvider>
      </QueryClientProvider>
    </ErrorBoundary>
  )
}

export default App
