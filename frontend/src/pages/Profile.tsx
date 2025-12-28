import { useEffect, useState } from 'react'
import {
  User,
  Phone,
  MapPin,
  Heart,
  Eye,
  EyeOff,
  Loader2,
  AlertTriangle,
  Gift,
} from 'lucide-react'
import { toast } from 'sonner'
import BackButton from '@/components/BackButton'
import { useBigMode } from '@/contexts/BigModeContext'
import { useAuth } from '@/contexts/AuthContext'
import { profileApi, type UserProfile, type ProfileVisibility } from '@/lib/api'

export default function Profile() {
  const { bigMode } = useBigMode()
  const { currentFamily } = useAuth()
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)

  // Profile data
  const [profile, setProfile] = useState<UserProfile>({
    phone: null,
    address_line1: null,
    address_line2: null,
    city: null,
    state: null,
    zip_code: null,
    country: null,
    allergies: null,
    dietary_restrictions: null,
    medical_needs: null,
    mobility_notes: null,
    share_health_info: false,
  })

  // Visibility settings for current family
  const [visibility, setVisibility] = useState<ProfileVisibility>({
    show_email: true,
    show_phone: true,
    show_address: true,
  })

  useEffect(() => {
    loadData()
  }, [currentFamily?.id])

  const loadData = async () => {
    try {
      setLoading(true)
      const profileData = await profileApi.get()
      setProfile(profileData)

      if (currentFamily?.id) {
        const visibilityData = await profileApi.getVisibility(currentFamily.id)
        setVisibility(visibilityData)
      }
    } catch (err) {
      toast.error('Failed to load profile')
    } finally {
      setLoading(false)
    }
  }

  const handleProfileChange = (field: keyof UserProfile, value: string | boolean) => {
    setProfile((prev) => ({ ...prev, [field]: value }))
  }

  const handleVisibilityChange = (field: keyof ProfileVisibility, value: boolean) => {
    setVisibility((prev) => ({ ...prev, [field]: value }))
  }

  const handleSave = async () => {
    try {
      setSaving(true)
      await profileApi.update(profile)
      if (currentFamily?.id) {
        await profileApi.updateVisibility(currentFamily.id, visibility)
      }
      toast.success('Profile saved')
    } catch (err) {
      toast.error('Failed to save profile')
    } finally {
      setSaving(false)
    }
  }

  const inputClass = `
    w-full px-4 py-3 rounded-xl
    bg-fc-bg border border-fc-border
    text-fc-text placeholder:text-fc-text-muted
    focus:outline-none focus:ring-2 focus:ring-primary/50
    ${bigMode ? 'text-lg' : 'text-base'}
  `

  const labelClass = `block text-fc-text mb-2 ${bigMode ? 'text-lg' : 'text-sm'} font-medium`

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-6">
        <BackButton />
        <div className="flex justify-center py-12">
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
          <User className={bigMode ? 'w-9 h-9' : 'w-7 h-7'} />
          My Profile
          {saving && <Loader2 className="w-5 h-5 animate-spin text-fc-text-muted" />}
        </h1>

        <div className="space-y-6">
          {/* Contact Information */}
          <div className="bg-fc-surface border border-fc-border rounded-2xl p-6">
            <div className="flex items-center gap-4 mb-6">
              <div className="w-12 h-12 bg-primary/10 rounded-xl flex items-center justify-center">
                <Phone className="w-6 h-6 text-primary" />
              </div>
              <div>
                <h2
                  className={`
                    font-semibold text-fc-text
                    ${bigMode ? 'text-xl' : 'text-lg'}
                  `}
                >
                  Contact Information
                </h2>
                <p className={`text-fc-text-muted ${bigMode ? 'text-base' : 'text-sm'}`}>
                  Your phone number for family contact
                </p>
              </div>
            </div>

            <div className="space-y-4">
              <div>
                <label className={labelClass}>Phone Number</label>
                <input
                  type="tel"
                  value={profile.phone || ''}
                  onChange={(e) => handleProfileChange('phone', e.target.value)}
                  placeholder="(555) 123-4567"
                  className={inputClass}
                />
              </div>
            </div>
          </div>

          {/* Address */}
          <div className="bg-fc-surface border border-fc-border rounded-2xl p-6">
            <div className="flex items-center gap-4 mb-6">
              <div className="w-12 h-12 bg-primary/10 rounded-xl flex items-center justify-center">
                <MapPin className="w-6 h-6 text-primary" />
              </div>
              <div>
                <h2
                  className={`
                    font-semibold text-fc-text
                    ${bigMode ? 'text-xl' : 'text-lg'}
                  `}
                >
                  Address
                </h2>
                <p className={`text-fc-text-muted ${bigMode ? 'text-base' : 'text-sm'}`}>
                  Your mailing address
                </p>
              </div>
            </div>

            {/* Secret Santa Note */}
            <div className="mb-6 p-4 rounded-xl bg-warning/10 border border-warning/20">
              <div className="flex items-start gap-3">
                <Gift className="w-5 h-5 text-warning flex-shrink-0 mt-0.5" />
                <p className={`text-fc-text ${bigMode ? 'text-base' : 'text-sm'}`}>
                  <strong>Note:</strong> Your address will be shared with your Secret Santa match so they can send you a gift.
                </p>
              </div>
            </div>

            <div className="space-y-4">
              <div>
                <label className={labelClass}>Address Line 1</label>
                <input
                  type="text"
                  value={profile.address_line1 || ''}
                  onChange={(e) => handleProfileChange('address_line1', e.target.value)}
                  placeholder="123 Main Street"
                  className={inputClass}
                />
              </div>
              <div>
                <label className={labelClass}>Address Line 2</label>
                <input
                  type="text"
                  value={profile.address_line2 || ''}
                  onChange={(e) => handleProfileChange('address_line2', e.target.value)}
                  placeholder="Apt 4B (optional)"
                  className={inputClass}
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className={labelClass}>City</label>
                  <input
                    type="text"
                    value={profile.city || ''}
                    onChange={(e) => handleProfileChange('city', e.target.value)}
                    placeholder="City"
                    className={inputClass}
                  />
                </div>
                <div>
                  <label className={labelClass}>State/Province</label>
                  <input
                    type="text"
                    value={profile.state || ''}
                    onChange={(e) => handleProfileChange('state', e.target.value)}
                    placeholder="State"
                    className={inputClass}
                  />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className={labelClass}>ZIP/Postal Code</label>
                  <input
                    type="text"
                    value={profile.zip_code || ''}
                    onChange={(e) => handleProfileChange('zip_code', e.target.value)}
                    placeholder="12345"
                    className={inputClass}
                  />
                </div>
                <div>
                  <label className={labelClass}>Country</label>
                  <input
                    type="text"
                    value={profile.country || ''}
                    onChange={(e) => handleProfileChange('country', e.target.value)}
                    placeholder="United States"
                    className={inputClass}
                  />
                </div>
              </div>
            </div>
          </div>

          {/* Health Information */}
          <div className="bg-fc-surface border border-fc-border rounded-2xl p-6">
            <div className="flex items-center gap-4 mb-6">
              <div className="w-12 h-12 bg-primary/10 rounded-xl flex items-center justify-center">
                <Heart className="w-6 h-6 text-primary" />
              </div>
              <div>
                <h2
                  className={`
                    font-semibold text-fc-text
                    ${bigMode ? 'text-xl' : 'text-lg'}
                  `}
                >
                  Health Information
                </h2>
                <p className={`text-fc-text-muted ${bigMode ? 'text-base' : 'text-sm'}`}>
                  Medical and dietary needs for event planning
                </p>
              </div>
            </div>

            {/* Health Sharing Toggle */}
            <div className="mb-6 p-4 rounded-xl bg-fc-bg border border-fc-border">
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <h3 className={`font-medium text-fc-text ${bigMode ? 'text-lg' : 'text-base'}`}>
                    Share health info with event organizers
                  </h3>
                  <p className={`text-fc-text-muted ${bigMode ? 'text-base' : 'text-sm'} mt-1`}>
                    {profile.share_health_info
                      ? 'Your health info will be shown anonymously (e.g., "Someone has a peanut allergy")'
                      : 'Your health info will be kept private'}
                  </p>
                </div>
                <button
                  onClick={() => handleProfileChange('share_health_info', !profile.share_health_info)}
                  className={`
                    relative w-14 h-8 rounded-full transition-colors flex-shrink-0 ml-4
                    ${profile.share_health_info ? 'bg-primary' : 'bg-fc-border'}
                  `}
                >
                  <span
                    className={`
                      absolute top-1 w-6 h-6 bg-white rounded-full transition-transform
                      ${profile.share_health_info ? 'translate-x-7' : 'translate-x-1'}
                    `}
                  />
                </button>
              </div>

              {!profile.share_health_info && (
                <div className="mt-4 p-3 rounded-lg bg-warning/10 border border-warning/20">
                  <div className="flex items-start gap-2">
                    <AlertTriangle className="w-5 h-5 text-warning flex-shrink-0 mt-0.5" />
                    <p className={`text-fc-text ${bigMode ? 'text-sm' : 'text-xs'}`}>
                      If you choose not to share, event organizers won't know about your dietary or medical needs. You attend at your own risk.
                    </p>
                  </div>
                </div>
              )}
            </div>

            <div className="space-y-4">
              <div>
                <label className={labelClass}>Allergies</label>
                <textarea
                  value={profile.allergies || ''}
                  onChange={(e) => handleProfileChange('allergies', e.target.value)}
                  placeholder="List any food or environmental allergies"
                  rows={2}
                  className={inputClass}
                />
              </div>
              <div>
                <label className={labelClass}>Dietary Restrictions</label>
                <textarea
                  value={profile.dietary_restrictions || ''}
                  onChange={(e) => handleProfileChange('dietary_restrictions', e.target.value)}
                  placeholder="Vegetarian, vegan, gluten-free, etc."
                  rows={2}
                  className={inputClass}
                />
              </div>
              <div>
                <label className={labelClass}>Medical Needs</label>
                <textarea
                  value={profile.medical_needs || ''}
                  onChange={(e) => handleProfileChange('medical_needs', e.target.value)}
                  placeholder="Any medical conditions event organizers should know about"
                  rows={2}
                  className={inputClass}
                />
              </div>
              <div>
                <label className={labelClass}>Mobility Notes</label>
                <textarea
                  value={profile.mobility_notes || ''}
                  onChange={(e) => handleProfileChange('mobility_notes', e.target.value)}
                  placeholder="Wheelchair access, limited walking, etc."
                  rows={2}
                  className={inputClass}
                />
              </div>
            </div>
          </div>

          {/* Privacy Settings */}
          {currentFamily && (
            <div className="bg-fc-surface border border-fc-border rounded-2xl p-6">
              <div className="flex items-center gap-4 mb-6">
                <div className="w-12 h-12 bg-primary/10 rounded-xl flex items-center justify-center">
                  <Eye className="w-6 h-6 text-primary" />
                </div>
                <div>
                  <h2
                    className={`
                      font-semibold text-fc-text
                      ${bigMode ? 'text-xl' : 'text-lg'}
                    `}
                  >
                    Privacy for {currentFamily.name}
                  </h2>
                  <p className={`text-fc-text-muted ${bigMode ? 'text-base' : 'text-sm'}`}>
                    Control what family members can see
                  </p>
                </div>
              </div>

              <div className="space-y-4">
                {/* Show Email */}
                <div className="flex items-center justify-between p-4 rounded-xl bg-fc-bg">
                  <div className="flex items-center gap-3">
                    {visibility.show_email ? (
                      <Eye className="w-5 h-5 text-primary" />
                    ) : (
                      <EyeOff className="w-5 h-5 text-fc-text-muted" />
                    )}
                    <span className={`text-fc-text ${bigMode ? 'text-lg' : 'text-base'}`}>
                      Show email address
                    </span>
                  </div>
                  <button
                    onClick={() => handleVisibilityChange('show_email', !visibility.show_email)}
                    className={`
                      relative w-14 h-8 rounded-full transition-colors
                      ${visibility.show_email ? 'bg-primary' : 'bg-fc-border'}
                    `}
                  >
                    <span
                      className={`
                        absolute top-1 w-6 h-6 bg-white rounded-full transition-transform
                        ${visibility.show_email ? 'translate-x-7' : 'translate-x-1'}
                      `}
                    />
                  </button>
                </div>

                {/* Show Phone */}
                <div className="flex items-center justify-between p-4 rounded-xl bg-fc-bg">
                  <div className="flex items-center gap-3">
                    {visibility.show_phone ? (
                      <Eye className="w-5 h-5 text-primary" />
                    ) : (
                      <EyeOff className="w-5 h-5 text-fc-text-muted" />
                    )}
                    <span className={`text-fc-text ${bigMode ? 'text-lg' : 'text-base'}`}>
                      Show phone number
                    </span>
                  </div>
                  <button
                    onClick={() => handleVisibilityChange('show_phone', !visibility.show_phone)}
                    className={`
                      relative w-14 h-8 rounded-full transition-colors
                      ${visibility.show_phone ? 'bg-primary' : 'bg-fc-border'}
                    `}
                  >
                    <span
                      className={`
                        absolute top-1 w-6 h-6 bg-white rounded-full transition-transform
                        ${visibility.show_phone ? 'translate-x-7' : 'translate-x-1'}
                      `}
                    />
                  </button>
                </div>

                {/* Show Address */}
                <div className="flex items-center justify-between p-4 rounded-xl bg-fc-bg">
                  <div className="flex items-center gap-3">
                    {visibility.show_address ? (
                      <Eye className="w-5 h-5 text-primary" />
                    ) : (
                      <EyeOff className="w-5 h-5 text-fc-text-muted" />
                    )}
                    <span className={`text-fc-text ${bigMode ? 'text-lg' : 'text-base'}`}>
                      Show address in family directory
                    </span>
                  </div>
                  <button
                    onClick={() => handleVisibilityChange('show_address', !visibility.show_address)}
                    className={`
                      relative w-14 h-8 rounded-full transition-colors
                      ${visibility.show_address ? 'bg-primary' : 'bg-fc-border'}
                    `}
                  >
                    <span
                      className={`
                        absolute top-1 w-6 h-6 bg-white rounded-full transition-transform
                        ${visibility.show_address ? 'translate-x-7' : 'translate-x-1'}
                      `}
                    />
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Save Button */}
          <button
            onClick={handleSave}
            disabled={saving}
            className={`
              w-full py-4 rounded-xl font-semibold
              bg-primary text-white
              hover:bg-primary-hover transition-colors
              disabled:opacity-50
              ${bigMode ? 'text-xl' : 'text-lg'}
            `}
          >
            {saving ? (
              <span className="flex items-center justify-center gap-2">
                <Loader2 className="w-5 h-5 animate-spin" />
                Saving...
              </span>
            ) : (
              'Save Profile'
            )}
          </button>
        </div>
      </div>
    </div>
  )
}
