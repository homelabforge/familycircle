import { AtSign, Send, Info, ExternalLink } from 'lucide-react'

interface TelegramConfigProps {
  settings: Record<string, string>
  onTextChange: (key: string, value: string) => void
  onToggle: (key: string, value: boolean) => void
  onTest: () => void
  testing: boolean
  saving: boolean
}

export function TelegramConfig({ settings, onTextChange, onToggle, onTest, testing, saving }: TelegramConfigProps) {
  const isEnabled = settings.telegram_enabled === 'true'
  const hasRequired = Boolean(settings.telegram_bot_token && settings.telegram_chat_id)

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3 mb-2">
        <AtSign className="w-5 h-5 text-primary" />
        <div>
          <h3 className="text-base font-semibold text-fc-text">Telegram</h3>
          <p className="text-xs text-fc-text-muted">Send notifications via Telegram bot</p>
        </div>
      </div>

      <label className="flex items-center cursor-pointer">
        <input
          type="checkbox"
          checked={isEnabled}
          onChange={(e) => onToggle('telegram_enabled', e.target.checked)}
          disabled={saving}
          className="w-4 h-4 text-primary bg-fc-bg border-fc-border rounded focus:ring-primary focus:ring-2 disabled:opacity-50"
        />
        <span className="ml-2 text-sm text-fc-text font-medium">Enable Telegram notifications</span>
      </label>

      <div>
        <label htmlFor="telegram_bot_token" className="block text-sm font-medium text-fc-text mb-1">
          Bot Token
        </label>
        <input
          type="password"
          id="telegram_bot_token"
          value={settings.telegram_bot_token ?? ''}
          onChange={(e) => onTextChange('telegram_bot_token', e.target.value)}
          placeholder="123456789:ABC..."
          disabled={saving || !isEnabled}
          className="w-full px-3 py-2 bg-fc-bg border border-fc-border rounded-lg text-fc-text placeholder-fc-text-muted focus:outline-none focus:ring-2 focus:ring-primary disabled:opacity-50"
        />
        <p className="mt-1 text-xs text-fc-text-muted">Get from @BotFather on Telegram</p>
      </div>

      <div>
        <label htmlFor="telegram_chat_id" className="block text-sm font-medium text-fc-text mb-1">
          Chat ID
        </label>
        <input
          type="text"
          id="telegram_chat_id"
          value={settings.telegram_chat_id ?? ''}
          onChange={(e) => onTextChange('telegram_chat_id', e.target.value)}
          placeholder="-1001234567890 or 123456789"
          disabled={saving || !isEnabled}
          className="w-full px-3 py-2 bg-fc-bg border border-fc-border rounded-lg text-fc-text placeholder-fc-text-muted focus:outline-none focus:ring-2 focus:ring-primary disabled:opacity-50"
        />
        <p className="mt-1 text-xs text-fc-text-muted">Your user ID, group ID, or channel ID</p>
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
            <p><strong>To set up Telegram notifications:</strong></p>
            <ol className="list-decimal list-inside space-y-1">
              <li>Message <span className="font-mono">@BotFather</span> on Telegram</li>
              <li>Create a new bot with <span className="font-mono">/newbot</span></li>
              <li>Copy the bot token</li>
              <li>Start a chat with your bot</li>
              <li>Get your chat ID from <span className="font-mono">@userinfobot</span></li>
            </ol>
            <a
              href="https://core.telegram.org/bots"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1 text-primary hover:underline"
            >
              Telegram Bot Documentation <ExternalLink className="w-3 h-3" />
            </a>
          </div>
        </div>
      </div>
    </div>
  )
}
