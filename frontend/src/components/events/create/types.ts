import type { EventType } from '@/lib/api'

export type WizardStep =
  | 'event-type'
  | 'basics'
  | 'holiday-config'
  | 'birthday-config'
  | 'baby-shower-config'
  | 'wedding-config'
  | 'features'
  | 'gift-exchange'
  | 'potluck'

export interface EventBasics {
  title: string
  description: string
  event_date: string
  location_name: string
  location_address: string
  has_rsvp: boolean
}

export interface HolidayConfig {
  holiday_name: string
  custom_holiday_name: string
  year: string
}

export interface BirthdayConfig {
  birthday_person_id: string
  birthday_person_name: string
  birth_date: string
  age_turning: string
  is_secret: boolean
  theme: string
}

export interface BabyShowerConfig {
  parent1_name: string
  parent2_name: string
  baby_name: string
  gender: string
  due_date: string
  registry_url: string
  is_gender_reveal: boolean
}

export interface WeddingConfig {
  partner1_name: string
  partner2_name: string
  wedding_date: string
  venue_name: string
  registry_url: string
  color_theme: string
  sub_event_template: string
}

export interface FeatureConfig {
  giftExchange: {
    enabled: boolean
    useDefaultLocation: boolean
    location_name: string
    location_address: string
    budget_min: string
    budget_max: string
    notes: string
  }
  potluck: {
    enabled: boolean
    mode: 'organized' | 'open'
    hostProviding: string
    useDefaultLocation: boolean
    location_name: string
    location_address: string
  }
}

export const emptyBasics: EventBasics = {
  title: '',
  description: '',
  event_date: '',
  location_name: '',
  location_address: '',
  has_rsvp: true,
}

export const emptyHolidayConfig: HolidayConfig = {
  holiday_name: '',
  custom_holiday_name: '',
  year: '',
}

export const emptyBirthdayConfig: BirthdayConfig = {
  birthday_person_id: '',
  birthday_person_name: '',
  birth_date: '',
  age_turning: '',
  is_secret: false,
  theme: '',
}

export const emptyBabyShowerConfig: BabyShowerConfig = {
  parent1_name: '',
  parent2_name: '',
  baby_name: '',
  gender: '',
  due_date: '',
  registry_url: '',
  is_gender_reveal: false,
}

export const emptyWeddingConfig: WeddingConfig = {
  partner1_name: '',
  partner2_name: '',
  wedding_date: '',
  venue_name: '',
  registry_url: '',
  color_theme: '',
  sub_event_template: '',
}

export const emptyFeatureConfig: FeatureConfig = {
  giftExchange: {
    enabled: false,
    useDefaultLocation: true,
    location_name: '',
    location_address: '',
    budget_min: '',
    budget_max: '',
    notes: '',
  },
  potluck: {
    enabled: false,
    mode: 'organized',
    hostProviding: '',
    useDefaultLocation: true,
    location_name: '',
    location_address: '',
  },
}

export function getStepLabels(eventType: EventType, features: FeatureConfig): string[] {
  const steps = ['Type', 'Details']
  if (eventType === 'holiday') steps.push('Holiday')
  if (eventType === 'birthday') steps.push('Birthday')
  if (eventType === 'baby_shower') steps.push('Baby Shower')
  if (eventType === 'wedding') steps.push('Wedding')
  steps.push('Features')
  if (features.giftExchange.enabled) steps.push('Gift Exchange')
  if (features.potluck.enabled) steps.push('Potluck')
  return steps
}

export function getStepIndex(
  step: WizardStep,
  eventType: EventType,
  features: FeatureConfig
): number {
  const map: Record<string, number> = { 'event-type': 0, basics: 1 }
  let idx = 2
  if (eventType === 'holiday') {
    map['holiday-config'] = idx++
  }
  if (eventType === 'birthday') {
    map['birthday-config'] = idx++
  }
  if (eventType === 'baby_shower') {
    map['baby-shower-config'] = idx++
  }
  if (eventType === 'wedding') {
    map['wedding-config'] = idx++
  }
  map['features'] = idx++
  if (features.giftExchange.enabled) {
    map['gift-exchange'] = idx++
  }
  if (features.potluck.enabled) {
    map['potluck'] = idx
  }
  return map[step] ?? 0
}
