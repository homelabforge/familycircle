import { useState } from 'react'
import { Settings as SettingsIcon, Moon, Sun, Monitor, ZoomIn, Loader2, Bell, Calendar, Copy, Check, RefreshCw } from 'lucide-react'
import BackButton from '@/components/BackButton'
import { useBigMode } from '@/contexts/BigModeContext'
import { useTheme } from '@/contexts/ThemeContext'
import { useAuth } from '@/contexts/AuthContext'
import { settingsApi, calendarApi } from '@/lib/api'
import NotificationsTab from '@/components/settings/NotificationsTab'

type SettingsTab = 'preferences' | 'notifications'

export default function Settings() {
  const { bigMode, setBigMode } = useBigMode()
  const { theme, setTheme } = useTheme()
  const { isSuperAdmin, isFamilyAdmin } = useAuth()
  const [saving, setSaving] = useState(false)
  const [activeTab, setActiveTab] = useState<SettingsTab>('preferences')
  const [feedUrl, setFeedUrl] = useState<string | null>(null)
  const [feedLoading, setFeedLoading] = useState(false)
  const [feedCopied, setFeedCopied] = useState(false)
  const [feedRegenerating, setFeedRegenerating] = useState(false)

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

  const loadFeedUrl = async () => {
    if (feedUrl) return // Already loaded
    try {
      setFeedLoading(true)
      const data = await calendarApi.getFeedUrl()
      setFeedUrl(`${window.location.origin}${data.feed_url}`)
    } catch {
      // Non-critical
    } finally {
      setFeedLoading(false)
    }
  }

  const handleCopyFeed = async () => {
    if (!feedUrl) return
    await navigator.clipboard.writeText(feedUrl)
    setFeedCopied(true)
    setTimeout(() => setFeedCopied(false), 2000)
  }

  const handleRegenerateFeed = async () => {
    if (!confirm('Regenerate calendar feed URL? The old URL will stop working.')) return
    try {
      setFeedRegenerating(true)
      const data = await calendarApi.regenerateToken()
      setFeedUrl(`${window.location.origin}${data.feed_url}`)
    } catch (err) {
      console.error('Failed to regenerate feed:', err)
    } finally {
      setFeedRegenerating(false)
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

        {/* Tab Navigation — only show if super admin has notifications tab */}
        {isSuperAdmin && (
          <div className="flex gap-1 mb-6 p-1 bg-fc-bg/50 rounded-xl border border-fc-border w-fit">
            <button
              onClick={() => setActiveTab('preferences')}
              className={`flex items-center gap-2 rounded-lg transition-colors ${
                bigMode ? 'px-4 py-2.5 text-base' : 'px-3 py-2 text-sm'
              } ${
                activeTab === 'preferences'
                  ? 'bg-primary text-white shadow-sm'
                  : 'text-fc-text-muted hover:text-fc-text hover:bg-fc-surface'
              }`}
            >
              <SettingsIcon className={bigMode ? 'w-5 h-5' : 'w-4 h-4'} />
              Preferences
            </button>
            <button
              onClick={() => setActiveTab('notifications')}
              className={`flex items-center gap-2 rounded-lg transition-colors ${
                bigMode ? 'px-4 py-2.5 text-base' : 'px-3 py-2 text-sm'
              } ${
                activeTab === 'notifications'
                  ? 'bg-primary text-white shadow-sm'
                  : 'text-fc-text-muted hover:text-fc-text hover:bg-fc-surface'
              }`}
            >
              <Bell className={bigMode ? 'w-5 h-5' : 'w-4 h-4'} />
              Notifications
            </button>
          </div>
        )}

        {/* Preferences Tab */}
        {activeTab === 'preferences' && (
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
                    ${bigMode ? 'bg-primary' : 'bg-red-500'}
                  `}
                >
                  <span
                    className={`
                      absolute left-0 top-1 w-6 h-6 bg-white rounded-full transition-transform
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

            {/* Calendar Feed — family admins */}
            {isFamilyAdmin && (
              <div className="bg-fc-surface border border-fc-border rounded-2xl p-6">
                <div className="flex items-center gap-4 mb-4">
                  <div className="w-12 h-12 bg-primary/10 rounded-xl flex items-center justify-center">
                    <Calendar className="w-6 h-6 text-primary" />
                  </div>
                  <div>
                    <h2
                      className={`
                        font-semibold text-fc-text
                        ${bigMode ? 'text-xl' : 'text-lg'}
                      `}
                    >
                      Calendar Feed
                    </h2>
                    <p className={`text-fc-text-muted ${bigMode ? 'text-base' : 'text-sm'}`}>
                      Subscribe to family events in your calendar app
                    </p>
                  </div>
                </div>

                {!feedUrl ? (
                  <button
                    onClick={loadFeedUrl}
                    disabled={feedLoading}
                    className={`
                      flex items-center gap-2 bg-primary/10 text-primary rounded-xl
                      hover:bg-primary/20 transition-colors
                      ${bigMode ? 'px-5 py-3 text-lg' : 'px-4 py-2'}
                    `}
                  >
                    {feedLoading ? (
                      <Loader2 className="w-4 h-4 animate-spin" />
                    ) : (
                      <Calendar className={bigMode ? 'w-5 h-5' : 'w-4 h-4'} />
                    )}
                    Show Feed URL
                  </button>
                ) : (
                  <div className="space-y-3">
                    <div className="flex items-center gap-2">
                      <input
                        type="text"
                        readOnly
                        value={feedUrl}
                        className={`
                          flex-1 bg-fc-bg border border-fc-border rounded-lg text-fc-text-muted
                          font-mono select-all
                          ${bigMode ? 'px-3 py-2 text-sm' : 'px-2.5 py-1.5 text-xs'}
                        `}
                      />
                      <button
                        onClick={handleCopyFeed}
                        className="p-2 text-fc-text-muted hover:text-primary transition-colors"
                        title="Copy URL"
                      >
                        {feedCopied ? (
                          <Check className="w-5 h-5 text-success" />
                        ) : (
                          <Copy className="w-5 h-5" />
                        )}
                      </button>
                    </div>
                    <div className="flex items-center gap-3">
                      <button
                        onClick={handleRegenerateFeed}
                        disabled={feedRegenerating}
                        className={`
                          flex items-center gap-2 text-fc-text-muted hover:text-error transition-colors
                          ${bigMode ? 'text-base' : 'text-sm'}
                        `}
                      >
                        <RefreshCw className={`w-4 h-4 ${feedRegenerating ? 'animate-spin' : ''}`} />
                        Regenerate URL
                      </button>
                      <span className={`text-fc-text-muted ${bigMode ? 'text-sm' : 'text-xs'}`}>
                        (old URL will stop working)
                      </span>
                    </div>
                    <p className={`text-fc-text-muted ${bigMode ? 'text-sm' : 'text-xs'}`}>
                      Add this URL to Google Calendar, Apple Calendar, or any app that supports iCal feeds.
                    </p>
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* Notifications Tab — super admin only */}
        {activeTab === 'notifications' && isSuperAdmin && <NotificationsTab />}
      </div>
    </div>
  )
}
