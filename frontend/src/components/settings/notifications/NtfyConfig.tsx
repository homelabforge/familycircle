import { Bell, Send, Info } from 'lucide-react'

interface NtfyConfigProps {
  settings: Record<string, string>
  onTextChange: (key: string, value: string) => void
  onToggle: (key: string, value: boolean) => void
  onTest: () => void
  testing: boolean
  saving: boolean
}

export function NtfyConfig({ settings, onTextChange, onToggle, onTest, testing, saving }: NtfyConfigProps) {
  const isEnabled = settings.ntfy_enabled === 'true'
  const hasRequired = Boolean(settings.ntfy_server && settings.ntfy_topic)

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3 mb-2">
        <Bell className="w-5 h-5 text-primary" />
        <div>
          <h3 className="text-base font-semibold text-fc-text">ntfy</h3>
          <p className="text-xs text-fc-text-muted">Self-hosted or ntfy.sh push notifications</p>
        </div>
      </div>

      <label className="flex items-center cursor-pointer">
        <input
          type="checkbox"
          checked={isEnabled}
          onChange={(e) => onToggle('ntfy_enabled', e.target.checked)}
          disabled={saving}
          className="w-4 h-4 text-primary bg-fc-bg border-fc-border rounded focus:ring-primary focus:ring-2 disabled:opacity-50"
        />
        <span className="ml-2 text-sm text-fc-text font-medium">Enable ntfy notifications</span>
      </label>

      <div>
        <label htmlFor="ntfy_server" className="block text-sm font-medium text-fc-text mb-1">
          Server URL
        </label>
        <input
          type="url"
          id="ntfy_server"
          value={settings.ntfy_server ?? ''}
          onChange={(e) => onTextChange('ntfy_server', e.target.value)}
          placeholder="https://ntfy.sh"
          disabled={saving || !isEnabled}
          className="w-full px-3 py-2 bg-fc-bg border border-fc-border rounded-lg text-fc-text placeholder-fc-text-muted focus:outline-none focus:ring-2 focus:ring-primary disabled:opacity-50"
        />
      </div>

      <div>
        <label htmlFor="ntfy_topic" className="block text-sm font-medium text-fc-text mb-1">
          Topic Name
        </label>
        <input
          type="text"
          id="ntfy_topic"
          value={settings.ntfy_topic ?? 'familycircle'}
          onChange={(e) => onTextChange('ntfy_topic', e.target.value)}
          placeholder="familycircle"
          disabled={saving || !isEnabled}
          className="w-full px-3 py-2 bg-fc-bg border border-fc-border rounded-lg text-fc-text placeholder-fc-text-muted focus:outline-none focus:ring-2 focus:ring-primary disabled:opacity-50"
        />
        <p className="mt-1 text-xs text-fc-text-muted">
          Subscribe to this topic in your ntfy app to receive notifications
        </p>
      </div>

      <div>
        <label htmlFor="ntfy_token" className="block text-sm font-medium text-fc-text mb-1">
          API Token <span className="text-fc-text-muted">(optional)</span>
        </label>
        <input
          type="password"
          id="ntfy_token"
          value={settings.ntfy_token ?? ''}
          onChange={(e) => onTextChange('ntfy_token', e.target.value)}
          placeholder="tk_..."
          disabled={saving || !isEnabled}
          className="w-full px-3 py-2 bg-fc-bg border border-fc-border rounded-lg text-fc-text placeholder-fc-text-muted focus:outline-none focus:ring-2 focus:ring-primary disabled:opacity-50"
        />
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
            Use unique, hard-to-guess topic names. ntfy.sh topics are public by default unless you enable authentication.
          </p>
        </div>
      </div>
    </div>
  )
}
