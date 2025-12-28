import { useEffect, useState } from 'react'
import { Settings as SettingsIcon, Moon, Sun, Monitor, ZoomIn, Loader2 } from 'lucide-react'
import BackButton from '@/components/BackButton'
import { useBigMode } from '@/contexts/BigModeContext'
import { useTheme } from '@/contexts/ThemeContext'
import { settingsApi } from '@/lib/api'

export default function Settings() {
  const { bigMode, setBigMode } = useBigMode()
  const { theme, setTheme } = useTheme()
  const [saving, setSaving] = useState(false)

  // Note: We don't load preferences on mount because the theme/bigMode
  // contexts already handle persistence. Loading here would override
  // any changes made via the quick-access toggles in the header.

  const handleBigModeToggle = async () => {
    const newValue = !bigMode
    setBigMode(newValue)
    try {
      setSaving(true)
      await settingsApi.updateUserPreferences({ big_mode: newValue })
    } catch (err) {
      console.error('Failed to save preference:', err)
    } finally {
      setSaving(false)
    }
  }

  const handleThemeChange = async (newTheme: 'light' | 'dark' | 'system') => {
    setTheme(newTheme)
    try {
      setSaving(true)
      await settingsApi.updateUserPreferences({ theme: newTheme })
    } catch (err) {
      console.error('Failed to save preference:', err)
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="container mx-auto px-4 py-6">
      <BackButton />

      <div className="mt-4">
        <h1
          className={`
            flex items-center gap-3 font-bold text-fc-text mb-6
            ${bigMode ? 'text-3xl' : 'text-2xl'}
          `}
        >
          <SettingsIcon className={bigMode ? 'w-9 h-9' : 'w-7 h-7'} />
          Settings
          {saving && <Loader2 className="w-5 h-5 animate-spin text-fc-text-muted" />}
        </h1>

        <div className="space-y-6">
          {/* Big Mode */}
          <div className="bg-fc-surface border border-fc-border rounded-2xl p-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 bg-primary/10 rounded-xl flex items-center justify-center">
                  <ZoomIn className="w-6 h-6 text-primary" />
                </div>
                <div>
                  <h2
                    className={`
                      font-semibold text-fc-text
                      ${bigMode ? 'text-xl' : 'text-lg'}
                    `}
                  >
                    Big Mode
                  </h2>
                  <p className={`text-fc-text-muted ${bigMode ? 'text-base' : 'text-sm'}`}>
                    Larger text and buttons for easier reading
                  </p>
                </div>
              </div>
              <button
                onClick={handleBigModeToggle}
                className={`
                  relative w-14 h-8 rounded-full transition-colors
                  ${bigMode ? 'bg-primary' : 'bg-fc-border'}
                `}
              >
                <span
                  className={`
                    absolute top-1 w-6 h-6 bg-white rounded-full transition-transform
                    ${bigMode ? 'translate-x-7' : 'translate-x-1'}
                  `}
                />
              </button>
            </div>
          </div>

          {/* Theme */}
          <div className="bg-fc-surface border border-fc-border rounded-2xl p-6">
            <div className="flex items-center gap-4 mb-4">
              <div className="w-12 h-12 bg-primary/10 rounded-xl flex items-center justify-center">
                {theme === 'light' ? (
                  <Sun className="w-6 h-6 text-primary" />
                ) : theme === 'dark' ? (
                  <Moon className="w-6 h-6 text-primary" />
                ) : (
                  <Monitor className="w-6 h-6 text-primary" />
                )}
              </div>
              <div>
                <h2
                  className={`
                    font-semibold text-fc-text
                    ${bigMode ? 'text-xl' : 'text-lg'}
                  `}
                >
                  Theme
                </h2>
                <p className={`text-fc-text-muted ${bigMode ? 'text-base' : 'text-sm'}`}>
                  Choose your preferred appearance
                </p>
              </div>
            </div>

            <div className={`grid gap-3 ${bigMode ? 'grid-cols-1 sm:grid-cols-3' : 'grid-cols-3'}`}>
              <button
                onClick={() => handleThemeChange('light')}
                className={`
                  flex items-center justify-center gap-2 rounded-xl border-2 transition-colors
                  ${bigMode ? 'px-4 py-4 text-lg' : 'px-3 py-3'}
                  ${
                    theme === 'light'
                      ? 'border-primary bg-primary/10 text-primary'
                      : 'border-fc-border text-fc-text hover:border-primary/50'
                  }
                `}
              >
                <Sun className={bigMode ? 'w-6 h-6' : 'w-5 h-5'} />
                Light
              </button>
              <button
                onClick={() => handleThemeChange('dark')}
                className={`
                  flex items-center justify-center gap-2 rounded-xl border-2 transition-colors
                  ${bigMode ? 'px-4 py-4 text-lg' : 'px-3 py-3'}
                  ${
                    theme === 'dark'
                      ? 'border-primary bg-primary/10 text-primary'
                      : 'border-fc-border text-fc-text hover:border-primary/50'
                  }
                `}
              >
                <Moon className={bigMode ? 'w-6 h-6' : 'w-5 h-5'} />
                Dark
              </button>
              <button
                onClick={() => handleThemeChange('system')}
                className={`
                  flex items-center justify-center gap-2 rounded-xl border-2 transition-colors
                  ${bigMode ? 'px-4 py-4 text-lg' : 'px-3 py-3'}
                  ${
                    theme === 'system'
                      ? 'border-primary bg-primary/10 text-primary'
                      : 'border-fc-border text-fc-text hover:border-primary/50'
                  }
                `}
              >
                <Monitor className={bigMode ? 'w-6 h-6' : 'w-5 h-5'} />
                System
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
