import { api } from './client'
import type { WishlistItem } from './types'

export const wishlistApi = {
  get: () => api.get<{ items: WishlistItem[] }>('/wishlist'),

  add: (data: {
    name: string
    description?: string
    url?: string
    price_range?: string
    priority?: number
  }) => api.post<{ message: string; id: string; item: WishlistItem }>('/wishlist', data),

  update: (id: string, data: Partial<WishlistItem>) =>
    api.put<{ message: string; item: WishlistItem }>(`/wishlist/${id}`, data),

  delete: (id: string) => api.delete<{ message: string }>(`/wishlist/${id}`),

  getUserWishlist: (userId: string) =>
    api.get<{ user_id: string; display_name?: string; items: WishlistItem[] }>(
      `/wishlist/user/${userId}`
    ),

  // Legacy alias
  getMemberWishlist: (memberId: string) =>
    api.get<{ user_id: string; display_name?: string; items: WishlistItem[] }>(
      `/wishlist/member/${memberId}`
    ),
}
