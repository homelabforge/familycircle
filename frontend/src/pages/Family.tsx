import { Users, Mail, Crown, Loader2, Phone, MapPin, Lock } from 'lucide-react'
import BackButton from '@/components/BackButton'
import { useBigMode } from '@/contexts/BigModeContext'
import { useAddressBook } from '@/hooks/queries/useFamily'

export default function Family() {
  const { bigMode } = useBigMode()
  const { data, isLoading: loading, error: queryError } = useAddressBook()
  const members = data?.members ?? []
  const error = queryError ? (queryError instanceof Error ? queryError.message : 'Failed to load family members') : null

  const getInitials = (name?: string) => {
    if (!name) return '?'
    return name
      .split(' ')
      .map((n) => n[0])
      .join('')
      .toUpperCase()
      .slice(0, 2)
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
          <Users className={bigMode ? 'w-9 h-9' : 'w-7 h-7'} />
          Family Directory
        </h1>

        {error && (
          <div className="bg-error/10 text-error px-4 py-3 rounded-xl mb-6">
            {error}
          </div>
        )}

        <p className={`text-fc-text-muted mb-6 ${bigMode ? 'text-lg' : ''}`}>
          {members.length} member{members.length !== 1 ? 's' : ''} in your family circle
        </p>

        <div className="space-y-4">
          {members.map((member) => (
            <div
              key={member.user_id}
              className={`
                bg-fc-surface border border-fc-border rounded-xl
                ${bigMode ? 'p-5' : 'p-4'}
              `}
            >
              <div className="flex items-start gap-4">
                {/* Avatar */}
                <div
                  className={`
                    flex items-center justify-center flex-shrink-0
                    bg-primary/10 rounded-full font-bold text-primary
                    ${bigMode ? 'w-14 h-14 text-lg' : 'w-12 h-12'}
                  `}
                >
                  {getInitials(member.display_name)}
                </div>

                {/* Info */}
                <div className="flex-1 min-w-0">
                  {/* Name and Role */}
                  <div className="flex items-center gap-2 flex-wrap">
                    <h3
                      className={`
                        font-medium text-fc-text
                        ${bigMode ? 'text-lg' : ''}
                      `}
                    >
                      {member.display_name}
                    </h3>
                    {member.role === 'admin' && (
                      <Crown className="w-4 h-4 text-warning" aria-label="Admin" />
                    )}
                  </div>

                  {/* Contact Info */}
                  <div className={`mt-2 space-y-1 ${bigMode ? 'text-base' : 'text-sm'}`}>
                    {/* Email */}
                    <div className="flex items-center gap-2 text-fc-text-muted">
                      <Mail className="w-4 h-4 flex-shrink-0" />
                      {member.email ? (
                        <a
                          href={`mailto:${member.email}`}
                          className="hover:text-primary truncate"
                        >
                          {member.email}
                        </a>
                      ) : (
                        <span className="flex items-center gap-1 italic">
                          <Lock className="w-3 h-3" />
                          Private
                        </span>
                      )}
                    </div>

                    {/* Phone */}
                    <div className="flex items-center gap-2 text-fc-text-muted">
                      <Phone className="w-4 h-4 flex-shrink-0" />
                      {member.phone ? (
                        <a
                          href={`tel:${member.phone}`}
                          className="hover:text-primary"
                        >
                          {member.phone}
                        </a>
                      ) : (
                        <span className="flex items-center gap-1 italic">
                          <Lock className="w-3 h-3" />
                          Private
                        </span>
                      )}
                    </div>

                    {/* Address */}
                    <div className="flex items-start gap-2 text-fc-text-muted">
                      <MapPin className="w-4 h-4 flex-shrink-0 mt-0.5" />
                      {member.address ? (
                        <span className="break-words">{member.address}</span>
                      ) : (
                        <span className="flex items-center gap-1 italic">
                          <Lock className="w-3 h-3" />
                          Private
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>

        {members.length === 0 && !error && (
          <div className="text-center py-12">
            <Users className="w-16 h-16 text-fc-text-muted mx-auto mb-4" />
            <p className={`text-fc-text-muted ${bigMode ? 'text-lg' : ''}`}>
              No family members yet.
            </p>
          </div>
        )}
      </div>
    </div>
  )
}
