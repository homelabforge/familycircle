import { useEffect, useState } from 'react'
import { Settings, Key, RefreshCw, Loader2, Copy, Check, Palette, Trash2, X } from 'lucide-react'
import { toast } from 'sonner'
import { useBigMode } from '@/contexts/BigModeContext'
import { useAuth } from '@/contexts/AuthContext'
import { settingsApi, type Settings as AppSettings } from '@/lib/api'

interface AppSettingsModalProps {
  isOpen: boolean
  onClose: () => void
}

export default function AppSettingsModal({ isOpen, onClose }: AppSettingsModalProps) {
  const { bigMode } = useBigMode()
  const { isSuperAdmin } = useAuth()
  const [_settings, setSettings] = useState<AppSettings | null>(null)
  const [familyCode, setFamilyCode] = useState('')
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [regenerating, setRegenerating] = useState(false)
  const [copied, setCopied] = useState(false)

  // Form state
  const [appName, setAppName] = useState('')
  const [themeColor, setThemeColor] = useState('#4f46e5')
  const [magicLinkExpiry, setMagicLinkExpiry] = useState('1')
  const [cancelledEventRetention, setCancelledEventRetention] = useState('7')

  useEffect(() => {
    if (isOpen) {
      loadData()
    }
  }, [isOpen])

  const loadData = async () => {
    try {
      setLoading(true)
      const [settingsRes, codeRes] = await Promise.all([
        settingsApi.getSettings(),
        settingsApi.getFamilyCode(),
      ])
      setSettings(settingsRes.settings)
      setFamilyCode(codeRes.code)

      // Set form values
      setAppName(settingsRes.settings.app_name || 'FamilyCircle')
      setThemeColor(settingsRes.settings.theme_color || '#4f46e5')
      setMagicLinkExpiry(settingsRes.settings.magic_link_expiry_days || '90')
      setCancelledEventRetention(settingsRes.settings.cancelled_event_retention_days || '7')
    } catch (err) {
      toast.error('Failed to load settings')
    } finally {
      setLoading(false)
    }
  }

  const handleSaveSettings = async () => {
    try {
      setSaving(true)
      // Save global settings (app name, magic link expiry, cancelled event retention) - super admin only
      if (isSuperAdmin) {
        await settingsApi.updateGlobalSettings({
          app_name: appName,
          magic_link_expiry_days: magicLinkExpiry,
          cancelled_event_retention_days: cancelledEventRetention,
        })
      }
      // Save family-specific settings (theme color) separately
      await settingsApi.updateFamilySettings({
        theme_color: themeColor,
      })
      toast.success('Settings saved')
    } catch (err) {
      toast.error('Failed to save settings')
    } finally {
      setSaving(false)
    }
  }

  const handleRegenerateCode = async () => {
    if (!confirm('This will invalidate the current join code. Are you sure?')) {
      return
    }

    try {
      setRegenerating(true)
      const res = await settingsApi.regenerateFamilyCode()
      setFamilyCode(res.code)
      toast.success('New family code generated')
    } catch (err) {
      toast.error('Failed to regenerate code')
    } finally {
      setRegenerating(false)
    }
  }

  const handleCopyCode = async () => {
    try {
      // Try modern clipboard API first
      if (navigator.clipboard && window.isSecureContext) {
        await navigator.clipboard.writeText(familyCode)
      } else {
        // Fallback for non-HTTPS contexts
        const textArea = document.createElement('textarea')
        textArea.value = familyCode
        textArea.style.position = 'fixed'
        textArea.style.left = '-999999px'
        textArea.style.top = '-999999px'
        document.body.appendChild(textArea)
        textArea.focus()
        textArea.select()
        document.execCommand('copy')
        document.body.removeChild(textArea)
      }
      setCopied(true)
      toast.success('Code copied to clipboard')
      setTimeout(() => setCopied(false), 2000)
    } catch (err) {
      toast.error('Failed to copy code')
    }
  }

  const handleClose = () => {
    onClose()
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/50 backdrop-blur-sm"
        onClick={handleClose}
      />

      {/* Modal */}
      <div
        className={`
          relative bg-fc-surface border border-fc-border rounded-2xl
          w-full max-w-2xl mx-4 shadow-xl max-h-[90vh] overflow-hidden flex flex-col
          ${bigMode ? 'p-8' : 'p-6'}
        `}
      >
        {/* Close button */}
        <button
          onClick={handleClose}
          className="absolute top-4 right-4 p-2 text-fc-text-muted hover:text-fc-text transition-colors"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Header */}
        <div className="flex items-center gap-3 mb-6">
          <div className="p-2 bg-primary/10 rounded-xl">
            <Settings className={`text-primary ${bigMode ? 'w-7 h-7' : 'w-6 h-6'}`} />
          </div>
          <h2 className={`font-bold text-fc-text ${bigMode ? 'text-2xl' : 'text-xl'}`}>
            App Settings
          </h2>
        </div>

        {loading ? (
          <div className="flex justify-center py-12">
            <Loader2 className="w-8 h-8 animate-spin text-primary" />
          </div>
        ) : (
          <div className="overflow-y-auto flex-1 space-y-4">
            {/* App Customization */}
            <div className="bg-fc-bg rounded-xl p-4">
              <div className="flex items-center gap-2 mb-3">
                <Palette className="w-5 h-5 text-primary" />
                <h3 className={`font-medium text-fc-text ${bigMode ? 'text-base' : 'text-sm'}`}>
                  App Customization
                </h3>
              </div>
              <div className="space-y-3">
                <div>
                  <label className={`block text-fc-text mb-1 ${bigMode ? 'text-sm' : 'text-xs'}`}>
                    App Name
                  </label>
                  <input
                    type="text"
                    value={appName}
                    onChange={(e) => setAppName(e.target.value)}
                    placeholder="e.g., The Smith Family"
                    className={`
                      w-full bg-fc-surface border border-fc-border rounded-lg
                      text-fc-text placeholder:text-fc-text-muted
                      focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent
                      ${bigMode ? 'px-4 py-3 text-base' : 'px-3 py-2 text-sm'}
                    `}
                  />
                </div>
                <div>
                  <label className={`block text-fc-text mb-1 ${bigMode ? 'text-sm' : 'text-xs'}`}>
                    Theme Color
                  </label>
                  <div className="flex items-center gap-3">
                    <input
                      type="color"
                      value={themeColor}
                      onChange={(e) => setThemeColor(e.target.value)}
                      className="w-12 h-10 rounded-lg cursor-pointer border border-fc-border"
                    />
                    <input
                      type="text"
                      value={themeColor}
                      onChange={(e) => setThemeColor(e.target.value)}
                      className={`
                        flex-1 bg-fc-surface border border-fc-border rounded-lg
                        text-fc-text font-mono
                        focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent
                        ${bigMode ? 'px-4 py-3 text-base' : 'px-3 py-2 text-sm'}
                      `}
                    />
                  </div>
                </div>
              </div>
            </div>

            {/* Family Join Code */}
            <div className="bg-fc-bg rounded-xl p-4">
              <div className="flex items-center gap-2 mb-3">
                <RefreshCw className="w-5 h-5 text-warning" />
                <h3 className={`font-medium text-fc-text ${bigMode ? 'text-base' : 'text-sm'}`}>
                  Family Join Code
                </h3>
              </div>
              <p className={`text-fc-text-muted mb-3 ${bigMode ? 'text-sm' : 'text-xs'}`}>
                Current code for new members to join.
              </p>
              <div className="flex items-center gap-3 mb-3">
                <code
                  className={`
                    bg-fc-surface border border-fc-border rounded-lg px-4 py-2
                    font-mono font-bold text-primary
                    ${bigMode ? 'text-xl' : 'text-lg'}
                  `}
                >
                  {familyCode}
                </code>
                <button
                  onClick={handleCopyCode}
                  className="p-2 text-fc-text-muted hover:text-primary transition-colors"
                  title="Copy code"
                >
                  {copied ? (
                    <Check className={bigMode ? 'w-5 h-5' : 'w-4 h-4'} />
                  ) : (
                    <Copy className={bigMode ? 'w-5 h-5' : 'w-4 h-4'} />
                  )}
                </button>
              </div>
              <button
                onClick={handleRegenerateCode}
                disabled={regenerating}
                className={`
                  flex items-center gap-2
                  text-warning hover:text-warning/80 transition-colors
                  disabled:opacity-50
                  ${bigMode ? 'text-sm' : 'text-xs'}
                `}
              >
                {regenerating ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <RefreshCw className="w-4 h-4" />
                )}
                Generate New Code
              </button>
              <p className={`text-fc-text-muted mt-1 ${bigMode ? 'text-xs' : 'text-xs'}`}>
                The old code will stop working immediately.
              </p>
            </div>

            {/* Super Admin Settings */}
            {isSuperAdmin && (
              <>
                {/* Magic Link Settings */}
                <div className="bg-fc-bg rounded-xl p-4">
                  <div className="flex items-center gap-2 mb-3">
                    <Key className="w-5 h-5 text-primary" />
                    <h3 className={`font-medium text-fc-text ${bigMode ? 'text-base' : 'text-sm'}`}>
                      Magic Link Settings
                    </h3>
                  </div>
                  <div>
                    <label className={`block text-fc-text mb-1 ${bigMode ? 'text-sm' : 'text-xs'}`}>
                      Link Expiry (days)
                    </label>
                    <input
                      type="number"
                      value={magicLinkExpiry}
                      onChange={(e) => setMagicLinkExpiry(e.target.value)}
                      min="1"
                      max="30"
                      className={`
                        w-full bg-fc-surface border border-fc-border rounded-lg
                        text-fc-text placeholder:text-fc-text-muted
                        focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent
                        ${bigMode ? 'px-4 py-3 text-base' : 'px-3 py-2 text-sm'}
                      `}
                    />
                    <p className={`text-fc-text-muted mt-1 ${bigMode ? 'text-xs' : 'text-xs'}`}>
                      Default: 1 day. Maximum 30 days.
                    </p>
                  </div>
                </div>

                {/* Cancelled Event Retention */}
                <div className="bg-fc-bg rounded-xl p-4">
                  <div className="flex items-center gap-2 mb-3">
                    <Trash2 className="w-5 h-5 text-error" />
                    <h3 className={`font-medium text-fc-text ${bigMode ? 'text-base' : 'text-sm'}`}>
                      Cancelled Event Cleanup
                    </h3>
                  </div>
                  <div>
                    <label className={`block text-fc-text mb-1 ${bigMode ? 'text-sm' : 'text-xs'}`}>
                      Retention (days)
                    </label>
                    <input
                      type="number"
                      value={cancelledEventRetention}
                      onChange={(e) => setCancelledEventRetention(e.target.value)}
                      min="1"
                      max="365"
                      className={`
                        w-full bg-fc-surface border border-fc-border rounded-lg
                        text-fc-text placeholder:text-fc-text-muted
                        focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent
                        ${bigMode ? 'px-4 py-3 text-base' : 'px-3 py-2 text-sm'}
                      `}
                    />
                    <p className={`text-fc-text-muted mt-1 ${bigMode ? 'text-xs' : 'text-xs'}`}>
                      Default: 7 days. Cancelled events are automatically hidden after this period.
                    </p>
                  </div>
                </div>
              </>
            )}

            {/* Save Button */}
            <button
              onClick={handleSaveSettings}
              disabled={saving}
              className={`
                w-full flex items-center justify-center gap-2
                bg-primary text-white rounded-xl
                hover:bg-primary-hover transition-colors
                disabled:opacity-50
                ${bigMode ? 'px-4 py-3 text-base' : 'px-3 py-2.5 text-sm'}
              `}
            >
              {saving && <Loader2 className="w-4 h-4 animate-spin" />}
              Save Settings
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
