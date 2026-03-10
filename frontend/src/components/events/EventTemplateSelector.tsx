import { useState, useEffect } from 'react'
import { FileText, Loader2 } from 'lucide-react'
import { useBigMode } from '@/contexts/BigModeContext'
import { eventTemplatesApi, type EventTemplate } from '@/lib/api'

interface EventTemplateSelectorProps {
  onSelect: (templateJson: string | null) => void
}

export default function EventTemplateSelector({ onSelect }: EventTemplateSelectorProps) {
  const { bigMode } = useBigMode()
  const [templates, setTemplates] = useState<EventTemplate[]>([])
  const [loading, setLoading] = useState(true)
  const [selected, setSelected] = useState<string>('')

  useEffect(() => {
    loadTemplates()
  }, [])

  async function loadTemplates() {
    try {
      const data = await eventTemplatesApi.list()
      setTemplates(data.templates)
    } catch {
      // No templates available
    } finally {
      setLoading(false)
    }
  }

  function handleSelect(templateId: string) {
    setSelected(templateId)
    if (!templateId) {
      onSelect(null)
      return
    }
    const template = templates.find(t => t.id === templateId)
    if (template) {
      onSelect(template.template_json)
    }
  }

  if (loading) return <Loader2 className="w-5 h-5 animate-spin text-fc-text-muted" />
  if (templates.length === 0) return null

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        <FileText className={`${bigMode ? 'w-5 h-5' : 'w-4 h-4'} text-primary`} />
        <h4 className={`font-medium text-fc-text ${bigMode ? 'text-lg' : 'text-sm'}`}>
          Start from Template
        </h4>
      </div>

      <select
        value={selected}
        onChange={e => handleSelect(e.target.value)}
        className={`w-full px-4 py-3 bg-fc-bg border border-fc-border rounded-xl text-fc-text focus:outline-none focus:ring-2 focus:ring-primary ${bigMode ? 'text-lg' : ''}`}
      >
        <option value="">Blank event</option>
        {templates.map(t => (
          <option key={t.id} value={t.id}>
            {t.name}{t.description ? ` — ${t.description}` : ''}
          </option>
        ))}
      </select>
    </div>
  )
}
