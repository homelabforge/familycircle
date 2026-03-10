import { Hash, Send, Info, ExternalLink } from 'lucide-react'

interface SlackConfigProps {
  settings: Record<string, string>
  onTextChange: (key: string, value: string) => void
  onToggle: (key: string, value: boolean) => void
  onTest: () => void
  testing: boolean
  saving: boolean
}

export function SlackConfig({ settings, onTextChange, onToggle, onTest, testing, saving }: SlackConfigProps) {
  const isEnabled = settings.slack_enabled === 'true'
  const hasRequired = Boolean(settings.slack_webhook_url)

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3 mb-2">
        <Hash className="w-5 h-5 text-primary" />
        <div>
          <h3 className="text-base font-semibold text-fc-text">Slack</h3>
          <p className="text-xs text-fc-text-muted">Send notifications to a Slack channel</p>
        </div>
      </div>

      <label className="flex items-center cursor-pointer">
        <input
          type="checkbox"
          checked={isEnabled}
          onChange={(e) => onToggle('slack_enabled', e.target.checked)}
          disabled={saving}
          className="w-4 h-4 text-primary bg-fc-bg border-fc-border rounded focus:ring-primary focus:ring-2 disabled:opacity-50"
        />
        <span className="ml-2 text-sm text-fc-text font-medium">Enable Slack notifications</span>
      </label>

      <div>
        <label htmlFor="slack_webhook_url" className="block text-sm font-medium text-fc-text mb-1">
          Webhook URL
        </label>
        <input
          type="password"
          id="slack_webhook_url"
          value={settings.slack_webhook_url ?? ''}
          onChange={(e) => onTextChange('slack_webhook_url', e.target.value)}
          placeholder="https://hooks.slack.com/services/..."
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
            <p>To create a Slack webhook:</p>
            <ol className="list-decimal list-inside space-y-1">
              <li>Go to your Slack workspace settings</li>
              <li>Navigate to Apps &gt; Incoming Webhooks</li>
              <li>Create a new webhook and select a channel</li>
              <li>Copy the webhook URL</li>
            </ol>
            <a
              href="https://api.slack.com/messaging/webhooks"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1 text-primary hover:underline"
            >
              Slack Webhooks Documentation <ExternalLink className="w-3 h-3" />
            </a>
          </div>
        </div>
      </div>
    </div>
  )
}
