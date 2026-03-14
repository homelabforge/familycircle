import { useMutation, useQueryClient } from '@tanstack/react-query'
import { familyApi } from '@/lib/api'

export function useInviteMember() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: familyApi.invite,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['family'] })
    },
  })
}

export function useSetMemberRole() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ userId, role }: { userId: string; role: 'admin' | 'member' }) =>
      familyApi.setRole(userId, role),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['family'] })
    },
  })
}

export function useRemoveMember() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: familyApi.removeMember,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['family'] })
    },
  })
}
