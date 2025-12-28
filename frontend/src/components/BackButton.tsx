import { Link } from 'react-router-dom'
import { ArrowLeft } from 'lucide-react'
import { useBigMode } from '@/contexts/BigModeContext'

interface BackButtonProps {
  to?: string
  label?: string
}

export default function BackButton({ to = '/', label = 'Back to Home' }: BackButtonProps) {
  const { bigMode } = useBigMode()

  return (
    <Link
      to={to}
      className={`inline-flex items-center gap-2 text-fc-text-muted hover:text-fc-text transition-colors ${
        bigMode ? 'text-lg py-3 px-4' : 'text-base py-2 px-3'
      }`}
    >
      <ArrowLeft className={bigMode ? 'w-6 h-6' : 'w-5 h-5'} />
      <span>{label}</span>
    </Link>
  )
}
