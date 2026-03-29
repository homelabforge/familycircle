import { useState, useRef, useEffect } from 'react'
import { Outlet } from 'react-router-dom'
import { Heart, Settings, Moon, Sun, Monitor, ZoomIn, ChevronDown, Crown, Check } from 'lucide-react'
import { useTheme } from '@/contexts/ThemeContext'
import { useBigMode } from '@/contexts/BigModeContext'
import { useAuth } from '@/contexts/AuthContext'
import { Link, useNavigate } from 'react-router-dom'
import { settingsApi } from '@/lib/api'

function ThemeToggle() {
  const { theme, setTheme } = useTheme()

  const cycleTheme = async () => {
    const themes: Array<'light' | 'dark' | 'system'> = ['light', 'dark', 'system']
    const currentIndex = themes.indexOf(theme)
    const nextIndex = (currentIndex + 1) % themes.length
    const newTheme = themes[nextIndex]
    setTheme(newTheme)
    // Save to backend (fire and forget)
    try {
      await settingsApi.updateUserPreferences({ theme: newTheme })
    } catch {
      // Ignore - local change still applies
    }
  }

  const Icon = theme === 'light' ? Sun : theme === 'dark' ? Moon : Monitor

  return (
    <button
      onClick={cycleTheme}
      className="p-2 rounded-lg hover:bg-fc-surface-hover transition-colors"
      title={`Theme: ${theme}`}
      aria-label={`Current theme: ${theme}. Click to change.`}
    >
      <Icon className="w-5 h-5 text-fc-text-muted" />
    </button>
  )
}

function BigModeToggle() {
  const { bigMode, toggleBigMode } = useBigMode()

  const handleToggle = async () => {
    const newValue = !bigMode
    toggleBigMode()
    // Save to backend (fire and forget)
    try {
      await settingsApi.updateUserPreferences({ big_mode: newValue })
    } catch {
      // Ignore - local change still applies
    }
  }

  return (
    <button
      onClick={handleToggle}
      className={`p-2 rounded-lg transition-colors ${
        bigMode
          ? 'bg-primary text-white'
          : 'hover:bg-fc-surface-hover text-fc-text-muted'
      }`}
      title={bigMode ? 'Big Mode: ON' : 'Big Mode: OFF'}
      aria-label={`Big Mode is ${bigMode ? 'on' : 'off'}. Click to toggle.`}
    >
      <ZoomIn className="w-5 h-5" />
    </button>
  )
}

function FamilySelector() {
  const { currentFamily, families, switchFamily, refresh } = useAuth()
  const [isOpen, setIsOpen] = useState(false)
  const [switching, setSwitching] = useState(false)
  const dropdownRef = useRef<HTMLDivElement>(null)
  const navigate = useNavigate()

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const handleSwitch = async (familyId: string) => {
    if (familyId === currentFamily?.id || switching) return

    try {
      setSwitching(true)
      await switchFamily(familyId)
      await refresh()
      setIsOpen(false)
      navigate('/')
    } catch {
      // Error handled by context
    } finally {
      setSwitching(false)
    }
  }

  // If no active family but user has families, auto-switch to the first one.
  // This handles edge cases like family deletion where the backend couldn't auto-switch.
  useEffect(() => {
    if (!currentFamily && families.length > 0 && !switching) {
      handleSwitch(families[0].id)
    }
  }, [currentFamily, families]) // eslint-disable-line react-hooks/exhaustive-deps

  if (!currentFamily) return null

  const hasMultipleFamilies = families.length > 1

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        onClick={() => hasMultipleFamilies && setIsOpen(!isOpen)}
        className={`
          flex items-center gap-2 px-3 py-1.5 rounded-lg
          text-fc-text font-medium text-sm
          ${hasMultipleFamilies
            ? 'hover:bg-fc-surface-hover cursor-pointer'
            : 'cursor-default'
          }
          transition-colors
        `}
        disabled={!hasMultipleFamilies}
      >
        <span className="truncate max-w-[150px] md:max-w-[200px]">
          {currentFamily.name}
        </span>
        {hasMultipleFamilies && (
          <ChevronDown className={`w-4 h-4 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
        )}
      </button>

      {/* Dropdown */}
      {isOpen && hasMultipleFamilies && (
        <div className="absolute top-full left-0 mt-1 w-64 bg-fc-surface border border-fc-border rounded-xl shadow-lg z-50">
          <div className="py-2">
            <div className="px-3 py-2 text-xs font-semibold text-fc-text-muted uppercase tracking-wider">
              Switch Family
            </div>
            {families.map((family) => (
              <button
                key={family.id}
                onClick={() => handleSwitch(family.id)}
                disabled={switching}
                className={`
                  w-full px-3 py-2 flex items-center justify-between
                  hover:bg-fc-bg transition-colors
                  ${family.id === currentFamily.id ? 'bg-fc-bg' : ''}
                  disabled:opacity-50
                `}
              >
                <div className="flex items-center gap-2">
                  <span className="text-fc-text text-sm truncate">
                    {family.name}
                  </span>
                  {family.role === 'admin' && (
                    <Crown className="w-3.5 h-3.5 text-warning" />
                  )}
                </div>
                {family.id === currentFamily.id && (
                  <Check className="w-4 h-4 text-primary" />
                )}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

export default function Layout() {
  return (
    <div className="min-h-screen flex flex-col bg-fc-bg">
      {/* Minimal Header */}
      <header className="bg-fc-surface border-b border-fc-border sticky top-0 z-40">
        <div className="container mx-auto px-4">
          <div className="flex items-center justify-between h-14 md:h-16">
            {/* Logo and Family Selector */}
            <div className="flex items-center gap-4">
              <Link to="/" className="flex items-center gap-2">
                <Heart className="w-7 h-7 md:w-8 md:h-8 text-primary" />
                <span className="text-xl md:text-2xl font-bold text-fc-text hidden sm:inline">
                  Family<span className="text-primary">Circle</span>
                </span>
              </Link>

              {/* Family Selector - visible on all screens */}
              <div className="border-l border-fc-border pl-4 hidden sm:block">
                <FamilySelector />
              </div>
            </div>

            {/* Right side controls */}
            <div className="flex items-center gap-1">
              {/* Mobile family selector */}
              <div className="sm:hidden">
                <FamilySelector />
              </div>
              <BigModeToggle />
              <ThemeToggle />
              <Link
                to="/settings"
                className="p-2 rounded-lg hover:bg-fc-surface-hover transition-colors"
                title="Settings"
              >
                <Settings className="w-5 h-5 text-fc-text-muted" />
              </Link>
            </div>
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="flex-1">
        <Outlet />
      </main>

      {/* Footer */}
      <footer className="bg-fc-surface border-t border-fc-border py-3 mt-auto">
        <div className="container mx-auto px-4 text-center text-fc-text-muted text-sm">
          <p>FamilyCircle v2.0.1 - Family event coordination for everyone</p>
        </div>
      </footer>
    </div>
  )
}
