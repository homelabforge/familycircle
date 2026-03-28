import { useState } from 'react'
import { Gift, Plus, Trash2, ExternalLink, Edit2, Loader2, X } from 'lucide-react'
import { useQueryClient } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import BackButton from '@/components/BackButton'
import { useBigMode } from '@/contexts/BigModeContext'
import { useWishlist } from '@/hooks/queries/useWishlist'
import { wishlistApi, type WishlistItem } from '@/lib/api'
import { wishlistItemSchema } from '@/lib/schemas'
interface WishlistFormValues {
  name: string
  description?: string
  url?: string
  price_range?: '' | '$' | '$$' | '$$$'
  priority: number
}

export default function Wishlist() {
  const { bigMode } = useBigMode()
  const queryClient = useQueryClient()
  const { data, isLoading: loading, error: queryError } = useWishlist()
  const items = data?.items ?? []
  const error = queryError ? (queryError instanceof Error ? queryError.message : 'Failed to load wishlist') : null
  const [showAddModal, setShowAddModal] = useState(false)
  const [editingItem, setEditingItem] = useState<WishlistItem | null>(null)

  const handleDelete = async (id: string) => {
    if (!confirm('Remove this item from your wishlist?')) return
    try {
      await wishlistApi.delete(id)
      queryClient.invalidateQueries({ queryKey: ['wishlist'] })
    } catch {
      // Error handled by query refetch
    }
  }

  const getPriorityLabel = (priority: number) => {
    switch (priority) {
      case 1:
        return 'Most wanted'
      case 2:
        return 'High'
      case 3:
        return 'Medium'
      case 4:
        return 'Low'
      case 5:
        return 'Nice to have'
      default:
        return ''
    }
  }

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-6">
        <BackButton />
        <div className="flex items-center justify-center py-12">
          <Loader2 className="w-8 h-8 animate-spin text-primary" />
        </div>
      </div>
    )
  }

  return (
    <div className="container mx-auto px-4 py-6">
      <BackButton />

      <div className="mt-4">
        <h1
          className={`
            flex items-center gap-3 font-bold text-fc-text mb-6
            ${bigMode ? 'text-3xl' : 'text-2xl'}
          `}
        >
          <Gift className={bigMode ? 'w-9 h-9' : 'w-7 h-7'} />
          My Wishlist
        </h1>

        <p className={`text-fc-text-muted mb-6 ${bigMode ? 'text-lg' : ''}`}>
          Add items you'd like to receive. Your Gift Exchange match will see this list!
        </p>

        {error && (
          <div className="bg-error/10 text-error px-4 py-3 rounded-xl mb-6">
            {error}
          </div>
        )}

        {/* Add Item Button */}
        <button
          onClick={() => setShowAddModal(true)}
          className={`
            w-full flex items-center justify-center gap-2
            bg-primary text-white rounded-xl
            hover:bg-primary-hover transition-colors mb-6
            ${bigMode ? 'px-6 py-4 text-lg' : 'px-4 py-3'}
          `}
        >
          <Plus className={bigMode ? 'w-6 h-6' : 'w-5 h-5'} />
          Add New Item
        </button>

        {/* Wishlist Items */}
        <div className="space-y-4">
          {items.map((item) => (
            <div
              key={item.id}
              className={`
                bg-fc-surface border border-fc-border rounded-xl
                ${bigMode ? 'p-5' : 'p-4'}
              `}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <h3
                      className={`
                        font-medium text-fc-text
                        ${bigMode ? 'text-lg' : ''}
                      `}
                    >
                      {item.name}
                    </h3>
                    {item.priority && item.priority <= 2 && (
                      <span className="text-xs bg-primary/10 text-primary px-2 py-0.5 rounded-full">
                        {getPriorityLabel(item.priority)}
                      </span>
                    )}
                  </div>
                  {item.description && (
                    <p className={`text-fc-text-muted mt-1 ${bigMode ? 'text-base' : 'text-sm'}`}>
                      {item.description}
                    </p>
                  )}
                  {item.price_range && (
                    <p className={`text-fc-text-muted mt-1 ${bigMode ? 'text-base' : 'text-sm'}`}>
                      Price: {item.price_range}
                    </p>
                  )}
                  {item.url && (
                    <a
                      href={item.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className={`
                        inline-flex items-center gap-1 text-primary hover:text-primary-hover mt-2
                        ${bigMode ? 'text-base' : 'text-sm'}
                      `}
                    >
                      <ExternalLink className="w-4 h-4" />
                      View Link
                    </a>
                  )}
                </div>
                <div className="flex gap-1">
                  <button
                    onClick={() => setEditingItem(item)}
                    className="p-2 text-fc-text-muted hover:text-primary transition-colors"
                    title="Edit item"
                  >
                    <Edit2 className={bigMode ? 'w-6 h-6' : 'w-5 h-5'} />
                  </button>
                  <button
                    onClick={() => handleDelete(item.id)}
                    className="p-2 text-fc-text-muted hover:text-error transition-colors"
                    title="Remove item"
                  >
                    <Trash2 className={bigMode ? 'w-6 h-6' : 'w-5 h-5'} />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>

        {items.length === 0 && !error && (
          <div className="text-center py-12">
            <Gift className="w-16 h-16 text-fc-text-muted mx-auto mb-4" />
            <p className={`text-fc-text-muted ${bigMode ? 'text-lg' : ''}`}>
              Your wishlist is empty. Add some items!
            </p>
          </div>
        )}
      </div>

      {/* Add/Edit Modal */}
      {(showAddModal || editingItem) && (
        <WishlistModal
          item={editingItem}
          onClose={() => {
            setShowAddModal(false)
            setEditingItem(null)
          }}
          onSave={async (data) => {
            if (editingItem) {
              await wishlistApi.update(editingItem.id, data)
            } else {
              await wishlistApi.add(data)
            }
            queryClient.invalidateQueries({ queryKey: ['wishlist'] })
            setShowAddModal(false)
            setEditingItem(null)
          }}
          bigMode={bigMode}
        />
      )}
    </div>
  )
}

interface WishlistModalProps {
  item: WishlistItem | null
  onClose: () => void
  onSave: (data: {
    name: string
    description?: string
    url?: string
    price_range?: string
    priority?: number
  }) => Promise<void>
  bigMode: boolean
}

function WishlistModal({ item, onClose, onSave, bigMode }: WishlistModalProps) {
  const [error, setError] = useState<string | null>(null)

  const {
    watch,
    setValue,
    handleSubmit,
    formState: { errors, isSubmitting, isSubmitted },
  } = useForm<WishlistFormValues>({
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    resolver: zodResolver(wishlistItemSchema) as any,
    defaultValues: {
      name: item?.name || '',
      description: item?.description || '',
      url: item?.url || '',
      price_range: (item?.price_range as '' | '$' | '$$' | '$$$' | undefined) ?? '',
      priority: item?.priority || 3,
    },
  })

  const values = watch()

  const onSubmit = handleSubmit(async (data: WishlistFormValues) => {
    try {
      setError(null)
      await onSave({
        name: data.name,
        description: data.description,
        url: data.url,
        price_range: data.price_range,
        priority: data.priority,
      })
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save')
    }
  })

  const inputClass = `
    w-full bg-fc-bg border border-fc-border rounded-xl text-fc-text
    placeholder:text-fc-text-muted focus:outline-none focus:ring-2 focus:ring-primary
    ${bigMode ? 'px-4 py-3 text-lg' : 'px-3 py-2'}
  `

  const inputErrorClass = `
    w-full bg-fc-bg border border-error rounded-xl text-fc-text
    placeholder:text-fc-text-muted focus:outline-none focus:ring-2 focus:ring-error
    ${bigMode ? 'px-4 py-3 text-lg' : 'px-3 py-2'}
  `

  const errorTextClass = `text-error ${bigMode ? 'text-sm' : 'text-xs'} mt-1`

  // Helper: show error only after form submission
  const fieldError = (field: string): string | undefined => {
    return isSubmitted ? (errors as Record<string, { message?: string } | undefined>)[field]?.message : undefined
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
      <div
        className={`
          bg-fc-surface rounded-2xl w-full max-w-md max-h-[90vh] overflow-y-auto
          ${bigMode ? 'p-6' : 'p-5'}
        `}
      >
        <div className="flex items-center justify-between mb-4">
          <h2
            className={`
              font-semibold text-fc-text
              ${bigMode ? 'text-xl' : 'text-lg'}
            `}
          >
            {item ? 'Edit Item' : 'Add New Item'}
          </h2>
          <button onClick={onClose} className="p-1 text-fc-text-muted hover:text-fc-text">
            <X className="w-5 h-5" />
          </button>
        </div>

        {error && (
          <div className="bg-error/10 text-error px-4 py-3 rounded-xl mb-4 text-sm">
            {error}
          </div>
        )}

        <form onSubmit={onSubmit} className="space-y-4">
          <div>
            <label className={`block text-fc-text mb-2 ${bigMode ? 'text-base' : 'text-sm'}`}>
              Item Name <span className="text-error">*</span>
            </label>
            <input
              type="text"
              value={values.name}
              onChange={(e) => setValue('name', e.target.value)}
              placeholder="What would you like?"
              className={fieldError('name') ? inputErrorClass : inputClass}
            />
            {fieldError('name') && (
              <p className={errorTextClass}>{fieldError('name')}</p>
            )}
          </div>

          <div>
            <label className={`block text-fc-text mb-2 ${bigMode ? 'text-base' : 'text-sm'}`}>
              Description/Notes
            </label>
            <textarea
              value={values.description || ''}
              onChange={(e) => setValue('description', e.target.value)}
              placeholder="Size, color, brand preference, etc."
              rows={2}
              className={`${inputClass} resize-none`}
            />
          </div>

          <div>
            <label className={`block text-fc-text mb-2 ${bigMode ? 'text-base' : 'text-sm'}`}>
              Link (optional)
            </label>
            <input
              type="url"
              value={values.url || ''}
              onChange={(e) => setValue('url', e.target.value)}
              placeholder="https://..."
              className={fieldError('url') ? inputErrorClass : inputClass}
            />
            {fieldError('url') && (
              <p className={errorTextClass}>{fieldError('url')}</p>
            )}
          </div>

          <div>
            <label className={`block text-fc-text mb-2 ${bigMode ? 'text-base' : 'text-sm'}`}>
              Price Range
            </label>
            <select
              value={values.price_range || ''}
              onChange={(e) => setValue('price_range', (e.target.value || undefined) as '' | '$' | '$$' | '$$$' | undefined)}
              className={inputClass}
            >
              <option value="">Not specified</option>
              <option value="$">$ (Under $25)</option>
              <option value="$$">$$ ($25-$50)</option>
              <option value="$$$">$$$ ($50+)</option>
            </select>
          </div>

          <div>
            <label className={`block text-fc-text mb-2 ${bigMode ? 'text-base' : 'text-sm'}`}>
              Priority
            </label>
            <select
              value={values.priority}
              onChange={(e) => setValue('priority', Number(e.target.value))}
              className={inputClass}
            >
              <option value={1}>Most wanted</option>
              <option value={2}>High</option>
              <option value={3}>Medium</option>
              <option value={4}>Low</option>
              <option value={5}>Nice to have</option>
            </select>
          </div>

          <div className="flex gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className={`
                flex-1 border border-fc-border text-fc-text rounded-xl
                hover:bg-fc-surface-hover transition-colors
                ${bigMode ? 'px-4 py-3 text-lg' : 'px-3 py-2'}
              `}
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className={`
                flex-1 bg-primary text-white rounded-xl
                hover:bg-primary-hover transition-colors
                disabled:opacity-50 disabled:cursor-not-allowed
                ${bigMode ? 'px-4 py-3 text-lg' : 'px-3 py-2'}
              `}
            >
              {isSubmitting ? 'Saving...' : item ? 'Update' : 'Add'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
