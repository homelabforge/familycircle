import { createContext, useContext, useState, useEffect, ReactNode, useCallback } from 'react'
import { authApi, User, FamilyInfo, setToken, clearToken, getToken } from '@/lib/api'

interface AuthContextType {
  user: User | null
  isAuthenticated: boolean
  isFamilyAdmin: boolean
  isOrganizer: boolean // Alias for isFamilyAdmin
  isSuperAdmin: boolean
  isLoading: boolean
  needsSetup: boolean | null
  currentFamily: FamilyInfo | null
  families: FamilyInfo[]
  login: (email: string, password: string) => Promise<void>
  register: (familyCode: string, email: string, password: string, displayName: string) => Promise<void>
  setup: (email: string, password: string, displayName: string, familyName: string) => Promise<{ familyCode: string }>
  switchFamily: (familyId: string) => Promise<void>
  createFamily: (familyName: string, displayName: string) => Promise<{ familyCode: string }>
  forgotPassword: (email: string) => Promise<string | undefined>
  resetPassword: (token: string, newPassword: string) => Promise<void>
  logout: () => Promise<void>
  refresh: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [needsSetup, setNeedsSetup] = useState<boolean | null>(null)

  const checkAuth = useCallback(async () => {
    try {
      // First check if setup is needed
      const setupStatus = await authApi.checkSetupStatus()
      setNeedsSetup(setupStatus.needs_setup)

      // If we have a token, try to validate it
      if (getToken()) {
        const u = await authApi.me()
        setUser(u)
      }
    } catch {
      // Not authenticated or token invalid
      clearToken()
      setUser(null)
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    checkAuth()
  }, [checkAuth])

  // Periodically refresh auth to catch role changes (every 30 seconds)
  useEffect(() => {
    if (!user) return

    const interval = setInterval(() => {
      checkAuth()
    }, 30000) // 30 seconds

    return () => clearInterval(interval)
  }, [user, checkAuth])

  const setup = async (email: string, password: string, displayName: string, familyName: string) => {
    const response = await authApi.setup({ email, password, display_name: displayName, family_name: familyName })
    setToken(response.session_token)
    setUser(response.user)
    setNeedsSetup(false)
    return { familyCode: response.family.family_code }
  }

  const login = async (email: string, password: string) => {
    const response = await authApi.login({ email, password })
    setToken(response.session_token)
    setUser(response.user)
  }

  const register = async (familyCode: string, email: string, password: string, displayName: string) => {
    const response = await authApi.register({
      family_code: familyCode,
      email,
      password,
      display_name: displayName,
    })
    setToken(response.session_token)
    setUser(response.user)
  }

  const switchFamily = async (familyId: string) => {
    const response = await authApi.switchFamily(familyId)
    setUser(response.user)
  }

  const createFamily = async (familyName: string, displayName: string) => {
    const response = await authApi.createFamily(familyName, displayName)
    // Refresh user to get updated families list
    await checkAuth()
    return { familyCode: response.family.family_code }
  }

  const forgotPassword = async (email: string): Promise<string | undefined> => {
    const response = await authApi.forgotPassword(email)
    return response.dev_token
  }

  const resetPassword = async (token: string, newPassword: string) => {
    const response = await authApi.resetPassword(token, newPassword)
    setToken(response.session_token)
    setUser(response.user)
  }

  const logout = async () => {
    try {
      await authApi.logout()
    } catch {
      // Ignore logout errors
    }
    clearToken()
    setUser(null)
  }

  const refresh = async () => {
    await checkAuth()
  }

  // Compute derived state
  const currentFamily = user?.families.find(f => f.id === user.current_family_id) ?? null
  const isFamilyAdmin = currentFamily?.role === 'admin' || user?.is_super_admin || false
  const isSuperAdmin = user?.is_super_admin || false

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        isFamilyAdmin,
        isOrganizer: isFamilyAdmin, // Alias
        isSuperAdmin,
        isLoading,
        needsSetup,
        currentFamily,
        families: user?.families ?? [],
        login,
        register,
        setup,
        switchFamily,
        createFamily,
        forgotPassword,
        resetPassword,
        logout,
        refresh,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

// eslint-disable-next-line react-refresh/only-export-components
export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
