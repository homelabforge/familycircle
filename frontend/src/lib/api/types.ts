/**
 * All shared types and interfaces for the FamilyCircle API
 */

// User and Family types
export interface FamilyInfo {
  id: string
  name: string
  family_code: string
  role: 'admin' | 'member'
}

export interface AdminFamilyInfo {
  id: string
  name: string
  family_code: string
  member_count: number
  created_at: string
}

export interface User {
  id: string
  email: string
  is_super_admin: boolean
  theme: string
  big_mode: boolean
  current_family_id: string | null
  current_family_name: string | null
  display_name: string | null
  role_in_family: 'admin' | 'member' | null
  families: FamilyInfo[]
}

// Legacy Member type for backwards compatibility
export interface Member {
  id: string
  name: string
  email: string
  is_organizer: boolean
  theme: string
  big_mode: boolean
}

export interface SetupStatus {
  needs_setup: boolean
}

export interface AuthResponse {
  session_token: string
  user: User
  message?: string
}

export interface SetupResponse extends AuthResponse {
  family: {
    id: string
    name: string
    family_code: string
  }
}

export interface MagicLinkResponse {
  message: string
  dev_token?: string
}

// Profile types
export interface UserProfile {
  phone: string | null
  address_line1: string | null
  address_line2: string | null
  city: string | null
  state: string | null
  zip_code: string | null
  country: string | null
  allergies: string | null
  dietary_restrictions: string | null
  medical_needs: string | null
  mobility_notes: string | null
  share_health_info: boolean
}

export interface ProfileVisibility {
  show_email: boolean
  show_phone: boolean
  show_address: boolean
}

// Family member (from address book)
export interface FamilyMember {
  user_id: string
  display_name: string
  role: 'admin' | 'member'
  email?: string
  phone?: string
  address?: string
}

// Settings types
export interface Settings {
  app_name: string
  theme_color?: string
  magic_link_expiry_days?: string
  cancelled_event_retention_days?: string
  // SMTP settings (super admin only)
  smtp_host?: string
  smtp_port?: string
  smtp_username?: string
  smtp_password?: string
  smtp_from_email?: string
  smtp_from_name?: string
  smtp_use_tls?: string
  smtp_configured?: boolean
}

export interface UserPreferences {
  theme: string
  big_mode: boolean
}

// Notifications types
export interface NotificationSettings {
  // Retry
  notification_retry_attempts: string
  notification_retry_delay: string
  // ntfy
  ntfy_enabled: string
  ntfy_server: string
  ntfy_topic: string
  ntfy_token: string
  // Gotify
  gotify_enabled: string
  gotify_server: string
  gotify_token: string
  // Pushover
  pushover_enabled: string
  pushover_user_key: string
  pushover_api_token: string
  // Slack
  slack_enabled: string
  slack_webhook_url: string
  // Discord
  discord_enabled: string
  discord_webhook_url: string
  // Telegram
  telegram_enabled: string
  telegram_bot_token: string
  telegram_chat_id: string
  // Email
  notification_email_enabled: string
  notification_email_to: string
  // Event toggles
  notify_event_created: string
  notify_event_updated: string
  notify_event_cancelled: string
  notify_event_reminder: string
  notify_rsvp_received: string
  notify_poll_created: string
  notify_poll_closing_soon: string
  notify_comment_added: string
  notify_comment_mention: string
  notify_family_member_joined: string
  // Reminder config
  event_reminder_days: string
  // SMTP status
  smtp_configured: boolean
}

// Event types
export type EventType = 'general' | 'holiday' | 'birthday' | 'baby_shower' | 'wedding'

export interface HolidayDetail {
  holiday_name: string
  custom_holiday_name?: string
  display_name: string
  year?: number
}

export interface BirthdayDetail {
  birthday_person_id?: string
  birthday_person_name: string
  birth_date?: string
  age_turning?: number
  is_secret: boolean
  theme?: string
}

export interface BabyShowerDetail {
  parent1_name: string
  parent2_name?: string
  baby_name?: string
  gender?: string
  due_date?: string
  registry_url?: string
  is_gender_reveal: boolean
  display_parents: string
}

export interface WeddingDetail {
  partner1_name: string
  partner2_name: string
  wedding_date?: string
  venue_name?: string
  registry_url?: string
  color_theme?: string
  display_couple: string
}

export interface WeddingPartyMember {
  id: string
  name: string
  role: string
  side?: string
  user_id?: string
  display_role: string
}

export interface SubEvent {
  id: string
  title: string
  event_date?: string
  event_type: EventType
  is_cancelled: boolean
}

