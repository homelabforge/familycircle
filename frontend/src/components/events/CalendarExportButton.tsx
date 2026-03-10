import { Calendar, Download } from 'lucide-react'
import { useBigMode } from '@/contexts/BigModeContext'
import { getToken } from '@/lib/api'

interface CalendarExportButtonProps {
  eventId: string
}

export default function CalendarExportButton({ eventId }: CalendarExportButtonProps) {
  const { bigMode } = useBigMode()

  const handleDownload = async () => {
    const token = getToken()
    const response = await fetch(`/api/events/${eventId}/calendar.ics`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    })

    if (!response.ok) {
      alert('Failed to download calendar file')
      return
    }

    const blob = await response.blob()
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `event-${eventId}.ics`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  return (
    <button
      onClick={handleDownload}
      className={`
        inline-flex items-center gap-2 text-fc-text-muted hover:text-primary transition-colors
        ${bigMode ? 'text-base' : 'text-sm'}
      `}
      title="Download .ics calendar file"
    >
      <Calendar className={bigMode ? 'w-5 h-5' : 'w-4 h-4'} />
      <Download className={bigMode ? 'w-4 h-4' : 'w-3.5 h-3.5'} />
    </button>
  )
}
