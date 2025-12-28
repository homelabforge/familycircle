import { Link } from 'react-router-dom'
import { LucideIcon, ChevronRight } from 'lucide-react'
import { useBigMode } from '@/contexts/BigModeContext'

interface DashboardCardProps {
  to: string
  icon: LucideIcon
  title: string
  description?: string
  badge?: string | number
  badgeColor?: 'primary' | 'success' | 'warning' | 'error'
}

export default function DashboardCard({
  to,
  icon: Icon,
  title,
  description,
  badge,
  badgeColor = 'primary',
}: DashboardCardProps) {
  const { bigMode } = useBigMode()

  const badgeColorClasses = {
    primary: 'bg-primary text-white',
    success: 'bg-success text-white',
    warning: 'bg-warning text-white',
    error: 'bg-error text-white',
  }

  return (
    <Link
      to={to}
      className={`
        relative flex flex-col items-center justify-center
        bg-fc-surface hover:bg-fc-surface-hover
        border border-fc-border rounded-2xl
        transition-all duration-200
        hover:shadow-lg hover:-translate-y-1
        focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2
        ${bigMode ? 'min-h-[180px] p-6 gap-4' : 'min-h-[140px] p-4 gap-3'}
      `}
    >
      {/* Badge */}
      {badge && (
        <span
          className={`
            absolute top-3 right-3
            ${badgeColorClasses[badgeColor]}
            ${bigMode ? 'text-sm px-3 py-1' : 'text-xs px-2 py-0.5'}
            rounded-full font-medium
          `}
        >
          {badge}
        </span>
      )}

      {/* Icon */}
      <div
        className={`
          flex items-center justify-center
          ${bigMode ? 'w-16 h-16' : 'w-12 h-12'}
          rounded-xl bg-primary/10
        `}
      >
        <Icon
          className={`
            text-primary
            ${bigMode ? 'w-10 h-10' : 'w-7 h-7'}
          `}
        />
      </div>

      {/* Title */}
      <span
        className={`
          font-semibold text-fc-text text-center
          ${bigMode ? 'text-xl' : 'text-lg'}
        `}
      >
        {title}
      </span>

      {/* Description (optional) */}
      {description && (
        <span
          className={`
            text-fc-text-muted text-center
            ${bigMode ? 'text-base' : 'text-sm'}
          `}
        >
          {description}
        </span>
      )}

      {/* Arrow indicator */}
      <div className="absolute bottom-3 right-3 text-fc-text-muted">
        <ChevronRight className={bigMode ? 'w-6 h-6' : 'w-5 h-5'} />
      </div>
    </Link>
  )
}
