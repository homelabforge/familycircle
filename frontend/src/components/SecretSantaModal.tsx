import { useEffect, useState } from 'react'
import { TreePine, Shuffle, UserX, Check, AlertCircle, Loader2, Plus, X, DollarSign } from 'lucide-react'
import { toast } from 'sonner'
import { useBigMode } from '@/contexts/BigModeContext'
import {
  eventsApi,
  secretSantaApi,
  familyApi,
  type Event,
  type SecretSantaStatus,
  type SecretSantaExclusion,
  type FamilyMember,
} from '@/lib/api'

interface SecretSantaModalProps {
  isOpen: boolean
  onClose: () => void
}

export default function SecretSantaModal({ isOpen, onClose }: SecretSantaModalProps) {
  const { bigMode } = useBigMode()
  const [events, setEvents] = useState<Event[]>([])
  const [selectedEventId, setSelectedEventId] = useState<string | null>(null)
  const [status, setStatus] = useState<SecretSantaStatus | null>(null)
  const [exclusions, setExclusions] = useState<SecretSantaExclusion[]>([])
  const [members, setMembers] = useState<FamilyMember[]>([])
  const [loading, setLoading] = useState(true)
  const [running, setRunning] = useState(false)
  const [showExclusionForm, setShowExclusionForm] = useState(false)
  const [member1, setMember1] = useState('')
  const [member2, setMember2] = useState('')

  // Budget rules
  const [budgetMin, setBudgetMin] = useState<string>('')
  const [budgetMax, setBudgetMax] = useState<string>('')
  const [notes, setNotes] = useState('')
  const [savingRules, setSavingRules] = useState(false)

  useEffect(() => {
    if (isOpen) {
      loadEvents()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isOpen])

  useEffect(() => {
    if (selectedEventId) {
      loadStatus()
      loadExclusions()
      const event = events.find((e) => e.id === selectedEventId)
      if (event) {
        setBudgetMin(event.secret_santa_budget_min?.toString() || '')
        setBudgetMax(event.secret_santa_budget_max?.toString() || '')
        setNotes(event.secret_santa_notes || '')
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedEventId, events])

  const loadEvents = async () => {
    try {
      setLoading(true)
      const [eventsRes, membersRes] = await Promise.all([
        eventsApi.list(),
        familyApi.listMembers(),
      ])
      const ssEvents = eventsRes.events.filter((e) => e.has_secret_santa)
      setEvents(ssEvents)
      setMembers(membersRes.members)
      if (ssEvents.length > 0 && !selectedEventId) {
        setSelectedEventId(ssEvents[0].id)
      }
    } catch (err) {
      toast.error('Failed to load events')
    } finally {
      setLoading(false)
    }
  }

  const loadStatus = async () => {
    if (!selectedEventId) return
    try {
      const res = await secretSantaApi.getStatus(selectedEventId)
      setStatus(res)
    } catch (err) {
      console.error('Failed to load status:', err)
    }
  }

  const loadExclusions = async () => {
    if (!selectedEventId) return
    try {
      const res = await secretSantaApi.getExclusions(selectedEventId)
      setExclusions(res.exclusions)
    } catch (err) {
      console.error('Failed to load exclusions:', err)
    }
  }

  const handleRunAssignment = async () => {
    if (!selectedEventId) return
    if (status?.status === 'assigned') {
      if (!confirm('This will overwrite existing assignments. Are you sure?')) {
        return
      }
    }

    try {
      setRunning(true)
      const res = await secretSantaApi.runAssignment(selectedEventId)
      toast.success(`Assignments created for ${res.assignment_count} participants!`)
      await loadStatus()
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to run assignment')
    } finally {
      setRunning(false)
    }
  }

  const handleAddExclusion = async () => {
    if (!selectedEventId || !member1 || !member2 || member1 === member2) {
      toast.error('Please select two different members')
      return
    }

    try {
      await secretSantaApi.addExclusion(selectedEventId, member1, member2)
      toast.success('Exclusion added')
      setShowExclusionForm(false)
      setMember1('')
      setMember2('')
      await loadExclusions()
    } catch (err) {
      toast.error('Failed to add exclusion')
    }
  }

  const handleRemoveExclusion = async (exclusionId: string) => {
    if (!selectedEventId) return
    try {
      await secretSantaApi.removeExclusion(selectedEventId, exclusionId)
      toast.success('Exclusion removed')
      await loadExclusions()
    } catch (err) {
      toast.error('Failed to remove exclusion')
    }
  }

  const handleSaveRules = async () => {
    if (!selectedEventId) return
    try {
      setSavingRules(true)
      await eventsApi.update(selectedEventId, {
        secret_santa_budget_min: budgetMin ? parseInt(budgetMin) : undefined,
        secret_santa_budget_max: budgetMax ? parseInt(budgetMax) : undefined,
        secret_santa_notes: notes || undefined,
      })
      toast.success('Rules saved')
      await loadEvents()
    } catch (err) {
      toast.error('Failed to save rules')
    } finally {
      setSavingRules(false)
    }
  }

  const handleClose = () => {
    setShowExclusionForm(false)
    onClose()
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/50 backdrop-blur-sm"
        onClick={handleClose}
      />

      {/* Modal */}
      <div
        className={`
          relative bg-fc-surface border border-fc-border rounded-2xl
          w-full max-w-2xl mx-4 shadow-xl max-h-[90vh] overflow-hidden flex flex-col
          ${bigMode ? 'p-8' : 'p-6'}
        `}
      >
        {/* Close button */}
        <button
          onClick={handleClose}
          className="absolute top-4 right-4 p-2 text-fc-text-muted hover:text-fc-text transition-colors"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Header */}
        <div className="flex items-center gap-3 mb-6">
          <div className="p-2 bg-success/10 rounded-xl">
            <TreePine className={`text-success ${bigMode ? 'w-7 h-7' : 'w-6 h-6'}`} />
          </div>
          <h2 className={`font-bold text-fc-text ${bigMode ? 'text-2xl' : 'text-xl'}`}>
            Secret Santa
          </h2>
        </div>

        {loading ? (
          <div className="flex justify-center py-12">
            <Loader2 className="w-8 h-8 animate-spin text-primary" />
          </div>
        ) : events.length === 0 ? (
          <div className="text-center py-8 text-fc-text-muted">
            <TreePine className="w-10 h-10 mx-auto mb-3 opacity-50" />
            <p>No events with Secret Santa enabled.</p>
            <p className="text-sm mt-1">Enable it when creating an event.</p>
          </div>
        ) : (
          <div className="overflow-y-auto flex-1 space-y-4">
            {/* Event Selector */}
            <div>
              <label className={`block text-fc-text mb-2 ${bigMode ? 'text-base' : 'text-sm'}`}>
                Select Event
              </label>
              <select
                value={selectedEventId || ''}
                onChange={(e) => setSelectedEventId(e.target.value)}
                className={`
                  w-full bg-fc-bg border border-fc-border rounded-xl
                  text-fc-text
                  focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent
                  ${bigMode ? 'px-4 py-3 text-base' : 'px-3 py-2 text-sm'}
                `}
              >
                {events.map((event) => (
                  <option key={event.id} value={event.id}>
                    {event.title} - {new Date(event.event_date).toLocaleDateString()}
                  </option>
                ))}
              </select>
            </div>

            {/* Status */}
            <div className="bg-fc-bg rounded-xl p-4">
              <h3 className={`font-medium text-fc-text mb-2 ${bigMode ? 'text-base' : 'text-sm'}`}>Status</h3>
              {status?.status === 'assigned' ? (
                <div className="flex items-center gap-2 text-success">
                  <Check className="w-5 h-5" />
                  <span className={bigMode ? 'text-base' : 'text-sm'}>
                    Assignments made ({status.participant_count} participants)
                  </span>
                </div>
              ) : (
                <div className="flex items-center gap-2 text-warning">
                  <AlertCircle className="w-5 h-5" />
                  <span className={bigMode ? 'text-base' : 'text-sm'}>No assignments yet</span>
                </div>
              )}
            </div>

            {/* Run Assignment */}
            <button
              onClick={handleRunAssignment}
              disabled={running}
              className={`
                w-full flex items-center justify-center gap-2
                bg-primary text-white rounded-xl
                hover:bg-primary-hover transition-colors
                disabled:opacity-50
                ${bigMode ? 'px-4 py-3 text-base' : 'px-3 py-2.5 text-sm'}
              `}
            >
              {running ? (
                <Loader2 className="w-5 h-5 animate-spin" />
              ) : (
                <Shuffle className="w-5 h-5" />
              )}
              {running ? 'Running...' : status?.status === 'assigned' ? 'Re-Run Assignment' : 'Run Assignment'}
            </button>

            {/* Budget */}
            <div className="bg-fc-bg rounded-xl p-4">
              <div className="flex items-center gap-2 mb-3">
                <DollarSign className="w-5 h-5 text-primary" />
                <h3 className={`font-medium text-fc-text ${bigMode ? 'text-base' : 'text-sm'}`}>
                  Gift Budget
                </h3>
              </div>
              <div className="grid grid-cols-2 gap-3 mb-3">
                <input
                  type="number"
                  value={budgetMin}
                  onChange={(e) => setBudgetMin(e.target.value)}
                  placeholder="Min $"
                  min="0"
                  className={`
                    w-full bg-fc-surface border border-fc-border rounded-lg
                    text-fc-text placeholder:text-fc-text-muted
                    focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent
                    ${bigMode ? 'px-3 py-2 text-base' : 'px-2 py-1.5 text-sm'}
                  `}
                />
                <input
                  type="number"
                  value={budgetMax}
                  onChange={(e) => setBudgetMax(e.target.value)}
                  placeholder="Max $"
                  min="0"
                  className={`
                    w-full bg-fc-surface border border-fc-border rounded-lg
                    text-fc-text placeholder:text-fc-text-muted
                    focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent
                    ${bigMode ? 'px-3 py-2 text-base' : 'px-2 py-1.5 text-sm'}
                  `}
                />
              </div>
              <textarea
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                placeholder="Additional notes..."
                rows={2}
                className={`
                  w-full bg-fc-surface border border-fc-border rounded-lg
                  text-fc-text placeholder:text-fc-text-muted resize-none mb-3
                  focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent
                  ${bigMode ? 'px-3 py-2 text-base' : 'px-2 py-1.5 text-sm'}
                `}
              />
              <button
                onClick={handleSaveRules}
                disabled={savingRules}
                className={`
                  flex items-center gap-2 text-primary hover:text-primary-hover transition-colors
                  ${bigMode ? 'text-base' : 'text-sm'}
                `}
              >
                {savingRules && <Loader2 className="w-4 h-4 animate-spin" />}
                Save Budget Rules
              </button>
            </div>

            {/* Exclusions */}
            <div className="bg-fc-bg rounded-xl p-4">
              <div className="flex items-center justify-between mb-3">
                <h3 className={`font-medium text-fc-text ${bigMode ? 'text-base' : 'text-sm'}`}>
                  Exclusions
                </h3>
                <button
                  onClick={() => setShowExclusionForm(!showExclusionForm)}
                  className="flex items-center gap-1 text-primary hover:text-primary-hover"
                >
                  <Plus className="w-4 h-4" />
                  <span className={bigMode ? 'text-sm' : 'text-xs'}>Add</span>
                </button>
              </div>

              {showExclusionForm && (
                <div className="bg-fc-surface rounded-lg p-3 mb-3 space-y-2">
                  <select
                    value={member1}
                    onChange={(e) => setMember1(e.target.value)}
                    className={`
                      w-full bg-fc-bg border border-fc-border rounded-lg
                      text-fc-text
                      ${bigMode ? 'px-3 py-2 text-sm' : 'px-2 py-1.5 text-xs'}
                    `}
                  >
                    <option value="">Select member 1...</option>
                    {members.map((m) => (
                      <option key={m.user_id} value={m.user_id}>{m.display_name}</option>
                    ))}
                  </select>
                  <select
                    value={member2}
                    onChange={(e) => setMember2(e.target.value)}
                    className={`
                      w-full bg-fc-bg border border-fc-border rounded-lg
                      text-fc-text
                      ${bigMode ? 'px-3 py-2 text-sm' : 'px-2 py-1.5 text-xs'}
                    `}
                  >
                    <option value="">Select member 2...</option>
                    {members.filter((m) => m.user_id !== member1).map((m) => (
                      <option key={m.user_id} value={m.user_id}>{m.display_name}</option>
                    ))}
                  </select>
                  <button
                    onClick={handleAddExclusion}
                    disabled={!member1 || !member2}
                    className={`
                      w-full bg-primary text-white rounded-lg
                      hover:bg-primary-hover transition-colors disabled:opacity-50
                      ${bigMode ? 'py-2 text-sm' : 'py-1.5 text-xs'}
                    `}
                  >
                    Add Exclusion
                  </button>
                </div>
              )}

              {exclusions.length > 0 ? (
                <div className="space-y-2">
                  {exclusions.map((exc) => (
                    <div
                      key={exc.id}
                      className="flex items-center justify-between bg-fc-surface rounded-lg p-2"
                    >
                      <span className={`text-fc-text ${bigMode ? 'text-sm' : 'text-xs'}`}>
                        {exc.user1_name} ↔ {exc.user2_name}
                      </span>
                      <button
                        onClick={() => handleRemoveExclusion(exc.id)}
                        className="text-fc-text-muted hover:text-error"
                      >
                        <UserX className="w-4 h-4" />
                      </button>
                    </div>
                  ))}
                </div>
              ) : (
                <p className={`text-fc-text-muted italic ${bigMode ? 'text-sm' : 'text-xs'}`}>
                  No exclusions set
                </p>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
