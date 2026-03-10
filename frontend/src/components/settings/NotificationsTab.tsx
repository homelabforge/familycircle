import { useState, useEffect, useCallback } from 'react'
import { Bell, Radio, Send, Hash, MessageSquare, AtSign, Mail, Loader2, AlertCircle, CheckCircle } from 'lucide-react'
import { notificationsApi } from '@/lib/api'
import { useBigMode } from '@/contexts/BigModeContext'
import { NtfyConfig } from './notifications/NtfyConfig'
import { GotifyConfig } from './notifications/GotifyConfig'
import { PushoverConfig } from './notifications/PushoverConfig'
import { SlackConfig } from './notifications/SlackConfig'
import { DiscordConfig } from './notifications/DiscordConfig'
import { TelegramConfig } from './notifications/TelegramConfig'
import { EmailConfig } from './notifications/EmailConfig'
import { EventToggles } from './notifications/EventToggles'

type ServiceTab = 'ntfy' | 'gotify' | 'pushover' | 'slack' | 'discord' | 'telegram' | 'email'

const serviceTabs: { id: ServiceTab; label: string; icon: React.ElementType; enabledKey: string }[] = [
  { id: 'ntfy', label: 'ntfy', icon: Bell, enabledKey: 'ntfy_enabled' },
  { id: 'gotify', label: 'Gotify', icon: Radio, enabledKey: 'gotify_enabled' },
  { id: 'pushover', label: 'Pushover', icon: Send, enabledKey: 'pushover_enabled' },
  { id: 'slack', label: 'Slack', icon: Hash, enabledKey: 'slack_enabled' },
  { id: 'discord', label: 'Discord', icon: MessageSquare, enabledKey: 'discord_enabled' },
  { id: 'telegram', label: 'Telegram', icon: AtSign, enabledKey: 'telegram_enabled' },
  { id: 'email', label: 'Email', icon: Mail, enabledKey: 'notification_email_enabled' },
]

