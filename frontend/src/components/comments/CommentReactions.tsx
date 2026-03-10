import { useState } from 'react'
import { useBigMode } from '@/contexts/BigModeContext'
import { useAuth } from '@/contexts/AuthContext'
import { eventCommentsApi, type CommentReaction } from '@/lib/api'

const EMOJI_OPTIONS = ['👍', '❤️', '😂', '😮', '😢', '🎉']

interface CommentReactionsProps {
  eventId: string
  commentId: string
  reactions: CommentReaction[]
  onReactionsUpdated: (reactions: CommentReaction[]) => void
}

export default function CommentReactions({
  eventId,
  commentId,
  reactions,
  onReactionsUpdated,
}: CommentReactionsProps) {
  const { bigMode } = useBigMode()
  const { user } = useAuth()
  const [showPicker, setShowPicker] = useState(false)
  const [toggling, setToggling] = useState(false)

  const handleToggle = async (emoji: string) => {
    if (toggling) return
    try {
      setToggling(true)
      const result = await eventCommentsApi.toggleReaction(eventId, commentId, emoji)
      onReactionsUpdated(result.reactions)
      setShowPicker(false)
    } catch {
      // Non-critical
    } finally {
      setToggling(false)
    }
  }

  const userReacted = (reaction: CommentReaction) =>
    user ? reaction.user_ids.includes(user.id) : false

  return (
    <div className="flex items-center gap-1.5 flex-wrap mt-1.5">
      {/* Existing reactions */}
      {reactions.map((r) => (
        <button
          key={r.emoji}
          onClick={() => handleToggle(r.emoji)}
          disabled={toggling}
          className={`
            inline-flex items-center gap-1 rounded-full border transition-colors
            ${bigMode ? 'px-2.5 py-1 text-sm' : 'px-2 py-0.5 text-xs'}
            ${
              userReacted(r)
                ? 'border-primary bg-primary/10 text-primary'
                : 'border-fc-border bg-fc-bg text-fc-text-muted hover:border-primary/50'
            }
          `}
        >
          <span>{r.emoji}</span>
          <span>{r.count}</span>
        </button>
      ))}

      {/* Add reaction button */}
      <div className="relative">
        <button
          onClick={() => setShowPicker((p) => !p)}
          className={`
            inline-flex items-center justify-center rounded-full border border-dashed
            border-fc-border text-fc-text-muted hover:border-primary/50 hover:text-primary
            transition-colors
            ${bigMode ? 'w-8 h-8 text-base' : 'w-6 h-6 text-sm'}
          `}
          title="Add reaction"
        >
          +
        </button>

        {/* Emoji picker popup */}
        {showPicker && (
          <div className="absolute bottom-full left-0 mb-1 flex gap-1 bg-fc-surface border border-fc-border rounded-xl p-1.5 shadow-lg z-10">
            {EMOJI_OPTIONS.map((emoji) => (
              <button
                key={emoji}
                onClick={() => handleToggle(emoji)}
                disabled={toggling}
                className={`
                  hover:bg-fc-bg rounded-lg transition-colors
                  ${bigMode ? 'p-1.5 text-xl' : 'p-1 text-lg'}
                `}
              >
                {emoji}
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
