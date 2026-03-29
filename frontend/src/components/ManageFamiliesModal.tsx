import { useEffect, useState } from 'react'
import { List, Trash2, Loader2, Users, X } from 'lucide-react'
import { toast } from 'sonner'
import { useBigMode } from '@/contexts/BigModeContext'
import { useAuth } from '@/contexts/AuthContext'
import { authApi, type AdminFamilyInfo } from '@/lib/api'

interface ManageFamiliesModalProps {
  isOpen: boolean
  onClose: () => void
}

export default function ManageFamiliesModal({ isOpen, onClose }: ManageFamiliesModalProps) {
  const { bigMode } = useBigMode()
  const { user, deleteFamily } = useAuth()
  const [families, setFamilies] = useState<AdminFamilyInfo[]>([])
  const [loading, setLoading] = useState(true)
  const [deleteConfirm, setDeleteConfirm] = useState<string | null>(null)
  const [deleting, setDeleting] = useState(false)

  useEffect(() => {
    if (isOpen) {
      loadFamilies()
    }
  }, [isOpen])

  const loadFamilies = async () => {
    try {
      setLoading(true)
      const res = await authApi.listAllFamilies()
      setFamilies(res.families)
    } catch {
      toast.error('Failed to load families')
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = async (familyId: string) => {
    try {
      setDeleting(true)
      await deleteFamily(familyId)
      toast.success('Family deleted')
      setDeleteConfirm(null)
      await loadFamilies()
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to delete family', { duration: 6000 })
    } finally {
      setDeleting(false)
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
            <List className={`text-primary ${bigMode ? 'w-7 h-7' : 'w-6 h-6'}`} />
          </div>
          <h2 className={`font-bold text-fc-text ${bigMode ? 'text-2xl' : 'text-xl'}`}>
            Manage Families
          </h2>
        </div>

        {loading ? (
          <div className="flex justify-center py-12">
            <Loader2 className="w-8 h-8 animate-spin text-primary" />
          </div>
        ) : (
          <div className="overflow-y-auto flex-1 space-y-2">
            {families.length === 0 ? (
              <p className="text-fc-text-muted text-center py-8">No families found.</p>
            ) : (
              families.map((family) => {
                const isActive = family.id === user?.current_family_id

                return (
                  <div
                    key={family.id}
                    className={`
                      flex items-center justify-between
                      bg-fc-bg rounded-xl
                      ${isActive ? 'ring-2 ring-primary/30' : ''}
                      ${bigMode ? 'p-4' : 'p-3'}
                    `}
                  >
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className={`font-medium text-fc-text truncate ${bigMode ? 'text-base' : 'text-sm'}`}>
                          {family.name}
                        </span>
                        {isActive && (
                          <span className="text-xs bg-primary/10 text-primary px-1.5 py-0.5 rounded shrink-0">
                            Active
                          </span>
                        )}
                      </div>
                      <div className={`flex items-center gap-3 text-fc-text-muted ${bigMode ? 'text-sm' : 'text-xs'}`}>
                        <span className="flex items-center gap-1">
                          <Users className="w-3 h-3" />
                          {family.member_count} {family.member_count === 1 ? 'member' : 'members'}
                        </span>
                        <span className="font-mono">{family.family_code}</span>
                      </div>
                    </div>
                    <div className="flex items-center gap-1 shrink-0 ml-2">
                      {deleteConfirm === family.id ? (
                        <div className="flex items-center gap-1">
                          <button
                            onClick={() => handleDelete(family.id)}
                            disabled={deleting}
                            className="px-2 py-1 text-xs bg-error text-white rounded disabled:opacity-50"
                          >
                            {deleting ? 'Deleting...' : 'Yes'}
                          </button>
                          <button
                            onClick={() => setDeleteConfirm(null)}
                            disabled={deleting}
                            className="px-2 py-1 text-xs border border-fc-border rounded disabled:opacity-50"
                          >
                            No
                          </button>
                        </div>
                      ) : (
                        <button
                          onClick={() => setDeleteConfirm(family.id)}
                          className="p-1.5 text-fc-text-muted hover:text-error transition-colors"
                          title="Delete family"
                        >
                          <Trash2 className={bigMode ? 'w-5 h-5' : 'w-4 h-4'} />
                        </button>
                      )}
                    </div>
                  </div>
                )
              })
            )}
          </div>
        )}
      </div>
    </div>
  )
}
