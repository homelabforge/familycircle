import { useState } from 'react'
import { Wrench, Users, Settings, Plus, Mail, List } from 'lucide-react'
import BackButton from '@/components/BackButton'
import NewFamilyModal from '@/components/NewFamilyModal'
import EmailSettingsModal from '@/components/EmailSettingsModal'
import FamilyMembersModal from '@/components/FamilyMembersModal'
import ManageFamiliesModal from '@/components/ManageFamiliesModal'
import AppSettingsModal from '@/components/AppSettingsModal'
import { useBigMode } from '@/contexts/BigModeContext'
import { useAuth } from '@/contexts/AuthContext'

export default function Admin() {
  const { bigMode } = useBigMode()
  const { isSuperAdmin } = useAuth()

  // Modal states
  const [showNewFamilyModal, setShowNewFamilyModal] = useState(false)
  const [showEmailModal, setShowEmailModal] = useState(false)
  const [showFamilyModal, setShowFamilyModal] = useState(false)
  const [showSettingsModal, setShowSettingsModal] = useState(false)
  const [showManageFamiliesModal, setShowManageFamiliesModal] = useState(false)

  const adminCards = [
    {
      onClick: () => setShowFamilyModal(true),
      icon: Users,
      title: 'Family Members',
      description: 'Invite and manage',
    },
    {
      onClick: () => setShowSettingsModal(true),
      icon: Settings,
      title: 'App Settings',
      description: 'Theme and config',
    },
  ]

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
          <Wrench className={bigMode ? 'w-9 h-9' : 'w-7 h-7'} />
          Admin Panel
        </h1>

        <p className={`text-fc-text-muted mb-6 ${bigMode ? 'text-lg' : ''}`}>
          Manage your family circle settings and events.
        </p>

        {/* Admin Cards Grid */}
        <div
          className={`
            grid gap-4
            ${bigMode
              ? 'grid-cols-1 sm:grid-cols-2'
              : 'grid-cols-2 md:grid-cols-4'
            }
          `}
        >
          {adminCards.map((card) => (
            <button
              key={card.title}
              onClick={card.onClick}
              className={`
                flex flex-col items-center justify-center gap-2
                bg-fc-surface border border-fc-border rounded-2xl
                hover:border-primary/50 hover:bg-fc-surface/80
                transition-all cursor-pointer text-center
                ${bigMode ? 'p-6' : 'p-4'}
              `}
            >
              <div
                className={`
                  flex items-center justify-center rounded-xl
                  bg-primary/10
                  ${bigMode ? 'w-14 h-14' : 'w-12 h-12'}
                `}
              >
                <card.icon className={`text-primary ${bigMode ? 'w-7 h-7' : 'w-6 h-6'}`} />
              </div>
              <span className={`font-medium text-fc-text ${bigMode ? 'text-lg' : ''}`}>
                {card.title}
              </span>
              <span className={`text-fc-text-muted ${bigMode ? 'text-base' : 'text-sm'}`}>
                {card.description}
              </span>
            </button>
          ))}
        </div>

        {/* Super Admin Section */}
        {isSuperAdmin && (
          <div className="mt-8">
            <h2
              className={`
                font-semibold text-fc-text mb-4
                ${bigMode ? 'text-xl' : 'text-lg'}
              `}
            >
              Super Admin
            </h2>
            <div
              className={`
                grid gap-4
                ${bigMode
                  ? 'grid-cols-1 sm:grid-cols-2'
                  : 'grid-cols-2 md:grid-cols-4'
                }
              `}
            >
              <button
                onClick={() => setShowEmailModal(true)}
                className={`
                  flex flex-col items-center justify-center gap-2
                  bg-fc-surface border border-fc-border rounded-2xl
                  hover:border-primary/50 hover:bg-fc-surface/80
                  transition-all cursor-pointer text-center
                  ${bigMode ? 'p-6' : 'p-4'}
                `}
              >
                <div
                  className={`
                    flex items-center justify-center rounded-xl
                    bg-primary/10
                    ${bigMode ? 'w-14 h-14' : 'w-12 h-12'}
                  `}
                >
                  <Mail className={`text-primary ${bigMode ? 'w-7 h-7' : 'w-6 h-6'}`} />
                </div>
                <span className={`font-medium text-fc-text ${bigMode ? 'text-lg' : ''}`}>
                  Email Settings
                </span>
                <span className={`text-fc-text-muted ${bigMode ? 'text-base' : 'text-sm'}`}>
                  Configure SMTP
                </span>
              </button>
              <button
                onClick={() => setShowManageFamiliesModal(true)}
                className={`
                  flex flex-col items-center justify-center gap-2
                  bg-fc-surface border border-fc-border rounded-2xl
                  hover:border-primary/50 hover:bg-fc-surface/80
                  transition-all cursor-pointer text-center
                  ${bigMode ? 'p-6' : 'p-4'}
                `}
              >
                <div
                  className={`
                    flex items-center justify-center rounded-xl
                    bg-primary/10
                    ${bigMode ? 'w-14 h-14' : 'w-12 h-12'}
                  `}
                >
                  <List className={`text-primary ${bigMode ? 'w-7 h-7' : 'w-6 h-6'}`} />
                </div>
                <span className={`font-medium text-fc-text ${bigMode ? 'text-lg' : ''}`}>
                  Manage Families
                </span>
                <span className={`text-fc-text-muted ${bigMode ? 'text-base' : 'text-sm'}`}>
                  View and delete families
                </span>
              </button>
              <button
                onClick={() => setShowNewFamilyModal(true)}
                className={`
                  flex flex-col items-center justify-center gap-2
                  bg-fc-surface border border-fc-border rounded-2xl
                  hover:border-primary/50 hover:bg-fc-surface/80
                  transition-all cursor-pointer text-center
                  ${bigMode ? 'p-6' : 'p-4'}
                `}
              >
                <div
                  className={`
                    flex items-center justify-center rounded-xl
                    bg-primary/10
                    ${bigMode ? 'w-14 h-14' : 'w-12 h-12'}
                  `}
                >
                  <Plus className={`text-primary ${bigMode ? 'w-7 h-7' : 'w-6 h-6'}`} />
                </div>
                <span className={`font-medium text-fc-text ${bigMode ? 'text-lg' : ''}`}>
                  Create New Family
                </span>
                <span className={`text-fc-text-muted ${bigMode ? 'text-base' : 'text-sm'}`}>
                  Add another family group
                </span>
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Modals */}
      <FamilyMembersModal
        isOpen={showFamilyModal}
        onClose={() => setShowFamilyModal(false)}
      />
      <AppSettingsModal
        isOpen={showSettingsModal}
        onClose={() => setShowSettingsModal(false)}
      />
      <NewFamilyModal
        isOpen={showNewFamilyModal}
        onClose={() => setShowNewFamilyModal(false)}
      />
      <ManageFamiliesModal
        isOpen={showManageFamiliesModal}
        onClose={() => setShowManageFamiliesModal(false)}
      />
      <EmailSettingsModal
        isOpen={showEmailModal}
        onClose={() => setShowEmailModal(false)}
      />
    </div>
  )
}
