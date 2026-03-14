import { useQuery } from '@tanstack/react-query'
import { wishlistApi } from '@/lib/api'

export function useWishlist() {
  return useQuery({
    queryKey: ['wishlist'],
    queryFn: () => wishlistApi.get(),
  })
}

export function useUserWishlist(userId: string) {
  return useQuery({
    queryKey: ['wishlist', userId],
    queryFn: () => wishlistApi.getUserWishlist(userId),
    enabled: !!userId,
  })
}
