import { useEffect, useState } from 'react'
import { Baby, Plus, Trash2, Loader2, Star, Heart, Sparkles } from 'lucide-react'
import { toast } from 'sonner'
import { useBigMode } from '@/contexts/BigModeContext'
import { useAuth } from '@/contexts/AuthContext'
import { babyShowerUpdatesApi, type BabyShowerUpdate } from '@/lib/api'
import BabyShowerUpdateForm from './BabyShowerUpdateForm'

const UPDATE_TYPE_ICONS: Record<string, { icon: typeof Baby; color: string }> = {
  baby_born: { icon: Star, color: 'text-amber-500' },
  name_announced: { icon: Sparkles, color: 'text-violet-500' },
  gender_revealed: { icon: Heart, color: 'text-rose-500' },
  milestone: { icon: Baby, color: 'text-blue-500' },
  custom: { icon: Baby, color: 'text-fc-text-muted' },
}

const UPDATE_TYPE_LABELS: Record<string, string> = {
  baby_born: 'Baby Born!',
  name_announced: 'Name Announced',
  gender_revealed: 'Gender Revealed',
  milestone: 'Milestone',
  custom: 'Update',
}

export default function BabyShowerTimeline({
  eventId,
  canManage,
  isCancelled,
}: {
  eventId: string
  canManage: boolean
  isCancelled: boolean
}) {
  const { bigMode } = useBigMode()
  const { user } = useAuth()
  const [updates, setUpdates] = useState<BabyShowerUpdate[]>([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [deletingId, setDeletingId] = useState<string | null>(null)

  const loadUpdates = async (): Promise<void> => {
    try {
      setLoading(true)
      const data = await babyShowerUpdatesApi.list(eventId)
      setUpdates(data.updates)
    } catch {
      // Non-critical
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadUpdates()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [eventId])

  const handleDelete = async (updateId: string): Promise<void> => {
    try {
      setDeletingId(updateId)
      await babyShowerUpdatesApi.delete(eventId, updateId)
      setUpdates((prev) => prev.filter((u) => u.id !== updateId))
      toast.success('Update removed')
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to delete update')
    } finally {
      setDeletingId(null)
    }
  }

  if (loading) {
    return (
      <div className="bg-fc-surface border border-fc-border rounded-2xl p-6 mb-6">
        <div className="flex items-center gap-3 mb-4">
          <Baby className="w-5 h-5 text-rose-500" />
          <h2 className={`font-semibold text-fc-text ${bigMode ? 'text-xl' : 'text-lg'}`}>
            Timeline
          </h2>
        </div>
        <div className="flex justify-center py-4">
          <Loader2 className="w-5 h-5 animate-spin text-primary" />
        </div>
      </div>
    )
  }

  return (
    <div className="bg-fc-surface border border-fc-border rounded-2xl p-6 mb-6">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <Baby className="w-5 h-5 text-rose-500" />
          <h2 className={`font-semibold text-fc-text ${bigMode ? 'text-xl' : 'text-lg'}`}>
            Timeline {updates.length > 0 && `(${updates.length})`}
          </h2>
        </div>
        {canManage && !isCancelled && (
          <button
            onClick={() => setShowForm(true)}
            className={`flex items-center gap-1 text-primary hover:text-primary/80 transition-colors ${bigMode ? 'text-base' : 'text-sm'}`}
          >
            <Plus className="w-4 h-4" />
            Add Update
          </button>
        )}
      </div>

      {updates.length === 0 ? (
        <p className={`text-fc-text-muted ${bigMode ? 'text-base' : 'text-sm'}`}>
          No updates yet. {canManage ? 'Share milestones and news with the family!' : ''}
        </p>
      ) : (
        <div className="relative pl-6 space-y-6">
          {/* Timeline line */}
          <div className="absolute left-2 top-2 bottom-2 w-0.5 bg-fc-border" />

          {updates.map((update) => {
            const typeInfo = UPDATE_TYPE_ICONS[update.update_type] || UPDATE_TYPE_ICONS.custom
            const Icon = typeInfo.icon
            return (
              <div key={update.id} className="relative">
                {/* Timeline dot */}
                <div className={`absolute -left-6 top-1 w-4 h-4 rounded-full border-2 border-fc-surface ${
                  update.update_type === 'baby_born' ? 'bg-amber-500' :
                  update.update_type === 'name_announced' ? 'bg-violet-500' :
                  update.update_type === 'gender_revealed' ? 'bg-rose-500' :
                  'bg-fc-border'
                }`} />

                <div className="bg-fc-bg rounded-xl p-4 border border-fc-border">
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex items-center gap-2 mb-1">
                      <Icon className={`w-4 h-4 ${typeInfo.color}`} />
                      <span className={`text-xs font-medium ${typeInfo.color}`}>
                        {UPDATE_TYPE_LABELS[update.update_type] || 'Update'}
                      </span>
                      {update.update_date && (
                        <span className="text-xs text-fc-text-muted">
                          {new Date(update.update_date + 'T00:00:00').toLocaleDateString('en-US', {
                            month: 'short',
                            day: 'numeric',
                            year: 'numeric',
                          })}
                        </span>
                      )}
                    </div>
                    {canManage && (
                      <button
                        onClick={() => handleDelete(update.id)}
                        disabled={deletingId === update.id}
                        className="text-fc-text-muted hover:text-error transition-colors p-1"
                      >
                        {deletingId === update.id ? (
                          <Loader2 className="w-3.5 h-3.5 animate-spin" />
                        ) : (
                          <Trash2 className="w-3.5 h-3.5" />
                        )}
                      </button>
                    )}
                  </div>
                  <h3 className={`font-medium text-fc-text ${bigMode ? 'text-base' : 'text-sm'}`}>
                    {update.title}
                  </h3>
                  {update.notes && (
                    <p className={`text-fc-text-muted mt-1 ${bigMode ? 'text-sm' : 'text-xs'}`}>
                      {update.notes}
                    </p>
                  )}
                  {update.photo_url && (
                    <img
                      src={update.photo_url}
                      alt={update.title}
                      className="mt-2 rounded-lg max-h-48 object-cover"
                    />
                  )}
                  <p className="text-xs text-fc-text-muted mt-2">
                    Posted by {update.posted_by_name === user?.display_name ? 'you' : update.posted_by_name}
                  </p>
                </div>
              </div>
            )
          })}
        </div>
      )}

      {showForm && (
        <BabyShowerUpdateForm
          eventId={eventId}
          onClose={() => setShowForm(false)}
          onCreated={(newUpdate) => {
            setUpdates((prev) => [...prev, newUpdate])
            setShowForm(false)
          }}
        />
      )}
    </div>
  )
}
