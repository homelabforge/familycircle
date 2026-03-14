import { useQuery } from '@tanstack/react-query'
import { pollsApi } from '@/lib/api'

export function usePolls(eventId?: string) {
  return useQuery({
    queryKey: ['polls', eventId ?? 'all'],
    queryFn: () => pollsApi.list(eventId),
  })
}

export function usePoll(id: string) {
  return useQuery({
    queryKey: ['polls', id],
    queryFn: () => pollsApi.get(id),
    enabled: !!id,
  })
}
