import { Mail, Send, Info } from 'lucide-react'

interface EmailConfigProps {
  settings: Record<string, string>
  onTextChange: (key: string, value: string) => void
  onToggle: (key: string, value: boolean) => void
  onTest: () => void
  testing: boolean
  saving: boolean
}

export function EmailConfig({ settings, onTextChange, onToggle, onTest, testing, saving }: EmailConfigProps) {
  const isEnabled = settings.notification_email_enabled === 'true'
  const smtpConfigured = settings.smtp_configured === 'true'
  const hasRequired = smtpConfigured && Boolean(settings.notification_email_to)

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3 mb-2">
        <Mail className="w-5 h-5 text-primary" />
        <div>
          <h3 className="text-base font-semibold text-fc-text">Email</h3>
          <p className="text-xs text-fc-text-muted">Send notifications via email (uses existing SMTP config)</p>
        </div>
      </div>

      {!smtpConfigured && (
        <div className="p-3 bg-amber-500/10 border border-amber-500/30 rounded-lg">
          <p className="text-sm text-amber-600 dark:text-amber-400">
            SMTP is not configured. Set up SMTP in App Settings before enabling email notifications.
          </p>
        </div>
      )}

      <label className="flex items-center cursor-pointer">
        <input
          type="checkbox"
          checked={isEnabled}
          onChange={(e) => onToggle('notification_email_enabled', e.target.checked)}
          disabled={saving || !smtpConfigured}
          className="w-4 h-4 text-primary bg-fc-bg border-fc-border rounded focus:ring-primary focus:ring-2 disabled:opacity-50"
        />
        <span className="ml-2 text-sm text-fc-text font-medium">Enable email notifications</span>
      </label>

      <div>
        <label htmlFor="notification_email_to" className="block text-sm font-medium text-fc-text mb-1">
          Recipient Address
        </label>
        <input
          type="email"
          id="notification_email_to"
          value={settings.notification_email_to ?? ''}
          onChange={(e) => onTextChange('notification_email_to', e.target.value)}
          placeholder="you@example.com"
          disabled={saving || !isEnabled || !smtpConfigured}
          className="w-full px-3 py-2 bg-fc-bg border border-fc-border rounded-lg text-fc-text placeholder-fc-text-muted focus:outline-none focus:ring-2 focus:ring-primary disabled:opacity-50"
        />
        <p className="mt-1 text-xs text-fc-text-muted">
          Notification emails will be sent to this address
        </p>
      </div>

      <button
        onClick={onTest}
        disabled={testing || saving || !isEnabled || !hasRequired}
        className="flex items-center gap-2 px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
      >
        <Send size={16} />
        {testing ? 'Sending...' : 'Test Connection'}
      </button>

      <div className="p-3 bg-fc-bg/50 border border-fc-border rounded-lg">
        <div className="flex items-start gap-2">
          <Info className="w-4 h-4 text-fc-text-muted mt-0.5 shrink-0" />
          <p className="text-xs text-fc-text-muted">
            Email notifications reuse the SMTP server configured in App Settings. Only the recipient address needs to be set here.
          </p>
        </div>
      </div>
    </div>
  )
}
