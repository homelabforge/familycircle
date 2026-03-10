import { Radio, Send, Info } from 'lucide-react'

interface GotifyConfigProps {
  settings: Record<string, string>
  onTextChange: (key: string, value: string) => void
  onToggle: (key: string, value: boolean) => void
  onTest: () => void
  testing: boolean
  saving: boolean
}

export function GotifyConfig({ settings, onTextChange, onToggle, onTest, testing, saving }: GotifyConfigProps) {
  const isEnabled = settings.gotify_enabled === 'true'
  const hasRequired = Boolean(settings.gotify_server && settings.gotify_token)

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3 mb-2">
        <Radio className="w-5 h-5 text-primary" />
        <div>
          <h3 className="text-base font-semibold text-fc-text">Gotify</h3>
          <p className="text-xs text-fc-text-muted">Self-hosted push notification server</p>
        </div>
      </div>

      <label className="flex items-center cursor-pointer">
        <input
          type="checkbox"
          checked={isEnabled}
          onChange={(e) => onToggle('gotify_enabled', e.target.checked)}
          disabled={saving}
          className="w-4 h-4 text-primary bg-fc-bg border-fc-border rounded focus:ring-primary focus:ring-2 disabled:opacity-50"
        />
        <span className="ml-2 text-sm text-fc-text font-medium">Enable Gotify notifications</span>
      </label>

      <div>
        <label htmlFor="gotify_server" className="block text-sm font-medium text-fc-text mb-1">
          Server URL
        </label>
        <input
          type="url"
          id="gotify_server"
          value={settings.gotify_server ?? ''}
          onChange={(e) => onTextChange('gotify_server', e.target.value)}
          placeholder="https://gotify.example.com"
          disabled={saving || !isEnabled}
          className="w-full px-3 py-2 bg-fc-bg border border-fc-border rounded-lg text-fc-text placeholder-fc-text-muted focus:outline-none focus:ring-2 focus:ring-primary disabled:opacity-50"
        />
      </div>

      <div>
        <label htmlFor="gotify_token" className="block text-sm font-medium text-fc-text mb-1">
          Application Token
        </label>
        <input
          type="password"
          id="gotify_token"
          value={settings.gotify_token ?? ''}
          onChange={(e) => onTextChange('gotify_token', e.target.value)}
          placeholder="A..."
          disabled={saving || !isEnabled}
          className="w-full px-3 py-2 bg-fc-bg border border-fc-border rounded-lg text-fc-text placeholder-fc-text-muted focus:outline-none focus:ring-2 focus:ring-primary disabled:opacity-50"
        />
        <p className="mt-1 text-xs text-fc-text-muted">
          Create an application in Gotify and copy the token
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
            Gotify is a self-hosted notification server. Create an application in your Gotify dashboard to get a token.
          </p>
        </div>
      </div>
    </div>
  )
}
