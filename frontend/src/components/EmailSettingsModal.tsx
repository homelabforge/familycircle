import { useEffect, useState } from 'react'
import { X, Loader2, Mail, Eye, EyeOff } from 'lucide-react'
import { toast } from 'sonner'
import { useBigMode } from '@/contexts/BigModeContext'
import { settingsApi } from '@/lib/api'

interface EmailSettingsModalProps {
  isOpen: boolean
  onClose: () => void
}

export default function EmailSettingsModal({ isOpen, onClose }: EmailSettingsModalProps) {
  const { bigMode } = useBigMode()
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [showPassword, setShowPassword] = useState(false)

  // SMTP form state
  const [smtpHost, setSmtpHost] = useState('')
  const [smtpPort, setSmtpPort] = useState('587')
  const [smtpUsername, setSmtpUsername] = useState('')
  const [smtpPassword, setSmtpPassword] = useState('')
  const [smtpFromEmail, setSmtpFromEmail] = useState('')
  const [smtpFromName, setSmtpFromName] = useState('')
  const [smtpUseTls, setSmtpUseTls] = useState(true)
  const [smtpConfigured, setSmtpConfigured] = useState(false)

  useEffect(() => {
    if (isOpen) {
      loadSettings()
    }
  }, [isOpen])

  const loadSettings = async () => {
    try {
      setLoading(true)
      const { settings } = await settingsApi.getSettings()

      setSmtpHost(settings.smtp_host || '')
      setSmtpPort(settings.smtp_port || '587')
      setSmtpUsername(settings.smtp_username || '')
      setSmtpPassword(settings.smtp_password || '')
      setSmtpFromEmail(settings.smtp_from_email || '')
      setSmtpFromName(settings.smtp_from_name || '')
      setSmtpUseTls(settings.smtp_use_tls !== 'false')
      setSmtpConfigured(settings.smtp_configured || false)
    } catch (err) {
      toast.error('Failed to load email settings')
    } finally {
      setLoading(false)
    }
  }

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      setSaving(true)
      await settingsApi.updateGlobalSettings({
        smtp_host: smtpHost,
        smtp_port: smtpPort,
        smtp_username: smtpUsername,
        smtp_password: smtpPassword,
        smtp_from_email: smtpFromEmail,
        smtp_from_name: smtpFromName,
        smtp_use_tls: smtpUseTls ? 'true' : 'false',
      })
      toast.success('Email settings saved')
      // Reload to get updated smtp_configured status
      await loadSettings()
    } catch (err) {
      toast.error('Failed to save email settings')
    } finally {
      setSaving(false)
    }
  }

  const handleClose = () => {
    setShowPassword(false)
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
          w-full max-w-lg mx-4 shadow-xl max-h-[90vh] overflow-y-auto
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
            <Mail className={`text-primary ${bigMode ? 'w-7 h-7' : 'w-6 h-6'}`} />
          </div>
          <div>
            <h2 className={`font-bold text-fc-text ${bigMode ? 'text-2xl' : 'text-xl'}`}>
              Email Settings
            </h2>
            {smtpConfigured && (
              <span className="flex items-center gap-1.5 text-success text-sm">
                <span className="w-2 h-2 bg-success rounded-full" />
                Configured
              </span>
            )}
          </div>
        </div>

        {loading ? (
          <div className="flex justify-center py-12">
            <Loader2 className="w-8 h-8 animate-spin text-primary" />
          </div>
        ) : (
          <form onSubmit={handleSave} className="space-y-4">
            <p className={`text-fc-text-muted ${bigMode ? 'text-base' : 'text-sm'}`}>
              Configure SMTP for sending magic links and invitations.
            </p>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className={`block text-fc-text mb-2 ${bigMode ? 'text-base' : 'text-sm'}`}>
                  SMTP Host
                </label>
                <input
                  type="text"
                  value={smtpHost}
                  onChange={(e) => setSmtpHost(e.target.value)}
                  placeholder="smtp.example.com"
                  className={`
                    w-full bg-fc-bg border border-fc-border rounded-xl
                    text-fc-text placeholder:text-fc-text-muted
                    focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent
                    ${bigMode ? 'px-4 py-3 text-base' : 'px-3 py-2 text-sm'}
                  `}
                />
              </div>
              <div>
                <label className={`block text-fc-text mb-2 ${bigMode ? 'text-base' : 'text-sm'}`}>
                  Port
                </label>
                <input
                  type="number"
                  value={smtpPort}
                  onChange={(e) => setSmtpPort(e.target.value)}
                  placeholder="587"
                  className={`
                    w-full bg-fc-bg border border-fc-border rounded-xl
                    text-fc-text placeholder:text-fc-text-muted
                    focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent
                    ${bigMode ? 'px-4 py-3 text-base' : 'px-3 py-2 text-sm'}
                  `}
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className={`block text-fc-text mb-2 ${bigMode ? 'text-base' : 'text-sm'}`}>
                  Username
                </label>
                <input
                  type="text"
                  value={smtpUsername}
                  onChange={(e) => setSmtpUsername(e.target.value)}
                  placeholder="user@example.com"
                  className={`
                    w-full bg-fc-bg border border-fc-border rounded-xl
                    text-fc-text placeholder:text-fc-text-muted
                    focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent
                    ${bigMode ? 'px-4 py-3 text-base' : 'px-3 py-2 text-sm'}
                  `}
                />
              </div>
              <div>
                <label className={`block text-fc-text mb-2 ${bigMode ? 'text-base' : 'text-sm'}`}>
                  Password
                </label>
                <div className="relative">
                  <input
                    type={showPassword ? 'text' : 'password'}
                    value={smtpPassword}
                    onChange={(e) => setSmtpPassword(e.target.value)}
                    placeholder="••••••••"
                    className={`
                      w-full bg-fc-bg border border-fc-border rounded-xl
                      text-fc-text placeholder:text-fc-text-muted
                      focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent
                      ${bigMode ? 'px-4 py-3 text-base pr-10' : 'px-3 py-2 text-sm pr-9'}
                    `}
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-fc-text-muted hover:text-fc-text"
                  >
                    {showPassword ? (
                      <EyeOff className="w-4 h-4" />
                    ) : (
                      <Eye className="w-4 h-4" />
                    )}
                  </button>
                </div>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className={`block text-fc-text mb-2 ${bigMode ? 'text-base' : 'text-sm'}`}>
                  From Email
                </label>
                <input
                  type="email"
                  value={smtpFromEmail}
                  onChange={(e) => setSmtpFromEmail(e.target.value)}
                  placeholder="noreply@example.com"
                  className={`
                    w-full bg-fc-bg border border-fc-border rounded-xl
                    text-fc-text placeholder:text-fc-text-muted
                    focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent
                    ${bigMode ? 'px-4 py-3 text-base' : 'px-3 py-2 text-sm'}
                  `}
                />
              </div>
              <div>
                <label className={`block text-fc-text mb-2 ${bigMode ? 'text-base' : 'text-sm'}`}>
                  From Name
                </label>
                <input
                  type="text"
                  value={smtpFromName}
                  onChange={(e) => setSmtpFromName(e.target.value)}
                  placeholder="FamilyCircle"
                  className={`
                    w-full bg-fc-bg border border-fc-border rounded-xl
                    text-fc-text placeholder:text-fc-text-muted
                    focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent
                    ${bigMode ? 'px-4 py-3 text-base' : 'px-3 py-2 text-sm'}
                  `}
                />
              </div>
            </div>

            <div className="flex items-center gap-3">
              <input
                type="checkbox"
                id="smtp-tls-modal"
                checked={smtpUseTls}
                onChange={(e) => setSmtpUseTls(e.target.checked)}
                className="w-4 h-4 rounded border-fc-border text-primary focus:ring-primary"
              />
              <label htmlFor="smtp-tls-modal" className={`text-fc-text ${bigMode ? 'text-base' : 'text-sm'}`}>
                Use TLS/STARTTLS (recommended)
              </label>
            </div>

            <div className="pt-4 border-t border-fc-border flex gap-3">
              <button
                type="button"
                onClick={handleClose}
                className={`
                  flex-1 border border-fc-border rounded-xl
                  text-fc-text hover:bg-fc-bg transition-colors
                  ${bigMode ? 'px-6 py-3 text-base' : 'px-4 py-2.5 text-sm'}
                `}
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={saving}
                className={`
                  flex-1 flex items-center justify-center gap-2
                  bg-primary text-white rounded-xl
                  hover:bg-primary-hover transition-colors
                  disabled:opacity-50
                  ${bigMode ? 'px-6 py-3 text-base' : 'px-4 py-2.5 text-sm'}
                `}
              >
                {saving && <Loader2 className="w-4 h-4 animate-spin" />}
                Save Settings
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  )
}