export interface Event {
  id: string
  family_id: string
  created_by_id: string
  title: string
  description?: string
  event_date: string
  location_name?: string
  location_address?: string
  has_gift_exchange: boolean
  has_potluck: boolean
  has_rsvp: boolean
  potluck_mode?: string
  potluck_host_providing?: string
  gift_exchange_assigned: boolean
  gift_exchange_budget_min?: number
  gift_exchange_budget_max?: number
  gift_exchange_notes?: string
  event_type: EventType
  parent_event_id?: string
  holiday_detail?: HolidayDetail | null
  birthday_detail?: BirthdayDetail | null
  baby_shower_detail?: BabyShowerDetail | null
  wedding_detail?: WeddingDetail | null
  sub_events?: SubEvent[]
  sub_event_count?: number
  wedding_party?: WeddingPartyMember[]
  is_cancelled: boolean
  cancelled_at?: string
  cancellation_reason?: string
  rsvp_counts: { yes: number; no: number; maybe: number }
  headcount?: number
  user_rsvp?: string
  can_manage: boolean
  is_recurring?: boolean
  recurrence?: {
    recurrence_type: string
    next_occurrence: string | null
    end_date: string | null
    max_occurrences: number | null
    occurrences_created: number
  } | null
  created_at?: string
}

export interface EventDetail extends Event {
  rsvps: { user_id: string; display_name: string; status: string }[]
}

// Wishlist types
export interface WishlistItem {
  id: string
  name: string
  description?: string
  url?: string
  price_range?: string
  priority: number
  created_at?: string
}

// Potluck types
export interface PotluckItem {
  id: string
  name: string
  category?: string
  description?: string
  serves?: number
  dietary_info?: string
  allergens?: string
  claimed_by_id?: string
  claimed_by_name?: string
  created_at?: string
}

export interface PotluckInfo {
  event_id: string
  event_title: string
  potluck_mode: string
  potluck_host_providing?: string
  can_manage: boolean
  items: PotluckItem[]
  categories: Record<string, PotluckItem[]>
  stats: { total: number; claimed: number; unclaimed: number }
}

// Gift Exchange types
export interface GiftExchangeStatus {
  event_id: string
  status: 'not_assigned' | 'assigned'
  participant_count: number
  has_assignment: boolean
}

export interface GiftExchangeAssignment {
  giftee_id: string | null
  giftee_name: string | null
  wishlist: WishlistItem[]
}

export interface GiftExchangeMessage {
  id: string
  content: string
  created_at?: string
}

export interface GiftExchangeExclusion {
  id: string
  user1_id: string
  user1_name: string
  user2_id: string
  user2_name: string
}

// Poll types
export interface PollOption {
  id: string
  text: string
  display_order: number
  vote_count: number
  voted_by: string[] | null // null when anonymous
}

export interface Poll {
  id: string
  family_id: string
  event_id: string | null
  created_by_id: string | null
  created_by_name: string | null
  title: string
  description: string | null
  allow_multiple: boolean
  is_anonymous: boolean
  close_date: string | null
  is_closed: boolean
  total_votes: number
  user_voted: boolean
  user_votes: string[] // option IDs user voted for
  options: PollOption[]
  created_at: string
}

// Photo types
export interface EventPhoto {
  id: string
  event_id: string
  uploaded_by_id: string | null
  uploaded_by_name: string
  filename: string
  url: string
  file_size: number
  mime_type: string
  caption: string | null
  display_order: number
  created_at: string
}

// Comment types
export interface CommentReaction {
  emoji: string
  count: number
  user_ids: string[]
}

export interface EventComment {
  id: string
  event_id: string
  user_id: string
  user_name: string
  content: string
  edited_at: string | null
  is_own: boolean
  is_pinned: boolean
  pinned_at: string | null
  reactions: CommentReaction[]
  created_at: string
}

// Poll Template types
export interface PollTemplate {
  id: string
  name: string
  description: string | null
  options: string[]
  allow_multiple: boolean
  is_builtin: boolean
}

// Baby Shower Update types
export interface BabyShowerUpdate {
  id: string
  event_id: string
  update_type: string
  update_date: string | null
  title: string
  notes: string | null
  photo_id: string | null
  photo_url: string | null
  posted_by_id: string | null
  posted_by_name: string
  created_at: string | null
}

// Registry types
export interface RegistryItem {
  id: string
  event_id: string
  item_name: string
  item_url: string | null
  price: number | null
  image_url: string | null
  quantity: number
  claimed_by_id: string | null
  claimed_by_name: string | null
  is_claimed: boolean
  is_purchased: boolean
  purchased_at: string | null
  notes: string | null
  created_at: string | null
}

export interface RegistryStats {
  total: number
  claimed: number
  purchased: number
}

// Wedding Template types
export interface WeddingTemplate {
  name: string
  label: string
  sub_events: { title: string; offset_days: string }[]
}

// RSVP Guest types
export interface RSVPGuest {
  id: string
  rsvp_id: string
  guest_name: string
  dietary_restrictions: string | null
  allergies: string | null
  created_at: string | null
}

// Event Template types
export interface EventTemplate {
  id: string
  family_id: string
  name: string
  description: string | null
  template_json: string
  created_by_id: string | null
  created_at: string | null
}
