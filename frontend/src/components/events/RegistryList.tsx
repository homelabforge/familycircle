import { useEffect, useState } from 'react'
import {
  Gift, Plus, Trash2, Loader2, ExternalLink, ShoppingCart,
  Check, X, DollarSign,
} from 'lucide-react'
import { toast } from 'sonner'
import { useBigMode } from '@/contexts/BigModeContext'
import { useAuth } from '@/contexts/AuthContext'
import { registryApi, type RegistryItem, type RegistryStats } from '@/lib/api'

export default function RegistryList({
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
  const [items, setItems] = useState<RegistryItem[]>([])
  const [stats, setStats] = useState<RegistryStats>({ total: 0, claimed: 0, purchased: 0 })
  const [loading, setLoading] = useState(true)
  const [showAddForm, setShowAddForm] = useState(false)
  const [actionLoading, setActionLoading] = useState<string | null>(null)

  // Add form state
  const [newName, setNewName] = useState('')
  const [newUrl, setNewUrl] = useState('')
  const [newPrice, setNewPrice] = useState('')
  const [newNotes, setNewNotes] = useState('')
  const [addSaving, setAddSaving] = useState(false)

  const loadRegistry = async (): Promise<void> => {
    try {
      setLoading(true)
      const data = await registryApi.list(eventId)
      setItems(data.items)
      setStats(data.stats)
    } catch {
      // Non-critical
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadRegistry()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [eventId])

  const handleAdd = async (e: React.FormEvent): Promise<void> => {
    e.preventDefault()
    if (!newName.trim()) return

    try {
      setAddSaving(true)
      const item = await registryApi.create(eventId, {
        item_name: newName.trim(),
        item_url: newUrl.trim() || undefined,
        price: newPrice ? parseFloat(newPrice) : undefined,
        notes: newNotes.trim() || undefined,
      })
      setItems((prev) => [...prev, item])
      setStats((prev) => ({ ...prev, total: prev.total + 1 }))
      setNewName('')
      setNewUrl('')
      setNewPrice('')
      setNewNotes('')
      setShowAddForm(false)
      toast.success('Item added to registry')
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to add item')
    } finally {
      setAddSaving(false)
    }
  }

  const handleClaim = async (itemId: string): Promise<void> => {
    try {
      setActionLoading(itemId)
      const updated = await registryApi.claim(eventId, itemId)
      setItems((prev) => prev.map((i) => (i.id === itemId ? updated : i)))
      setStats((prev) => ({ ...prev, claimed: prev.claimed + 1 }))
      toast.success('Item claimed!')
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to claim item')
    } finally {
      setActionLoading(null)
    }
  }

  const handleUnclaim = async (itemId: string): Promise<void> => {
    try {
      setActionLoading(itemId)
      const updated = await registryApi.unclaim(eventId, itemId)
      setItems((prev) => prev.map((i) => (i.id === itemId ? updated : i)))
      setStats((prev) => ({ ...prev, claimed: prev.claimed - 1 }))
      toast.success('Claim released')
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to unclaim item')
    } finally {
      setActionLoading(null)
    }
  }

  const handlePurchase = async (itemId: string): Promise<void> => {
    try {
      setActionLoading(itemId)
      const updated = await registryApi.markPurchased(eventId, itemId)
      setItems((prev) => prev.map((i) => (i.id === itemId ? updated : i)))
      setStats((prev) => ({ ...prev, purchased: prev.purchased + 1 }))
      toast.success('Marked as purchased!')
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to mark as purchased')
    } finally {
      setActionLoading(null)
    }
  }

  const handleDelete = async (itemId: string): Promise<void> => {
    try {
      setActionLoading(itemId)
      await registryApi.delete(eventId, itemId)
      setItems((prev) => prev.filter((i) => i.id !== itemId))
      setStats((prev) => ({ ...prev, total: prev.total - 1 }))
      toast.success('Item removed')
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to delete item')
    } finally {
      setActionLoading(null)
    }
  }

  if (loading) {
    return (
      <div className="bg-fc-surface border border-fc-border rounded-2xl p-6 mb-6">
        <div className="flex items-center gap-3 mb-4">
          <Gift className="w-5 h-5 text-primary" />
          <h2 className={`font-semibold text-fc-text ${bigMode ? 'text-xl' : 'text-lg'}`}>
            Registry
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
          <Gift className="w-5 h-5 text-primary" />
          <h2 className={`font-semibold text-fc-text ${bigMode ? 'text-xl' : 'text-lg'}`}>
            Registry
          </h2>
          {stats.total > 0 && (
            <span className="text-xs text-fc-text-muted">
              {stats.claimed}/{stats.total} claimed, {stats.purchased} purchased
            </span>
          )}
        </div>
        {canManage && !isCancelled && (
          <button
            onClick={() => setShowAddForm(!showAddForm)}
            className={`flex items-center gap-1 text-primary hover:text-primary/80 transition-colors ${bigMode ? 'text-base' : 'text-sm'}`}
          >
            {showAddForm ? <X className="w-4 h-4" /> : <Plus className="w-4 h-4" />}
            {showAddForm ? 'Cancel' : 'Add Item'}
          </button>
        )}
      </div>

      {/* Add Form */}
      {showAddForm && (
        <form onSubmit={handleAdd} className="bg-fc-bg rounded-xl p-4 border border-fc-border mb-4 space-y-3">
          <input
            type="text"
            value={newName}
            onChange={(e) => setNewName(e.target.value)}
            className="w-full px-3 py-2 bg-fc-surface border border-fc-border rounded-lg text-fc-text text-sm focus:outline-none focus:ring-2 focus:ring-primary"
            placeholder="Item name *"
            required
          />
          <div className="grid grid-cols-2 gap-3">
            <input
              type="url"
              value={newUrl}
              onChange={(e) => setNewUrl(e.target.value)}
              className="w-full px-3 py-2 bg-fc-surface border border-fc-border rounded-lg text-fc-text text-sm focus:outline-none focus:ring-2 focus:ring-primary"
              placeholder="Product URL"
            />
            <input
              type="number"
              value={newPrice}
              onChange={(e) => setNewPrice(e.target.value)}
              className="w-full px-3 py-2 bg-fc-surface border border-fc-border rounded-lg text-fc-text text-sm focus:outline-none focus:ring-2 focus:ring-primary"
              placeholder="Price"
              step="0.01"
              min="0"
            />
          </div>
          <input
            type="text"
            value={newNotes}
            onChange={(e) => setNewNotes(e.target.value)}
            className="w-full px-3 py-2 bg-fc-surface border border-fc-border rounded-lg text-fc-text text-sm focus:outline-none focus:ring-2 focus:ring-primary"
            placeholder="Notes (color, size, etc.)"
          />
          <div className="flex justify-end">
            <button
              type="submit"
              disabled={addSaving}
              className="px-4 py-2 bg-primary text-white rounded-lg text-sm hover:bg-primary-hover transition-colors disabled:opacity-50 flex items-center gap-1"
            >
              {addSaving && <Loader2 className="w-3 h-3 animate-spin" />}
              Add
            </button>
          </div>
        </form>
      )}

      {items.length === 0 ? (
        <p className={`text-fc-text-muted ${bigMode ? 'text-base' : 'text-sm'}`}>
          No registry items yet.
        </p>
      ) : (
        <div className="space-y-3">
          {items.map((item) => {
            const isOwnClaim = item.claimed_by_id === user?.id
            const isLoading = actionLoading === item.id

            return (
              <div
                key={item.id}
                className={`
                  bg-fc-bg rounded-xl p-4 border transition-colors
                  ${item.is_purchased
                    ? 'border-success/30 opacity-75'
                    : item.is_claimed
                      ? 'border-primary/30'
                      : 'border-fc-border'
                  }
                `}
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className={`font-medium text-fc-text ${bigMode ? 'text-base' : 'text-sm'} ${item.is_purchased ? 'line-through' : ''}`}>
                        {item.item_name}
                      </span>
                      {item.price != null && (
                        <span className="flex items-center gap-0.5 text-xs text-fc-text-muted">
                          <DollarSign className="w-3 h-3" />
                          {item.price.toFixed(2)}
                        </span>
                      )}
                      {item.is_purchased && (
                        <span className="text-xs bg-success/10 text-success px-2 py-0.5 rounded-full">
                          Purchased
                        </span>
                      )}
                      {item.is_claimed && !item.is_purchased && (
                        <span className="text-xs bg-primary/10 text-primary px-2 py-0.5 rounded-full">
                          Claimed by {isOwnClaim ? 'you' : item.claimed_by_name}
                        </span>
                      )}
                    </div>
                    {item.notes && (
                      <p className="text-xs text-fc-text-muted mt-1">{item.notes}</p>
                    )}
                    {item.item_url && (
                      <a
                        href={item.item_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-1 text-xs text-primary hover:underline mt-1"
                      >
                        <ExternalLink className="w-3 h-3" />
                        View Product
                      </a>
                    )}
                  </div>

                  <div className="flex items-center gap-1 flex-shrink-0">
                    {/* Claim/Unclaim/Purchase actions */}
                    {!item.is_purchased && !item.is_claimed && !isCancelled && (
                      <button
                        onClick={() => handleClaim(item.id)}
                        disabled={isLoading}
                        className="px-3 py-1.5 text-xs bg-primary/10 text-primary rounded-lg hover:bg-primary/20 transition-colors disabled:opacity-50"
                        title="Claim this item"
                      >
                        {isLoading ? <Loader2 className="w-3 h-3 animate-spin" /> : 'Claim'}
                      </button>
                    )}
                    {item.is_claimed && isOwnClaim && !item.is_purchased && (
                      <>
                        <button
                          onClick={() => handlePurchase(item.id)}
                          disabled={isLoading}
                          className="px-2 py-1.5 text-xs bg-success/10 text-success rounded-lg hover:bg-success/20 transition-colors disabled:opacity-50"
                          title="Mark as purchased"
                        >
                          {isLoading ? <Loader2 className="w-3 h-3 animate-spin" /> : <ShoppingCart className="w-3.5 h-3.5" />}
                        </button>
                        <button
                          onClick={() => handleUnclaim(item.id)}
                          disabled={isLoading}
                          className="px-2 py-1.5 text-xs bg-fc-border text-fc-text-muted rounded-lg hover:bg-fc-border/80 transition-colors disabled:opacity-50"
                          title="Release claim"
                        >
                          <X className="w-3.5 h-3.5" />
                        </button>
                      </>
                    )}
                    {item.is_purchased && (
                      <Check className="w-4 h-4 text-success" />
                    )}
                    {canManage && (
                      <button
                        onClick={() => handleDelete(item.id)}
                        disabled={isLoading}
                        className="p-1.5 text-fc-text-muted hover:text-error transition-colors disabled:opacity-50"
                        title="Delete item"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    )}
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
