import { LucideIcon } from 'lucide-react'
import { useBigMode } from '@/contexts/BigModeContext'

interface EmptyStateProps {
  icon: LucideIcon
  title: string
  description?: string
  action?: {
    label: string
    onClick: () => void
  }
}

export default function EmptyState({
  icon: Icon,
  title,
  description,
  action,
}: EmptyStateProps) {
  const { bigMode } = useBigMode()

  return (
    <div className="text-center py-12">
      <div className="w-16 h-16 bg-fc-border/30 rounded-full flex items-center justify-center mx-auto mb-4">
        <Icon className="w-8 h-8 text-fc-text-muted opacity-60" />
      </div>
      <h3
        className={`font-medium text-fc-text mb-2 ${bigMode ? 'text-xl' : 'text-lg'}`}
      >
        {title}
      </h3>
      {description && (
        <p className={`text-fc-text-muted ${bigMode ? 'text-base' : 'text-sm'}`}>
          {description}
        </p>
      )}
      {action && (
        <button
          onClick={action.onClick}
          className={`
            mt-4 px-4 py-2 bg-primary text-white rounded-xl
            hover:bg-primary-hover transition-colors
            ${bigMode ? 'text-lg' : ''}
          `}
        >
          {action.label}
        </button>
      )}
    </div>
  )
}
