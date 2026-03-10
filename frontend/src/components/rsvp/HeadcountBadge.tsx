import { Users } from 'lucide-react'
import { useBigMode } from '@/contexts/BigModeContext'

interface HeadcountBadgeProps {
  headcount: number
  rsvpYes: number
}

export default function HeadcountBadge({ headcount, rsvpYes }: HeadcountBadgeProps) {
  const { bigMode } = useBigMode()

  if (headcount === 0) return null

  const guestCount = headcount - rsvpYes

  return (
    <div className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 ${bigMode ? 'text-base' : 'text-sm'}`}>
      <Users className={`${bigMode ? 'w-5 h-5' : 'w-4 h-4'} text-emerald-400`} />
      <span className="text-emerald-400 font-medium">
        {headcount} attending
      </span>
      {guestCount > 0 && (
        <span className="text-fc-text-muted">
          ({rsvpYes} + {guestCount} guest{guestCount !== 1 ? 's' : ''})
        </span>
      )}
    </div>
  )
}
