/**
 * API client for FamilyCircle backend - Multi-family version
 *
 * Barrel re-export: all imports from '@/lib/api' continue to work.
 */

// Client utilities
export { api, getToken, setToken, clearToken } from './client'

// All types
export type {
  AdminFamilyInfo,
  FamilyInfo,
  User,
  Member,
  SetupStatus,
  AuthResponse,
  SetupResponse,
  MagicLinkResponse,
  UserProfile,
  ProfileVisibility,
  FamilyMember,
  Settings,
  UserPreferences,
  NotificationSettings,
  EventType,
  HolidayDetail,
  BirthdayDetail,
  BabyShowerDetail,
  WeddingDetail,
  WeddingPartyMember,
  SubEvent,
  Event,
  EventDetail,
  WishlistItem,
  PotluckItem,
  PotluckInfo,
  GiftExchangeStatus,
  GiftExchangeAssignment,
  GiftExchangeMessage,
  GiftExchangeExclusion,
  PollOption,
  Poll,
  EventPhoto,
  CommentReaction,
  EventComment,
  PollTemplate,
  BabyShowerUpdate,
  RegistryItem,
  RegistryStats,
  WeddingTemplate,
  RSVPGuest,
  EventTemplate,
} from './types'

// API namespaces
export { authApi } from './auth'
export { eventsApi } from './events'
export { familyApi } from './family'
export { profileApi } from './profile'
export { settingsApi, notificationsApi } from './settings'
export { potluckApi } from './potluck'
export { giftExchangeApi } from './gift-exchange'
export { pollsApi, pollTemplatesApi } from './polls'
export { wishlistApi } from './wishlist'
export { eventCommentsApi } from './comments'
export { eventPhotosApi } from './photos'
export { calendarApi } from './calendar'
export { registryApi } from './registry'
export { rsvpGuestsApi } from './rsvp'
export { eventTemplatesApi, WEDDING_TEMPLATES } from './templates'
export { babyShowerUpdatesApi } from './baby-shower'
