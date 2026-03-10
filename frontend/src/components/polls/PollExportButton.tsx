import { useState } from 'react'
import { Download, Loader2 } from 'lucide-react'
import { useBigMode } from '@/contexts/BigModeContext'
import { pollsApi } from '@/lib/api'
import { toast } from 'sonner'

interface PollExportButtonProps {
  pollId: string
}

export default function PollExportButton({ pollId }: PollExportButtonProps) {
  const { bigMode } = useBigMode()
  const [exporting, setExporting] = useState(false)

  const handleExport = async () => {
    try {
      setExporting(true)
      await pollsApi.exportCsv(pollId)
      toast.success('Poll results exported')
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to export')
    } finally {
      setExporting(false)
    }
  }

  return (
    <button
      onClick={handleExport}
      disabled={exporting}
      className={`
        flex items-center gap-2 px-4 py-2 border border-fc-border text-fc-text rounded-xl
        hover:bg-fc-surface-hover transition-colors disabled:opacity-50
        ${bigMode ? 'text-base' : 'text-sm'}
      `}
    >
      {exporting ? (
        <Loader2 className="w-4 h-4 animate-spin" />
      ) : (
        <Download className="w-4 h-4" />
      )}
      Export CSV
    </button>
  )
}