export default function NotificationsTab() {
  const { bigMode } = useBigMode()
  const [settings, setSettings] = useState<Record<string, string>>({})
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [testing, setTesting] = useState(false)
  const [activeService, setActiveService] = useState<ServiceTab>('ntfy')
  const [toast, setToast] = useState<{ type: 'success' | 'error'; message: string } | null>(null)
  const [dirty, setDirty] = useState(false)

  useEffect(() => {
    loadSettings()
  }, [])

  // Auto-dismiss toast
  useEffect(() => {
    if (toast) {
      const timer = setTimeout(() => setToast(null), 4000)
      return () => clearTimeout(timer)
    }
  }, [toast])

  const loadSettings = async () => {
    try {
      const resp = await notificationsApi.getSettings()
      const flat: Record<string, string> = {}
      for (const [k, v] of Object.entries(resp.settings)) {
        flat[k] = String(v)
      }
      setSettings(flat)
    } catch (err) {
      console.error('Failed to load notification settings:', err)
      setToast({ type: 'error', message: 'Failed to load notification settings' })
    } finally {
      setLoading(false)
    }
  }

  const handleTextChange = useCallback((key: string, value: string) => {
    setSettings((prev) => ({ ...prev, [key]: value }))
    setDirty(true)
  }, [])

  const handleToggle = useCallback((key: string, value: boolean) => {
    setSettings((prev) => ({ ...prev, [key]: value ? 'true' : 'false' }))
    setDirty(true)
  }, [])

  const handleSave = async () => {
    setSaving(true)
    try {
      // Filter out masked values (********) so we don't overwrite secrets with the mask
      const payload: Record<string, string> = {}
      for (const [k, v] of Object.entries(settings)) {
        if (v !== '********' && k !== 'smtp_configured') {
          payload[k] = v
        }
      }
      await notificationsApi.updateSettings(payload)
      setToast({ type: 'success', message: 'Notification settings saved' })
      setDirty(false)
      // Reload to get fresh masked values
      await loadSettings()
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to save settings'
      setToast({ type: 'error', message })
    } finally {
      setSaving(false)
    }
  }

  const handleTest = async (service: string) => {
    // Save first if dirty
    if (dirty) {
      await handleSave()
    }
    setTesting(true)
    try {
      const resp = await notificationsApi.testService(service)
      setToast({
        type: resp.success ? 'success' : 'error',
        message: resp.message,
      })
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Test failed'
      setToast({ type: 'error', message })
    } finally {
      setTesting(false)
    }
  }

  const hasEnabledService = serviceTabs.some((s) => settings[s.enabledKey] === 'true')

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="w-6 h-6 animate-spin text-fc-text-muted" />
      </div>
    )
  }

  const serviceConfigProps = {
    settings,
    onTextChange: handleTextChange,
    onToggle: handleToggle,
    testing,
    saving,
  }

  return (
    <div className="space-y-6">
      {/* Toast */}
      {toast && (
        <div
          className={`flex items-center gap-2 p-3 rounded-lg border ${
            toast.type === 'success'
              ? 'bg-green-500/10 border-green-500/30 text-green-700 dark:text-green-400'
              : 'bg-red-500/10 border-red-500/30 text-red-700 dark:text-red-400'
          }`}
        >
          {toast.type === 'success' ? (
            <CheckCircle className="w-4 h-4 shrink-0" />
          ) : (
            <AlertCircle className="w-4 h-4 shrink-0" />
          )}
          <span className="text-sm">{toast.message}</span>
        </div>
      )}

      {/* Service Config Card */}
      <div className="bg-fc-surface border border-fc-border rounded-2xl p-6">
        <h2 className={`font-semibold text-fc-text mb-4 ${bigMode ? 'text-xl' : 'text-lg'}`}>
          Notification Services
        </h2>

        {/* Service sub-tabs */}
        <div className="flex flex-wrap gap-2 mb-6 p-1 bg-fc-bg/50 rounded-lg border border-fc-border">
          {serviceTabs.map((tab) => {
            const Icon = tab.icon
            const isActive = activeService === tab.id
            const isEnabled = settings[tab.enabledKey] === 'true'

            return (
              <button
                key={tab.id}
                onClick={() => setActiveService(tab.id)}
                className={`flex items-center gap-2 px-3 py-2 rounded-md transition-colors ${
                  isActive
                    ? 'bg-primary/20 text-primary'
                    : 'text-fc-text-muted hover:text-fc-text hover:bg-fc-surface'
                }`}
              >
                <Icon className="w-4 h-4" />
                <span className="text-sm">{tab.label}</span>
                {isEnabled && <span className="w-2 h-2 rounded-full bg-green-500" />}
              </button>
            )
          })}
        </div>

        {/* Active service config */}
        {activeService === 'ntfy' && <NtfyConfig {...serviceConfigProps} onTest={() => handleTest('ntfy')} />}
        {activeService === 'gotify' && <GotifyConfig {...serviceConfigProps} onTest={() => handleTest('gotify')} />}
        {activeService === 'pushover' && (
          <PushoverConfig {...serviceConfigProps} onTest={() => handleTest('pushover')} />
        )}
        {activeService === 'slack' && <SlackConfig {...serviceConfigProps} onTest={() => handleTest('slack')} />}
        {activeService === 'discord' && (
          <DiscordConfig {...serviceConfigProps} onTest={() => handleTest('discord')} />
        )}
        {activeService === 'telegram' && (
          <TelegramConfig {...serviceConfigProps} onTest={() => handleTest('telegram')} />
        )}
        {activeService === 'email' && <EmailConfig {...serviceConfigProps} onTest={() => handleTest('email')} />}
      </div>

      {/* Event Toggles */}
      <EventToggles
        settings={settings}
        onToggle={handleToggle}
        onTextChange={handleTextChange}
        saving={saving}
        hasEnabledService={hasEnabledService}
      />

      {/* Save Button */}
      {dirty && (
        <div className="sticky bottom-4 flex justify-end">
          <button
            onClick={handleSave}
            disabled={saving}
            className={`flex items-center gap-2 bg-primary text-white rounded-xl shadow-lg hover:bg-primary/90 transition-colors disabled:opacity-50 ${
              bigMode ? 'px-6 py-3 text-lg' : 'px-5 py-2.5'
            }`}
          >
            {saving && <Loader2 className="w-4 h-4 animate-spin" />}
            Save Changes
          </button>
        </div>
      )}
    </div>
  )
}
