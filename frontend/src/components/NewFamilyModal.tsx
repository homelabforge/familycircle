import { useState } from 'react'
import { X, Loader2, Users, Copy, Check } from 'lucide-react'
import { toast } from 'sonner'
import { useBigMode } from '@/contexts/BigModeContext'
import { useAuth } from '@/contexts/AuthContext'

interface NewFamilyModalProps {
  isOpen: boolean
  onClose: () => void
}

export default function NewFamilyModal({ isOpen, onClose }: NewFamilyModalProps) {
  const { bigMode } = useBigMode()
  const { createFamily, switchFamily, families } = useAuth()
  const [familyName, setFamilyName] = useState('')
  const [displayName, setDisplayName] = useState('')
  const [creating, setCreating] = useState(false)
  const [createdCode, setCreatedCode] = useState<string | null>(null)
  const [copied, setCopied] = useState(false)

  if (!isOpen) return null

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!familyName.trim()) {
      toast.error('Family name is required')
      return
    }
    if (!displayName.trim()) {
      toast.error('Your display name is required')
      return
    }

    try {
      setCreating(true)
      const { familyCode } = await createFamily(familyName.trim(), displayName.trim())
      setCreatedCode(familyCode)
      toast.success(`Family "${familyName}" created!`)
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to create family')
    } finally {
      setCreating(false)
    }
  }

  const handleCopyCode = async () => {
    if (!createdCode) return
    try {
      await navigator.clipboard.writeText(createdCode)
      setCopied(true)
      toast.success('Code copied to clipboard')
      setTimeout(() => setCopied(false), 2000)
    } catch {
      toast.error('Failed to copy code')
    }
  }

  const handleSwitchToNew = async () => {
    // Find the newly created family in the updated families list
    const newFamily = families.find(f => f.name === familyName.trim())
    if (newFamily) {
      await switchFamily(newFamily.id)
      toast.success(`Switched to ${newFamily.name}`)
    }
    handleClose()
  }

  const handleClose = () => {
    setFamilyName('')
    setDisplayName('')
    setCreatedCode(null)
    setCopied(false)
    onClose()
  }

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
          w-full max-w-md mx-4 shadow-xl
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
            Create New Family
          </h2>
        </div>

        {!createdCode ? (
          <form onSubmit={handleCreate} className="space-y-4">
            <div>
              <label
                className={`block text-fc-text font-medium mb-2 ${bigMode ? 'text-lg' : ''}`}
              >
                Family Name
              </label>
              <input
                type="text"
                value={familyName}
                onChange={(e) => setFamilyName(e.target.value)}
                placeholder="e.g., The Smiths, Johnson Family"
                className={`
                  w-full bg-fc-bg border border-fc-border rounded-xl
                  text-fc-text placeholder:text-fc-text-muted
                  focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent
                  ${bigMode ? 'px-5 py-4 text-lg' : 'px-4 py-3'}
                `}
                autoFocus
              />
            </div>

            <div>
              <label
                className={`block text-fc-text font-medium mb-2 ${bigMode ? 'text-lg' : ''}`}
              >
                Your Display Name
              </label>
              <p className={`text-fc-text-muted mb-2 ${bigMode ? 'text-base' : 'text-sm'}`}>
                How you'll appear in this family (can be different from other families)
              </p>
              <input
                type="text"
                value={displayName}
                onChange={(e) => setDisplayName(e.target.value)}
                placeholder="e.g., Mom, Dad, Grandma Alice"
                className={`
                  w-full bg-fc-bg border border-fc-border rounded-xl
                  text-fc-text placeholder:text-fc-text-muted
                  focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent
                  ${bigMode ? 'px-5 py-4 text-lg' : 'px-4 py-3'}
                `}
              />
            </div>

            <button
              type="submit"
              disabled={creating}
              className={`
                w-full flex items-center justify-center gap-2
                bg-primary text-white rounded-xl
                hover:bg-primary-hover transition-colors
                disabled:opacity-50
                ${bigMode ? 'px-6 py-4 text-lg font-semibold' : 'px-4 py-3 font-medium'}
              `}
            >
              {creating ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  Creating...
                </>
              ) : (
                'Create Family'
              )}
            </button>
          </form>
        ) : (
          <div className="space-y-6">
            <div className="text-center">
              <div className="w-16 h-16 bg-success/10 rounded-full flex items-center justify-center mx-auto mb-4">
                <Check className="w-8 h-8 text-success" />
              </div>
              <p className={`text-fc-text ${bigMode ? 'text-lg' : ''}`}>
                Family created successfully!
              </p>
            </div>

            <div className="bg-fc-bg rounded-xl p-4">
              <p className={`text-fc-text-muted mb-2 ${bigMode ? 'text-base' : 'text-sm'}`}>
                Share this code with family members:
              </p>
              <div className="flex items-center gap-3">
                <code
                  className={`
                    flex-1 bg-fc-surface border border-fc-border rounded-lg px-4 py-2
                    font-mono font-bold text-primary text-center
                    ${bigMode ? 'text-2xl' : 'text-xl'}
                  `}
                >
                  {createdCode}
                </code>
                <button
                  onClick={handleCopyCode}
                  className="p-3 text-fc-text-muted hover:text-primary transition-colors"
                  title="Copy code"
                >
                  {copied ? (
                    <Check className={bigMode ? 'w-6 h-6' : 'w-5 h-5'} />
                  ) : (
                    <Copy className={bigMode ? 'w-6 h-6' : 'w-5 h-5'} />
                  )}
                </button>
              </div>
            </div>

            <div className="flex gap-3">
              <button
                onClick={handleClose}
                className={`
                  flex-1 border border-fc-border rounded-xl
                  text-fc-text hover:bg-fc-bg transition-colors
                  ${bigMode ? 'px-6 py-4 text-lg' : 'px-4 py-3'}
                `}
              >
                Stay Here
              </button>
              <button
                onClick={handleSwitchToNew}
                className={`
                  flex-1 bg-primary text-white rounded-xl
                  hover:bg-primary-hover transition-colors
                  ${bigMode ? 'px-6 py-4 text-lg' : 'px-4 py-3'}
                `}
              >
                Switch to New Family
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
