import { MessageSquare, Send, Info, ExternalLink } from 'lucide-react'

interface DiscordConfigProps {
  settings: Record<string, string>
  onTextChange: (key: string, value: string) => void
  onToggle: (key: string, value: boolean) => void
  onTest: () => void
  testing: boolean
  saving: boolean
}

export function DiscordConfig({ settings, onTextChange, onToggle, onTest, testing, saving }: DiscordConfigProps) {
  const isEnabled = settings.discord_enabled === 'true'
  const hasRequired = Boolean(settings.discord_webhook_url)

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3 mb-2">
        <MessageSquare className="w-5 h-5 text-primary" />
        <div>
          <h3 className="text-base font-semibold text-fc-text">Discord</h3>
          <p className="text-xs text-fc-text-muted">Send notifications to a Discord channel</p>
        </div>
      </div>

      <label className="flex items-center cursor-pointer">
        <input
          type="checkbox"
          checked={isEnabled}
          onChange={(e) => onToggle('discord_enabled', e.target.checked)}
          disabled={saving}
          className="w-4 h-4 text-primary bg-fc-bg border-fc-border rounded focus:ring-primary focus:ring-2 disabled:opacity-50"
        />
        <span className="ml-2 text-sm text-fc-text font-medium">Enable Discord notifications</span>
      </label>

      <div>
        <label htmlFor="discord_webhook_url" className="block text-sm font-medium text-fc-text mb-1">
          Webhook URL
        </label>
        <input
          type="password"
          id="discord_webhook_url"
          value={settings.discord_webhook_url ?? ''}
          onChange={(e) => onTextChange('discord_webhook_url', e.target.value)}
          placeholder="https://discord.com/api/webhooks/..."
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
          <div className="text-xs text-fc-text-muted space-y-2">
            <p>To create a Discord webhook:</p>
            <ol className="list-decimal list-inside space-y-1">
              <li>Right-click on the channel you want notifications in</li>
              <li>Select &quot;Edit Channel&quot; &gt; &quot;Integrations&quot;</li>
              <li>Click &quot;Create Webhook&quot;</li>
              <li>Copy the webhook URL</li>
            </ol>
            <a
              href="https://support.discord.com/hc/en-us/articles/228383668-Intro-to-Webhooks"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1 text-primary hover:underline"
            >
              Discord Webhooks Guide <ExternalLink className="w-3 h-3" />
            </a>
          </div>
        </div>
      </div>
    </div>
  )
}
