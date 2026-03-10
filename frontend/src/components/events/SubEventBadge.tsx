import { Calendar } from 'lucide-react'

export default function SubEventBadge({ count }: { count: number }) {
  if (count <= 0) return null

  return (
    <span className="inline-flex items-center gap-1 text-xs bg-violet-500/10 text-violet-600 px-2 py-0.5 rounded-full font-medium">
      <Calendar className="w-3 h-3" />
      {count} sub-event{count !== 1 ? 's' : ''}
    </span>
  )
}
