import { Send, SendHorizonal, Info } from 'lucide-react'

interface PushoverConfigProps {
  settings: Record<string, string>
  onTextChange: (key: string, value: string) => void
  onToggle: (key: string, value: boolean) => void
  onTest: () => void
  testing: boolean
  saving: boolean
}

export function PushoverConfig({ settings, onTextChange, onToggle, onTest, testing, saving }: PushoverConfigProps) {
  const isEnabled = settings.pushover_enabled === 'true'
  const hasRequired = Boolean(settings.pushover_user_key && settings.pushover_api_token)

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3 mb-2">
        <SendHorizonal className="w-5 h-5 text-primary" />
        <div>
          <h3 className="text-base font-semibold text-fc-text">Pushover</h3>
          <p className="text-xs text-fc-text-muted">Cross-platform push notifications</p>
        </div>
      </div>

      <label className="flex items-center cursor-pointer">
        <input
          type="checkbox"
          checked={isEnabled}
          onChange={(e) => onToggle('pushover_enabled', e.target.checked)}
          disabled={saving}
          className="w-4 h-4 text-primary bg-fc-bg border-fc-border rounded focus:ring-primary focus:ring-2 disabled:opacity-50"
        />
        <span className="ml-2 text-sm text-fc-text font-medium">Enable Pushover notifications</span>
      </label>

      <div>
        <label htmlFor="pushover_user_key" className="block text-sm font-medium text-fc-text mb-1">
          User Key
        </label>
        <input
          type="password"
          id="pushover_user_key"
          value={settings.pushover_user_key ?? ''}
          onChange={(e) => onTextChange('pushover_user_key', e.target.value)}
          placeholder="u..."
          disabled={saving || !isEnabled}
          className="w-full px-3 py-2 bg-fc-bg border border-fc-border rounded-lg text-fc-text placeholder-fc-text-muted focus:outline-none focus:ring-2 focus:ring-primary disabled:opacity-50"
        />
        <p className="mt-1 text-xs text-fc-text-muted">Found on your Pushover dashboard</p>
      </div>

      <div>
        <label htmlFor="pushover_api_token" className="block text-sm font-medium text-fc-text mb-1">
          API Token / App Token
        </label>
        <input
          type="password"
          id="pushover_api_token"
          value={settings.pushover_api_token ?? ''}
          onChange={(e) => onTextChange('pushover_api_token', e.target.value)}
          placeholder="a..."
          disabled={saving || !isEnabled}
          className="w-full px-3 py-2 bg-fc-bg border border-fc-border rounded-lg text-fc-text placeholder-fc-text-muted focus:outline-none focus:ring-2 focus:ring-primary disabled:opacity-50"
        />
        <p className="mt-1 text-xs text-fc-text-muted">
          Create an application at pushover.net to get a token
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
            Pushover requires a one-time $5 purchase per platform (iOS, Android, Desktop). Visit pushover.net to set up your account.
          </p>
        </div>
      </div>
    </div>
  )
}
