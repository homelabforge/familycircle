import { useQuery } from '@tanstack/react-query'
import { familyApi } from '@/lib/api'

export function useFamilyMembers() {
  return useQuery({
    queryKey: ['family', 'members'],
    queryFn: () => familyApi.listMembers(),
  })
}

export function useAddressBook() {
  return useQuery({
    queryKey: ['family', 'addressBook'],
    queryFn: () => familyApi.getAddressBook(),
  })
}
