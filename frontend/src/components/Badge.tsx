import { useBigMode } from '@/contexts/BigModeContext'

interface BadgeProps {
  children: React.ReactNode
  variant?: 'primary' | 'success' | 'warning' | 'error' | 'muted'
}

export default function Badge({ children, variant = 'primary' }: BadgeProps) {
  const { bigMode } = useBigMode()

  const variantClasses = {
    primary: 'bg-primary text-white',
    success: 'bg-success text-white',
    warning: 'bg-warning text-white',
    error: 'bg-error text-white',
    muted: 'bg-fc-surface-hover text-fc-text-muted',
  }

  return (
    <span
      className={`
        inline-flex items-center justify-center
        font-medium rounded-full
        ${variantClasses[variant]}
        ${bigMode ? 'text-sm px-3 py-1' : 'text-xs px-2 py-0.5'}
      `}
    >
      {children}
    </span>
  )
}
