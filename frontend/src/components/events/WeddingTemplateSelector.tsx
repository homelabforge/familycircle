import { Calendar, Check } from 'lucide-react'
import { useBigMode } from '@/contexts/BigModeContext'
import { WEDDING_TEMPLATES } from '@/lib/api'

export default function WeddingTemplateSelector({
  selected,
  onSelect,
}: {
  selected: string
  onSelect: (template: string) => void
}) {
  const { bigMode } = useBigMode()

  return (
    <div className="mt-4 pt-4 border-t border-fc-border">
      <label className="block text-sm font-medium text-fc-text mb-3">
        Sub-event Template (optional)
      </label>
      <p className="text-xs text-fc-text-muted mb-3">
        Automatically create related events (ceremony, reception, etc.)
      </p>

      <div className="space-y-2">
        {/* No template option */}
        <button
          type="button"
          onClick={() => onSelect('')}
          className={`
            w-full text-left p-3 rounded-xl border-2 transition-all
            ${!selected
              ? 'border-primary bg-primary/5'
              : 'border-fc-border bg-fc-surface hover:bg-fc-surface-hover'
            }
          `}
        >
          <div className="flex items-center justify-between">
            <div>
              <span className={`font-medium text-fc-text ${bigMode ? 'text-base' : 'text-sm'}`}>
                No template
              </span>
              <p className="text-xs text-fc-text-muted mt-0.5">
                I'll create sub-events manually if needed
              </p>
            </div>
            {!selected && (
              <div className="w-5 h-5 bg-primary rounded-full flex items-center justify-center">
                <Check className="w-3 h-3 text-white" />
              </div>
            )}
          </div>
        </button>

        {WEDDING_TEMPLATES.map((tpl) => (
          <button
            key={tpl.name}
            type="button"
            onClick={() => onSelect(tpl.name)}
            className={`
              w-full text-left p-3 rounded-xl border-2 transition-all
              ${selected === tpl.name
                ? 'border-primary bg-primary/5'
                : 'border-fc-border bg-fc-surface hover:bg-fc-surface-hover'
              }
            `}
          >
            <div className="flex items-center justify-between">
              <div>
                <span className={`font-medium text-fc-text ${bigMode ? 'text-base' : 'text-sm'}`}>
                  {tpl.label}
                </span>
                <div className="flex flex-wrap gap-1.5 mt-1.5">
                  {tpl.sub_events.map((se, idx) => (
                    <span
                      key={idx}
                      className="inline-flex items-center gap-1 text-xs bg-violet-500/10 text-violet-600 px-2 py-0.5 rounded-full"
                    >
                      <Calendar className="w-2.5 h-2.5" />
                      {se.title}
                    </span>
                  ))}
                </div>
              </div>
              {selected === tpl.name && (
                <div className="w-5 h-5 bg-primary rounded-full flex items-center justify-center flex-shrink-0">
                  <Check className="w-3 h-3 text-white" />
                </div>
              )}
            </div>
          </button>
        ))}
      </div>
    </div>
  )
}
