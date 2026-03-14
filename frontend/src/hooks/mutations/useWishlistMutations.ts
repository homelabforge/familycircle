import { useMutation, useQueryClient } from '@tanstack/react-query'
import { wishlistApi } from '@/lib/api'

export function useAddWishlistItem() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: wishlistApi.add,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['wishlist'] })
    },
  })
}

export function useUpdateWishlistItem() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Parameters<typeof wishlistApi.update>[1] }) =>
      wishlistApi.update(id, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['wishlist'] })
    },
  })
}

export function useDeleteWishlistItem() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: wishlistApi.delete,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['wishlist'] })
    },
  })
}
