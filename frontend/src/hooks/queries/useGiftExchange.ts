import { useQuery } from '@tanstack/react-query'
import { giftExchangeApi } from '@/lib/api'

export function useGiftExchangeStatus(eventId: string) {
  return useQuery({
    queryKey: ['giftExchange', 'status', eventId],
    queryFn: () => giftExchangeApi.getStatus(eventId),
    enabled: !!eventId,
  })
}

export function useGiftExchangeAssignment(eventId: string) {
  return useQuery({
    queryKey: ['giftExchange', 'assignment', eventId],
    queryFn: () => giftExchangeApi.getAssignment(eventId),
    enabled: !!eventId,
  })
}

export function useGiftExchangeMessages(eventId: string) {
  return useQuery({
    queryKey: ['giftExchange', 'messages', eventId],
    queryFn: () => giftExchangeApi.getMessages(eventId),
    enabled: !!eventId,
  })
}
