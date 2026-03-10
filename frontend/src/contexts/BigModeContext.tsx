import { createContext, useContext, useEffect, useState, ReactNode } from 'react'

interface BigModeContextType {
  bigMode: boolean
  setBigMode: (enabled: boolean) => void
  toggleBigMode: () => void
}

const BigModeContext = createContext<BigModeContextType | undefined>(undefined)

export function BigModeProvider({ children }: { children: ReactNode }) {
  const [bigMode, setBigMode] = useState<boolean>(() => {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('fc-big-mode') === 'true'
    }
    return false
  })

  useEffect(() => {
    const root = document.documentElement
    if (bigMode) {
      root.classList.add('big-mode')
    } else {
      root.classList.remove('big-mode')
    }
    localStorage.setItem('fc-big-mode', String(bigMode))
  }, [bigMode])

  const toggleBigMode = () => setBigMode(prev => !prev)

  return (
    <BigModeContext.Provider value={{ bigMode, setBigMode, toggleBigMode }}>
      {children}
    </BigModeContext.Provider>
  )
}

// eslint-disable-next-line react-refresh/only-export-components
export function useBigMode() {
  const context = useContext(BigModeContext)
  if (context === undefined) {
    throw new Error('useBigMode must be used within a BigModeProvider')
  }
  return context
}
