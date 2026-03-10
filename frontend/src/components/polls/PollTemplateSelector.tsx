import { useEffect, useState } from 'react'
import { FileText, Loader2 } from 'lucide-react'
import { useBigMode } from '@/contexts/BigModeContext'
import { pollTemplatesApi, type PollTemplate } from '@/lib/api'

interface PollTemplateSelectorProps {
  onSelect: (template: PollTemplate) => void
}

export default function PollTemplateSelector({ onSelect }: PollTemplateSelectorProps) {
  const { bigMode } = useBigMode()
  const [templates, setTemplates] = useState<PollTemplate[]>([])
  const [loading, setLoading] = useState(true)
  const [expanded, setExpanded] = useState(false)

  useEffect(() => {
    pollTemplatesApi
      .list()
      .then((res) => setTemplates(res.templates))
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return (
      <div className="flex items-center gap-2 text-fc-text-muted">
        <Loader2 className="w-4 h-4 animate-spin" />
        <span className={bigMode ? 'text-sm' : 'text-xs'}>Loading templates...</span>
      </div>
    )
  }

  if (templates.length === 0) return null

  return (
    <div>
      <button
        type="button"
        onClick={() => setExpanded((e) => !e)}
        className={`
          flex items-center gap-2 text-primary hover:text-primary/80 transition-colors
          ${bigMode ? 'text-base' : 'text-sm'}
        `}
      >
        <FileText className="w-4 h-4" />
        {expanded ? 'Hide templates' : 'Use a template'}
      </button>

      {expanded && (
        <div className="grid gap-2 mt-2">
          {templates.map((t) => (
            <button
              key={t.id}
              type="button"
              onClick={() => onSelect(t)}
              className={`
                text-left px-3 py-2 bg-fc-bg border border-fc-border rounded-xl
                hover:border-primary/50 transition-colors
              `}
            >
              <div className="flex items-center justify-between">
                <span className={`font-medium text-fc-text ${bigMode ? 'text-base' : 'text-sm'}`}>
                  {t.name}
                </span>
                {t.is_builtin && (
                  <span className="text-xs text-fc-text-muted bg-fc-surface px-1.5 py-0.5 rounded">
                    Built-in
                  </span>
                )}
              </div>
              {t.description && (
                <p className={`text-fc-text-muted mt-0.5 ${bigMode ? 'text-sm' : 'text-xs'}`}>
                  {t.description}
                </p>
              )}
              <p className={`text-fc-text-muted mt-1 ${bigMode ? 'text-sm' : 'text-xs'}`}>
                Options: {t.options.join(', ')}
              </p>
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
