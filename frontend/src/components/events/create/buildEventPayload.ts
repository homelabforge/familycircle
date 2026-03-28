import { eventsApi } from '@/lib/api'
import type { EventType } from '@/lib/api'
import type {
  EventBasics,
  FeatureConfig,
  HolidayConfig,
  BirthdayConfig,
  BabyShowerConfig,
  WeddingConfig,
} from './types'

interface RecurrenceState {
  recurrenceType: string
  recurrenceEndDate: string
  recurrenceMaxOccurrences: string
}

interface BuildPayloadArgs {
  basics: EventBasics
  eventType: EventType
  features: FeatureConfig
  recurrence: RecurrenceState
  holidayConfig: HolidayConfig
  birthdayConfig: BirthdayConfig
  babyShowerConfig: BabyShowerConfig
  weddingConfig: WeddingConfig
}

export function buildEventPayload({
  basics,
  eventType,
  features,
  recurrence,
  holidayConfig,
  birthdayConfig,
  babyShowerConfig,
  weddingConfig,
}: BuildPayloadArgs): Parameters<typeof eventsApi.create>[0] {
  const payload: Parameters<typeof eventsApi.create>[0] = {
    title: basics.title,
    description: basics.description || undefined,
    event_date: basics.event_date,
    location_name: basics.location_name || undefined,
    location_address: basics.location_address || undefined,
    has_gift_exchange: features.giftExchange.enabled,
    has_potluck: features.potluck.enabled,
    has_rsvp: basics.has_rsvp,
    event_type: eventType,
    ...(features.giftExchange.enabled && {
      gift_exchange_budget_min: features.giftExchange.budget_min
        ? parseInt(features.giftExchange.budget_min)
        : undefined,
      gift_exchange_budget_max: features.giftExchange.budget_max
        ? parseInt(features.giftExchange.budget_max)
        : undefined,
      gift_exchange_notes: features.giftExchange.notes || undefined,
    }),
    ...(features.potluck.enabled && {
      potluck_mode: features.potluck.mode,
      potluck_host_providing: features.potluck.hostProviding || undefined,
    }),
  }

  // Add recurrence if set
  if (recurrence.recurrenceType) {
    payload.recurrence_type = recurrence.recurrenceType
    if (recurrence.recurrenceEndDate) {
      payload.recurrence_end_date = recurrence.recurrenceEndDate
    }
    if (recurrence.recurrenceMaxOccurrences) {
      payload.recurrence_max_occurrences = parseInt(recurrence.recurrenceMaxOccurrences)
    }
  }

  // Add type-specific details
  if (eventType === 'holiday' && holidayConfig.holiday_name) {
    payload.holiday_detail = {
      holiday_name: holidayConfig.holiday_name,
      custom_holiday_name:
        holidayConfig.holiday_name === 'custom'
          ? holidayConfig.custom_holiday_name || undefined
          : undefined,
      year: holidayConfig.year ? parseInt(holidayConfig.year) : undefined,
    }
  }

  if (eventType === 'birthday' && birthdayConfig.birthday_person_name) {
    payload.birthday_detail = {
      birthday_person_id: birthdayConfig.birthday_person_id || undefined,
      birthday_person_name: birthdayConfig.birthday_person_name,
      birth_date: birthdayConfig.birth_date || undefined,
      age_turning: birthdayConfig.age_turning
        ? parseInt(birthdayConfig.age_turning)
        : undefined,
      is_secret: birthdayConfig.is_secret,
      theme: birthdayConfig.theme || undefined,
    }
  }

  if (eventType === 'baby_shower' && babyShowerConfig.parent1_name) {
    payload.baby_shower_detail = {
      parent1_name: babyShowerConfig.parent1_name,
      parent2_name: babyShowerConfig.parent2_name || undefined,
      baby_name: babyShowerConfig.baby_name || undefined,
      gender: babyShowerConfig.gender || undefined,
      due_date: babyShowerConfig.due_date || undefined,
      registry_url: babyShowerConfig.registry_url || undefined,
      is_gender_reveal: babyShowerConfig.is_gender_reveal,
    }
  }

  if (eventType === 'wedding' && weddingConfig.partner1_name) {
    payload.wedding_detail = {
      partner1_name: weddingConfig.partner1_name,
      partner2_name: weddingConfig.partner2_name,
      wedding_date: weddingConfig.wedding_date || undefined,
      venue_name: weddingConfig.venue_name || undefined,
      registry_url: weddingConfig.registry_url || undefined,
      color_theme: weddingConfig.color_theme || undefined,
      sub_event_template: weddingConfig.sub_event_template || undefined,
    }
  }

  return payload
}
