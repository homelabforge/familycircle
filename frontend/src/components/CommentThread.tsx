import { useEffect, useState } from 'react'
import { MessageSquare, Send, Pencil, Trash2, Loader2, X, Check, Pin } from 'lucide-react'
import Markdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { useBigMode } from '@/contexts/BigModeContext'
import { useAuth } from '@/contexts/AuthContext'
import { eventCommentsApi, type EventComment, type CommentReaction } from '@/lib/api'
import CommentReactions from '@/components/comments/CommentReactions'
import MentionInput from '@/components/comments/MentionInput'
import { toast } from 'sonner'

interface CommentThreadProps {
  eventId: string
  isCancelled?: boolean
  canPin?: boolean
}

function CommentItem({
  comment,
  eventId,
  isAdmin,
  canPin,
  onUpdated,
  onDeleted,
}: {
  comment: EventComment
  eventId: string
  isAdmin: boolean
  canPin: boolean
  onUpdated: (comment: EventComment) => void
  onDeleted: (commentId: string) => void
}) {
  const { bigMode } = useBigMode()
  const [editing, setEditing] = useState(false)
  const [editContent, setEditContent] = useState(comment.content)
  const [saving, setSaving] = useState(false)
  const [deleting, setDeleting] = useState(false)
  const [pinning, setPinning] = useState(false)

  const handleSave = async () => {
    const trimmed = editContent.trim()
    if (!trimmed) return

    try {
      setSaving(true)
      const updated = await eventCommentsApi.update(eventId, comment.id, trimmed)
      onUpdated(updated)
      setEditing(false)
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to update comment')
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async () => {
    if (!confirm('Delete this comment?')) return
    try {
      setDeleting(true)
      await eventCommentsApi.delete(eventId, comment.id)
      onDeleted(comment.id)
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to delete comment')
    } finally {
      setDeleting(false)
    }
  }

  const handleTogglePin = async () => {
    try {
      setPinning(true)
      const updated = comment.is_pinned
        ? await eventCommentsApi.unpin(eventId, comment.id)
        : await eventCommentsApi.pin(eventId, comment.id)
      onUpdated(updated)
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to update pin')
    } finally {
      setPinning(false)
    }
  }

  const handleReactionsUpdated = (reactions: CommentReaction[]) => {
    onUpdated({ ...comment, reactions })
  }

  const canEdit = comment.is_own
  const canDelete = comment.is_own || isAdmin

  return (
    <div
      className={`
        rounded-xl
        ${bigMode ? 'p-4' : 'p-3'}
        ${comment.is_pinned ? 'bg-primary/5 border border-primary/20' : 'bg-fc-bg'}
      `}
    >
      {/* Pinned badge */}
      {comment.is_pinned && (
        <div className={`flex items-center gap-1 text-primary mb-1.5 ${bigMode ? 'text-xs' : 'text-[10px]'}`}>
          <Pin className="w-3 h-3" />
          <span className="font-medium">Pinned</span>
        </div>
      )}

      {/* Header */}
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <span className={`font-medium text-fc-text ${bigMode ? 'text-base' : 'text-sm'}`}>
            {comment.user_name}
          </span>
          <span className={`text-fc-text-muted ${bigMode ? 'text-sm' : 'text-xs'}`}>
            {new Date(comment.created_at).toLocaleString(undefined, {
              month: 'short',
              day: 'numeric',
              hour: 'numeric',
              minute: '2-digit',
            })}
          </span>
          {comment.edited_at && (
            <span className={`text-fc-text-muted italic ${bigMode ? 'text-sm' : 'text-xs'}`}>
              (edited)
            </span>
          )}
        </div>
        {!editing && (
          <div className="flex items-center gap-1">
            {canPin && (
              <button
                onClick={handleTogglePin}
                disabled={pinning}
                className={`
                  p-1.5 rounded-lg transition-colors disabled:opacity-50
                  ${comment.is_pinned
                    ? 'text-primary hover:text-primary/70 hover:bg-primary/10'
                    : 'text-fc-text-muted hover:text-primary hover:bg-fc-surface-hover'
                  }
                `}
                title={comment.is_pinned ? 'Unpin' : 'Pin'}
              >
                <Pin className="w-3.5 h-3.5" />
              </button>
            )}
            {canEdit && (
              <button
                onClick={() => {
                  setEditContent(comment.content)
                  setEditing(true)
                }}
                className="p-1.5 rounded-lg text-fc-text-muted hover:text-primary hover:bg-fc-surface-hover transition-colors"
                title="Edit"
              >
                <Pencil className="w-3.5 h-3.5" />
              </button>
            )}
            {canDelete && (
              <button
                onClick={handleDelete}
                disabled={deleting}
                className="p-1.5 rounded-lg text-fc-text-muted hover:text-error hover:bg-error/10 transition-colors disabled:opacity-50"
                title="Delete"
              >
                <Trash2 className="w-3.5 h-3.5" />
              </button>
            )}
          </div>
        )}
      </div>

      {/* Content or edit form */}
      {editing ? (
        <div className="space-y-2">
          <textarea
            value={editContent}
            onChange={(e) => setEditContent(e.target.value)}
            className={`
              w-full px-3 py-2 bg-fc-surface border border-fc-border rounded-lg
              text-fc-text focus:outline-none focus:ring-2 focus:ring-primary
              ${bigMode ? 'text-base' : 'text-sm'}
            `}
            rows={3}
            maxLength={5000}
          />
          <div className="flex gap-2 justify-end">
            <button
              onClick={() => setEditing(false)}
              className="p-1.5 rounded-lg text-fc-text-muted hover:bg-fc-surface-hover transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
            <button
              onClick={handleSave}
              disabled={saving || !editContent.trim()}
              className="p-1.5 rounded-lg text-primary hover:bg-primary/10 transition-colors disabled:opacity-50"
            >
              {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Check className="w-4 h-4" />}
            </button>
          </div>
        </div>
      ) : (
        <div className={`text-fc-text prose prose-sm max-w-none dark:prose-invert ${bigMode ? 'prose-base' : ''}`}>
          <Markdown remarkPlugins={[remarkGfm]}>{comment.content}</Markdown>
        </div>
      )}

      {/* Reactions */}
      <CommentReactions
        eventId={eventId}
        commentId={comment.id}
        reactions={comment.reactions}
        onReactionsUpdated={handleReactionsUpdated}
      />
    </div>
  )
}

export default function CommentThread({ eventId, isCancelled = false, canPin = false }: CommentThreadProps) {
  const { bigMode } = useBigMode()
  const { isOrganizer } = useAuth()
  const [comments, setComments] = useState<EventComment[]>([])
  const [loading, setLoading] = useState(true)
  const [newComment, setNewComment] = useState('')
  const [submitting, setSubmitting] = useState(false)

  const loadComments = async () => {
    try {
      setLoading(true)
      const res = await eventCommentsApi.list(eventId)
      setComments(res.comments)
    } catch {
      // Silently fail — comments are non-critical
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadComments()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [eventId])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    const trimmed = newComment.trim()
    if (!trimmed) return

    try {
      setSubmitting(true)
      const comment = await eventCommentsApi.create(eventId, trimmed)
      setComments((prev) => [...prev, comment])
      setNewComment('')
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to post comment')
    } finally {
      setSubmitting(false)
    }
  }

  const handleUpdated = (updated: EventComment) => {
    setComments((prev) => prev.map((c) => (c.id === updated.id ? updated : c)))
  }

  const handleDeleted = (commentId: string) => {
    setComments((prev) => prev.filter((c) => c.id !== commentId))
  }

  return (
    <div className={`mt-8 ${bigMode ? 'mt-10' : ''}`}>
      <h2
        className={`
          flex items-center gap-2 font-semibold text-fc-text mb-4
          ${bigMode ? 'text-xl' : 'text-lg'}
        `}
      >
        <MessageSquare className={bigMode ? 'w-6 h-6' : 'w-5 h-5'} />
        Comments
        {comments.length > 0 && (
          <span className="text-fc-text-muted font-normal">({comments.length})</span>
        )}
      </h2>

      {loading ? (
        <div className="flex items-center justify-center py-6">
          <Loader2 className="w-6 h-6 text-primary animate-spin" />
        </div>
      ) : (
        <>
          {/* Comments list */}
          {comments.length > 0 ? (
            <div className="space-y-3 mb-4">
              {comments.map((comment) => (
                <CommentItem
                  key={comment.id}
                  comment={comment}
                  eventId={eventId}
                  isAdmin={isOrganizer}
                  canPin={canPin}
                  onUpdated={handleUpdated}
                  onDeleted={handleDeleted}
                />
              ))}
            </div>
          ) : (
            <p className={`text-fc-text-muted mb-4 ${bigMode ? 'text-base' : 'text-sm'}`}>
              No comments yet. Be the first to comment!
            </p>
          )}

          {/* New comment form with @mention support */}
          {!isCancelled && (
            <form onSubmit={handleSubmit} className="flex gap-2">
              <MentionInput
                value={newComment}
                onChange={setNewComment}
                placeholder="Write a comment... (use @name to mention)"
              />
              <button
                type="submit"
                disabled={submitting || !newComment.trim()}
                className={`
                  self-end px-4 py-3 bg-primary text-white rounded-xl
                  hover:bg-primary/90 transition-colors disabled:opacity-50
                `}
              >
                {submitting ? (
                  <Loader2 className="w-5 h-5 animate-spin" />
                ) : (
                  <Send className="w-5 h-5" />
                )}
              </button>
            </form>
          )}
        </>
      )}
    </div>
  )
}
