import { useEffect, useState } from 'react'
import { Users, Mail, Crown, Trash2, Copy, Loader2, Check, X } from 'lucide-react'
import { toast } from 'sonner'
import { useBigMode } from '@/contexts/BigModeContext'
import { useAuth } from '@/contexts/AuthContext'
import { familyApi, settingsApi, type FamilyMember } from '@/lib/api'

interface FamilyMembersModalProps {
  isOpen: boolean
  onClose: () => void
}

export default function FamilyMembersModal({ isOpen, onClose }: FamilyMembersModalProps) {
  const { bigMode } = useBigMode()
  const { user } = useAuth()
  const [members, setMembers] = useState<FamilyMember[]>([])
  const [familyCode, setFamilyCode] = useState('')
  const [loading, setLoading] = useState(true)
  const [inviteEmail, setInviteEmail] = useState('')
  const [inviteName, setInviteName] = useState('')
  const [inviting, setInviting] = useState(false)
  const [copied, setCopied] = useState(false)
  const [deleteConfirm, setDeleteConfirm] = useState<string | null>(null)

  useEffect(() => {
    if (isOpen) {
      loadData()
    }
  }, [isOpen])

  const loadData = async () => {
    try {
      setLoading(true)
      const [membersRes, codeRes] = await Promise.all([
        familyApi.listMembers(),
        settingsApi.getFamilyCode(),
      ])
      setMembers(membersRes.members)
      setFamilyCode(codeRes.code)
    } catch (err) {
      toast.error('Failed to load data')
    } finally {
      setLoading(false)
    }
  }

  const handleCopyCode = async () => {
    try {
      // Try modern clipboard API first
      if (navigator.clipboard && window.isSecureContext) {
        await navigator.clipboard.writeText(familyCode)
      } else {
        // Fallback for non-HTTPS contexts
        const textArea = document.createElement('textarea')
        textArea.value = familyCode
        textArea.style.position = 'fixed'
        textArea.style.left = '-999999px'
        textArea.style.top = '-999999px'
        document.body.appendChild(textArea)
        textArea.focus()
        textArea.select()
        document.execCommand('copy')
        document.body.removeChild(textArea)
      }
      setCopied(true)
      toast.success('Code copied to clipboard')
      setTimeout(() => setCopied(false), 2000)
    } catch (err) {
      toast.error('Failed to copy code')
    }
  }

  const handleInvite = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!inviteEmail.trim() || !inviteName.trim()) {
      toast.error('Name and email are required')
      return
    }

    try {
      setInviting(true)
      const res = await familyApi.invite({ name: inviteName.trim(), email: inviteEmail.trim() })
      toast.success('Invitation sent!')

      // In dev mode, show the magic link token
      if (res.dev_token) {
        console.log('Dev magic link token:', res.dev_token)
        toast.info(`Dev token: ${res.dev_token.slice(0, 20)}...`, { duration: 10000 })
      }

      setInviteEmail('')
      setInviteName('')
      await loadData()
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to send invitation')
    } finally {
      setInviting(false)
    }
  }

  const handleToggleRole = async (member: FamilyMember) => {
    const newRole = member.role === 'admin' ? 'member' : 'admin'
    try {
      await familyApi.setRole(member.user_id, newRole)
      toast.success(
        newRole === 'admin'
          ? `${member.display_name} is now an admin`
          : `${member.display_name} is no longer an admin`
      )
      await loadData()
    } catch (err) {
      toast.error('Failed to update role')
    }
  }

  const handleRemoveMember = async (userId: string) => {
    try {
      await familyApi.removeMember(userId)
      toast.success('Member removed')
      setDeleteConfirm(null)
      await loadData()
    } catch (err) {
      toast.error('Failed to remove member')
    }
  }

  const handleClose = () => {
    setDeleteConfirm(null)
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
          <div className="p-2 bg-primary/10 rounded-xl">
            <Users className={`text-primary ${bigMode ? 'w-7 h-7' : 'w-6 h-6'}`} />
          </div>
          <h2 className={`font-bold text-fc-text ${bigMode ? 'text-2xl' : 'text-xl'}`}>
            Family Members
          </h2>
        </div>

        {loading ? (
          <div className="flex justify-center py-12">
            <Loader2 className="w-8 h-8 animate-spin text-primary" />
          </div>
        ) : (
          <div className="overflow-y-auto flex-1 space-y-4">
            {/* Family Code */}
            <div className="bg-fc-bg rounded-xl p-4">
              <h3 className={`font-medium text-fc-text mb-2 ${bigMode ? 'text-base' : 'text-sm'}`}>
                Family Join Code
              </h3>
              <p className={`text-fc-text-muted mb-3 ${bigMode ? 'text-sm' : 'text-xs'}`}>
                Share this code with family members to let them join.
              </p>
              <div className="flex items-center gap-3">
                <code
                  className={`
                    bg-fc-surface border border-fc-border rounded-lg px-4 py-2
                    font-mono font-bold text-primary
                    ${bigMode ? 'text-xl' : 'text-lg'}
                  `}
                >
                  {familyCode}
                </code>
                <button
                  onClick={handleCopyCode}
                  className="p-2 text-fc-text-muted hover:text-primary transition-colors"
                  title="Copy code"
                >
                  {copied ? (
                    <Check className={bigMode ? 'w-5 h-5' : 'w-4 h-4'} />
                  ) : (
                    <Copy className={bigMode ? 'w-5 h-5' : 'w-4 h-4'} />
                  )}
                </button>
              </div>
            </div>

            {/* Invite by Email */}
            <div className="bg-fc-bg rounded-xl p-4">
              <h3 className={`font-medium text-fc-text mb-2 ${bigMode ? 'text-base' : 'text-sm'}`}>
                Invite by Email
              </h3>
              <form onSubmit={handleInvite} className="space-y-2">
                <input
                  type="text"
                  value={inviteName}
                  onChange={(e) => setInviteName(e.target.value)}
                  placeholder="Name (e.g., Uncle Bob)"
                  className={`
                    w-full bg-fc-surface border border-fc-border rounded-lg
                    text-fc-text placeholder:text-fc-text-muted
                    focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent
                    ${bigMode ? 'px-4 py-3 text-base' : 'px-3 py-2 text-sm'}
                  `}
                />
                <div className="flex gap-2">
                  <input
                    type="email"
                    value={inviteEmail}
                    onChange={(e) => setInviteEmail(e.target.value)}
                    placeholder="Email address"
                    className={`
                      flex-1 bg-fc-surface border border-fc-border rounded-lg
                      text-fc-text placeholder:text-fc-text-muted
                      focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent
                      ${bigMode ? 'px-4 py-3 text-base' : 'px-3 py-2 text-sm'}
                    `}
                  />
                  <button
                    type="submit"
                    disabled={inviting}
                    className={`
                      flex items-center justify-center gap-2
                      bg-primary text-white rounded-lg
                      hover:bg-primary-hover transition-colors
                      disabled:opacity-50
                      ${bigMode ? 'px-4 py-3 text-base' : 'px-3 py-2 text-sm'}
                    `}
                  >
                    {inviting ? (
                      <Loader2 className="w-4 h-4 animate-spin" />
                    ) : (
                      <Mail className={bigMode ? 'w-5 h-5' : 'w-4 h-4'} />
                    )}
                    Invite
                  </button>
                </div>
              </form>
            </div>

            {/* Members List */}
            <div>
              <h3 className={`font-medium text-fc-text mb-3 ${bigMode ? 'text-base' : 'text-sm'}`}>
                Current Members ({members.length})
              </h3>
              <div className="space-y-2">
                {members.map((member) => {
                  const initials = member.display_name
                    ? member.display_name
                        .split(' ')
                        .map((n: string) => n[0])
                        .join('')
                        .toUpperCase()
                        .slice(0, 2)
                    : '?'
                  const isCurrentUser = member.user_id === user?.id
                  const isAdmin = member.role === 'admin'

                  return (
                    <div
                      key={member.user_id}
                      className={`
                        flex items-center justify-between
                        bg-fc-bg rounded-xl
                        ${bigMode ? 'p-3' : 'p-2'}
                      `}
                    >
                      <div className="flex items-center gap-3">
                        <div
                          className={`
                            flex items-center justify-center
                            bg-primary/10 rounded-full font-bold text-primary
                            ${bigMode ? 'w-10 h-10 text-base' : 'w-8 h-8 text-sm'}
                          `}
                        >
                          {initials}
                        </div>
                        <div>
                          <div className="flex items-center gap-2">
                            <span className={`font-medium text-fc-text ${bigMode ? 'text-base' : 'text-sm'}`}>
                              {member.display_name}
                            </span>
                            {isAdmin && (
                              <Crown className="w-3.5 h-3.5 text-warning" aria-label="Admin" />
                            )}
                            {isCurrentUser && (
                              <span className="text-xs bg-primary/10 text-primary px-1.5 py-0.5 rounded">
                                You
                              </span>
                            )}
                          </div>
                          <span className={`text-fc-text-muted ${bigMode ? 'text-sm' : 'text-xs'}`}>
                            {member.email || 'No email'}
                          </span>
                        </div>
                      </div>
                      <div className="flex gap-1">
                        {!isCurrentUser && (
                          <>
                            <button
                              onClick={() => handleToggleRole(member)}
                              className={`p-1.5 transition-colors ${
                                isAdmin
                                  ? 'text-warning hover:text-warning/70'
                                  : 'text-fc-text-muted hover:text-warning'
                              }`}
                              title={isAdmin ? 'Remove admin' : 'Make admin'}
                            >
                              <Crown className={bigMode ? 'w-5 h-5' : 'w-4 h-4'} />
                            </button>
                            {deleteConfirm === member.user_id ? (
                              <div className="flex items-center gap-1">
                                <button
                                  onClick={() => handleRemoveMember(member.user_id)}
                                  className="px-2 py-1 text-xs bg-error text-white rounded"
                                >
                                  Yes
                                </button>
                                <button
                                  onClick={() => setDeleteConfirm(null)}
                                  className="px-2 py-1 text-xs border border-fc-border rounded"
                                >
                                  No
                                </button>
                              </div>
                            ) : (
                              <button
                                onClick={() => setDeleteConfirm(member.user_id)}
                                className="p-1.5 text-fc-text-muted hover:text-error transition-colors"
                                title="Remove member"
                              >
                                <Trash2 className={bigMode ? 'w-5 h-5' : 'w-4 h-4'} />
                              </button>
                            )}
                          </>
                        )}
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
