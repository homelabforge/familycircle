import { useEffect, useState } from 'react'
import { useParams, Link, useNavigate } from 'react-router-dom'
import { BarChart3, Loader2, Lock, Calendar, Trash2, XCircle, ArrowLeft } from 'lucide-react'
import BackButton from '@/components/BackButton'
import PollCard from '@/components/PollCard'
import PollExportButton from '@/components/polls/PollExportButton'
import { useBigMode } from '@/contexts/BigModeContext'
import { useAuth } from '@/contexts/AuthContext'
import { pollsApi, type Poll } from '@/lib/api'
import { toast } from 'sonner'

export default function PollDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { bigMode } = useBigMode()
  const { user, isOrganizer } = useAuth()
  const [poll, setPoll] = useState<Poll | null>(null)
  const [loading, setLoading] = useState(true)
  const [closing, setClosing] = useState(false)
  const [deleting, setDeleting] = useState(false)

  const loadPoll = async () => {
    if (!id) return
    try {
      setLoading(true)
      const data = await pollsApi.get(id)
      setPoll(data)
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to load poll')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadPoll()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id])

  const handleClose = async () => {
    if (!poll) return
    try {
      setClosing(true)
      const updated = await pollsApi.close(poll.id)
      setPoll(updated)
      toast.success('Poll closed')
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to close poll')
    } finally {
      setClosing(false)
    }
  }

  const handleDelete = async () => {
    if (!poll || !confirm('Are you sure you want to delete this poll?')) return
    try {
      setDeleting(true)
      await pollsApi.delete(poll.id)
      toast.success('Poll deleted')
      navigate('/polls')
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to delete poll')
    } finally {
      setDeleting(false)
    }
  }

  const canManage = poll && (poll.created_by_id === user?.id || isOrganizer)

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-6">
        <BackButton />
        <div className="flex items-center justify-center py-12">
          <Loader2 className="w-8 h-8 text-primary animate-spin" />
        </div>
      </div>
    )
  }

  if (!poll) {
    return (
      <div className="container mx-auto px-4 py-6">
        <BackButton />
        <div className="text-center py-12">
          <p className="text-fc-text-muted">Poll not found.</p>
          <Link to="/polls" className="text-primary hover:underline mt-2 inline-block">
            Back to Polls
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="container mx-auto px-4 py-6 max-w-2xl">
      <BackButton />

      {/* Header */}
      <div className="mb-6">
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-center gap-3">
            <BarChart3 className={`text-primary shrink-0 ${bigMode ? 'w-8 h-8' : 'w-7 h-7'}`} />
            <h1 className={`font-bold text-fc-text ${bigMode ? 'text-3xl' : 'text-2xl'}`}>
              {poll.title}
            </h1>
          </div>
          <div className="flex items-center gap-2 shrink-0">
            {poll.is_anonymous && (
              <span className="flex items-center gap-1 text-xs font-medium text-fc-text-muted bg-fc-bg px-2 py-1 rounded-md">
                <Lock className="w-3 h-3" />
                Anonymous
              </span>
            )}
          </div>
        </div>

        {poll.description && (
          <p className={`text-fc-text-muted mt-2 ${bigMode ? 'text-lg' : 'text-base'}`}>
            {poll.description}
          </p>
        )}

        <div className={`flex flex-wrap items-center gap-4 mt-3 text-fc-text-muted ${bigMode ? 'text-sm' : 'text-xs'}`}>
          {poll.created_by_name && <span>Created by {poll.created_by_name}</span>}
          {poll.created_at && (
            <span className="flex items-center gap-1">
              <Calendar className="w-3 h-3" />
              {new Date(poll.created_at).toLocaleDateString()}
            </span>
          )}
          {poll.event_id && (
            <Link to={`/event/${poll.event_id}`} className="text-primary hover:underline flex items-center gap-1">
              <ArrowLeft className="w-3 h-3" />
              View Event
            </Link>
          )}
        </div>
      </div>

      {/* Poll card with voting */}
      <PollCard
        poll={poll}
        onUpdated={(updated) => setPoll(updated)}
      />

      {/* Management actions */}
      {canManage && (
        <div className="flex flex-wrap gap-3 mt-6">
          <PollExportButton pollId={poll.id} />
          {!poll.is_closed && (
            <button
              onClick={handleClose}
              disabled={closing}
              className={`
                flex items-center gap-2 px-4 py-2 border border-warning text-warning rounded-xl
                hover:bg-warning/10 transition-colors disabled:opacity-50
                ${bigMode ? 'text-base' : 'text-sm'}
              `}
            >
              <XCircle className="w-4 h-4" />
              {closing ? 'Closing...' : 'Close Poll'}
            </button>
          )}
          <button
            onClick={handleDelete}
            disabled={deleting}
            className={`
              flex items-center gap-2 px-4 py-2 border border-error text-error rounded-xl
              hover:bg-error/10 transition-colors disabled:opacity-50
              ${bigMode ? 'text-base' : 'text-sm'}
            `}
          >
            <Trash2 className="w-4 h-4" />
            {deleting ? 'Deleting...' : 'Delete Poll'}
          </button>
        </div>
      )}
    </div>
  )
}
