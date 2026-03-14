import { useMutation, useQueryClient } from '@tanstack/react-query'
import { giftExchangeApi } from '@/lib/api'

export function useRunAssignment() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: giftExchangeApi.runAssignment,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['giftExchange'] })
    },
  })
}

export function useSendGiftMessage() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ eventId, content }: { eventId: string; content: string }) =>
      giftExchangeApi.sendMessage(eventId, content),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['giftExchange'] })
    },
  })
}

export function useAddExclusion() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ eventId, user1Id, user2Id }: { eventId: string; user1Id: string; user2Id: string }) =>
      giftExchangeApi.addExclusion(eventId, user1Id, user2Id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['giftExchange'] })
    },
  })
}

export function useRemoveExclusion() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ eventId, exclusionId }: { eventId: string; exclusionId: string }) =>
      giftExchangeApi.removeExclusion(eventId, exclusionId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['giftExchange'] })
    },
  })
}
