import { useMutation, useQueryClient } from '@tanstack/react-query'
import { pollsApi } from '@/lib/api'

export function useCreatePoll() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: pollsApi.create,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['polls'] })
    },
  })
}

export function useVote() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ pollId, optionIds }: { pollId: string; optionIds: string[] }) =>
      pollsApi.vote(pollId, optionIds),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['polls'] })
    },
  })
}

export function useClosePoll() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: pollsApi.close,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['polls'] })
    },
  })
}

export function useDeletePoll() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: pollsApi.delete,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['polls'] })
    },
  })
}
