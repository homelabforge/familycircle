import { useState } from 'react'
import { BarChart3, Lock, Users, Check, Clock, X } from 'lucide-react'
import { Link } from 'react-router-dom'
import { useBigMode } from '@/contexts/BigModeContext'
import { pollsApi, type Poll } from '@/lib/api'
import { toast } from 'sonner'

interface PollCardProps {
  poll: Poll
  onUpdated?: (poll: Poll) => void
  compact?: boolean
}

export default function PollCard({ poll, onUpdated, compact = false }: PollCardProps) {
  const { bigMode } = useBigMode()
  const [voting, setVoting] = useState(false)
  const [selectedOptions, setSelectedOptions] = useState<Set<string>>(
    new Set(poll.user_votes)
  )

  const totalOptionVotes = poll.options.reduce((sum, o) => sum + o.vote_count, 0)

  const handleVote = async (optionId: string) => {
    if (poll.is_closed || voting) return

    let optionIds: string[]
    if (poll.allow_multiple) {
      // Toggle the option
      const next = new Set(selectedOptions)
      if (next.has(optionId)) {
        next.delete(optionId)
      } else {
        next.add(optionId)
      }
      setSelectedOptions(next)
      optionIds = [optionId] // Send only the toggled option
    } else {
      // Single select — replace
      setSelectedOptions(new Set([optionId]))
      optionIds = [optionId]
    }

    try {
      setVoting(true)
      const updated = await pollsApi.vote(poll.id, optionIds)
      setSelectedOptions(new Set(updated.user_votes))
      onUpdated?.(updated)
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to vote')
      // Revert on error
      setSelectedOptions(new Set(poll.user_votes))
    } finally {
      setVoting(false)
    }
  }

  const getPercentage = (voteCount: number): number => {
    if (totalOptionVotes === 0) return 0
    return Math.round((voteCount / totalOptionVotes) * 100)
  }

  return (
    <div
      className={`
        bg-fc-surface border border-fc-border rounded-xl
        ${bigMode ? 'p-5' : 'p-4'}
      `}
    >
      {/* Header */}
      <div className="flex items-start justify-between gap-3 mb-3">
        <div className="flex-1 min-w-0">
          <Link
            to={`/polls/${poll.id}`}
            className={`
              font-medium text-fc-text hover:text-primary transition-colors
              ${bigMode ? 'text-lg' : 'text-base'}
            `}
          >
            {poll.title}
          </Link>
          {!compact && poll.description && (
            <p className={`text-fc-text-muted mt-1 ${bigMode ? 'text-base' : 'text-sm'}`}>
              {poll.description}
            </p>
          )}
        </div>
        <div className="flex items-center gap-2 shrink-0">
          {poll.is_anonymous && (
            <span className="flex items-center gap-1 text-xs font-medium text-fc-text-muted bg-fc-bg px-2 py-1 rounded-md">
              <Lock className="w-3 h-3" />
              Anonymous
            </span>
          )}
          {poll.is_closed ? (
            <span className="flex items-center gap-1 text-xs font-medium text-error bg-error/10 px-2 py-1 rounded-md">
              <X className="w-3 h-3" />
              Closed
            </span>
          ) : poll.close_date ? (
            <span className="flex items-center gap-1 text-xs font-medium text-warning bg-warning/10 px-2 py-1 rounded-md">
              <Clock className="w-3 h-3" />
              Closes {new Date(poll.close_date).toLocaleDateString()}
            </span>
          ) : null}
        </div>
      </div>

      {/* Meta info */}
      <div className={`flex items-center gap-3 mb-3 text-fc-text-muted ${bigMode ? 'text-sm' : 'text-xs'}`}>
        {poll.created_by_name && <span>by {poll.created_by_name}</span>}
        <span className="flex items-center gap-1">
          <Users className="w-3 h-3" />
          {poll.total_votes} {poll.total_votes === 1 ? 'vote' : 'votes'}
        </span>
        {poll.allow_multiple && (
          <span className="flex items-center gap-1">
            <BarChart3 className="w-3 h-3" />
            Multi-select
          </span>
        )}
      </div>

      {/* Options */}
      <div className="space-y-2">
        {poll.options.map((option) => {
          const pct = getPercentage(option.vote_count)
          const isSelected = selectedOptions.has(option.id)
          const canVote = !poll.is_closed

          return (
            <button
              key={option.id}
              onClick={() => canVote && handleVote(option.id)}
              disabled={!canVote || voting}
              className={`
                w-full relative overflow-hidden rounded-lg border transition-all text-left
                ${canVote ? 'cursor-pointer hover:border-primary' : 'cursor-default'}
                ${isSelected
                  ? 'border-primary bg-primary/5'
                  : 'border-fc-border bg-fc-bg'
                }
                ${bigMode ? 'p-3' : 'p-2.5'}
              `}
            >
              {/* Background bar */}
              <div
                className={`
                  absolute inset-y-0 left-0 transition-all duration-300
                  ${isSelected ? 'bg-primary/15' : 'bg-fc-surface-hover'}
                `}
                style={{ width: `${pct}%` }}
              />

              {/* Content */}
              <div className="relative flex items-center justify-between gap-2">
                <div className="flex items-center gap-2 min-w-0">
                  {isSelected && (
                    <Check className="w-4 h-4 text-primary shrink-0" />
                  )}
                  <span className={`text-fc-text truncate ${bigMode ? 'text-base' : 'text-sm'}`}>
                    {option.text}
                  </span>
                </div>
                <span className={`text-fc-text-muted shrink-0 ${bigMode ? 'text-sm' : 'text-xs'}`}>
                  {option.vote_count} ({pct}%)
                </span>
              </div>
            </button>
          )
        })}
      </div>
    </div>
  )
}
