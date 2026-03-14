import { useState } from 'react'
import { BarChart3, Plus, Loader2 } from 'lucide-react'
import { useQueryClient } from '@tanstack/react-query'
import BackButton from '@/components/BackButton'
import PollCard from '@/components/PollCard'
import CreatePollModal from '@/components/CreatePollModal'
import { useBigMode } from '@/contexts/BigModeContext'
import { useAuth } from '@/contexts/AuthContext'
import { usePolls } from '@/hooks/queries/usePolls'

type PollFilter = 'all' | 'open' | 'closed' | 'mine'

const FILTERS: { value: PollFilter; label: string }[] = [
  { value: 'all', label: 'All' },
  { value: 'open', label: 'Open' },
  { value: 'closed', label: 'Closed' },
  { value: 'mine', label: 'Mine' },
]

export default function Polls() {
  const { bigMode } = useBigMode()
  const { user } = useAuth()
  const queryClient = useQueryClient()
  const { data, isLoading: loading } = usePolls()
  const polls = data?.polls ?? []
  const [filter, setFilter] = useState<PollFilter>('all')
  const [showCreate, setShowCreate] = useState(false)

  const invalidatePolls = () => queryClient.invalidateQueries({ queryKey: ['polls'] })

  const filteredPolls = polls.filter((p) => {
    switch (filter) {
      case 'open':
        return !p.is_closed
      case 'closed':
        return p.is_closed
      case 'mine':
        return p.created_by_id === user?.id
      default:
        return true
    }
  })

  return (
    <div className="container mx-auto px-4 py-6">
      <BackButton />

      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <BarChart3 className={`text-primary ${bigMode ? 'w-8 h-8' : 'w-7 h-7'}`} />
          <h1 className={`font-bold text-fc-text ${bigMode ? 'text-3xl' : 'text-2xl'}`}>
            Polls
          </h1>
        </div>
        <button
          onClick={() => setShowCreate(true)}
          className={`
            flex items-center gap-2 px-4 py-2 bg-primary text-white rounded-xl
            hover:bg-primary/90 transition-colors
            ${bigMode ? 'text-lg' : 'text-base'}
          `}
        >
          <Plus className="w-5 h-5" />
          Create Poll
        </button>
      </div>

      {/* Filter tabs */}
      <div className="flex gap-2 mb-6 overflow-x-auto">
        {FILTERS.map((f) => (
          <button
            key={f.value}
            onClick={() => setFilter(f.value)}
            className={`
              px-4 py-2 rounded-xl font-medium transition-colors whitespace-nowrap
              ${bigMode ? 'text-base' : 'text-sm'}
              ${filter === f.value
                ? 'bg-primary text-white'
                : 'bg-fc-surface border border-fc-border text-fc-text-muted hover:bg-fc-surface-hover'
              }
            `}
          >
            {f.label}
          </button>
        ))}
      </div>

      {/* Content */}
      {loading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="w-8 h-8 text-primary animate-spin" />
        </div>
      ) : filteredPolls.length === 0 ? (
        <div className="text-center py-12">
          <BarChart3 className="w-12 h-12 text-fc-text-muted mx-auto mb-3" />
          <p className={`text-fc-text-muted ${bigMode ? 'text-lg' : 'text-base'}`}>
            {filter === 'all'
              ? 'No polls yet. Create one to get started!'
              : `No ${filter} polls found.`}
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {filteredPolls.map((poll) => (
            <PollCard
              key={poll.id}
              poll={poll}
              onUpdated={invalidatePolls}
            />
          ))}
        </div>
      )}

      {/* Create modal */}
      <CreatePollModal
        isOpen={showCreate}
        onClose={() => setShowCreate(false)}
        onCreated={invalidatePolls}
      />
    </div>
  )
}
