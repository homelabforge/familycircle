import { z } from 'zod'

// ============================================================================
// Common schemas
// ============================================================================

export const emailSchema = z.string().email('Please enter a valid email address')

export const passwordSchema = z
  .string()
  .min(6, 'Password must be at least 6 characters')

export const nameSchema = z
  .string()
  .min(1, 'Name is required')
  .transform((v) => v.trim())

export const optionalString = z
  .string()
  .transform((v) => v.trim() || undefined)
  .optional()

export const optionalUrl = z
  .string()
  .url('Please enter a valid URL')
  .or(z.literal(''))
  .transform((v) => v || undefined)
  .optional()

export const optionalPositiveInt = z
  .string()
  .transform((v) => (v ? parseInt(v, 10) : undefined))
  .refine((v) => v === undefined || (Number.isInteger(v) && v > 0), {
    message: 'Must be a positive number',
  })
  .optional()

// ============================================================================
// Auth schemas
// ============================================================================

export const loginSchema = z.object({
  email: emailSchema,
  password: z.string().min(1, 'Password is required'),
})

export const registerSchema = z
  .object({
    family_code: z
      .string()
      .min(1, 'Family code is required')
      .transform((v) => v.toUpperCase().trim()),
    display_name: nameSchema,
    email: emailSchema,
    password: passwordSchema,
    confirmPassword: z.string(),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: 'Passwords do not match',
    path: ['confirmPassword'],
  })

export const setupSchema = z
  .object({
    display_name: nameSchema,
    email: emailSchema,
    password: passwordSchema,
    confirmPassword: z.string(),
    family_name: z.string().min(1, 'Family name is required').transform((v) => v.trim()),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: 'Passwords do not match',
    path: ['confirmPassword'],
  })

export const forgotPasswordSchema = z.object({
  email: emailSchema,
})

export const resetPasswordSchema = z
  .object({
    password: passwordSchema,
    confirmPassword: z.string(),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: 'Passwords do not match',
    path: ['confirmPassword'],
  })

// Legacy aliases for backwards compatibility
export const magicLinkSchema = forgotPasswordSchema
export const organizerLoginSchema = loginSchema
export const joinFamilySchema = registerSchema

// ============================================================================
// Event schemas
// ============================================================================

export const eventTypeSchema = z.enum([
  'general', 'holiday', 'birthday', 'baby_shower', 'wedding',
])

export const eventFormSchema = z.object({
  title: z.string().min(1, 'Title is required').transform((v) => v.trim()),
  description: optionalString,
  event_date: z.string().min(1, 'Date is required'),
  location_name: optionalString,
  location_address: optionalString,
  has_gift_exchange: z.boolean().default(false),
  has_potluck: z.boolean().default(false),
  event_type: eventTypeSchema.default('general'),
})

export const holidayDetailSchema = z
  .object({
    holiday_name: z.string().min(1, 'Select a holiday'),
    custom_holiday_name: z
      .string()
      .transform((v) => v.trim() || undefined)
      .optional(),
    year: z.coerce.number().int().positive().optional(),
  })
  .refine(
    (data) =>
      data.holiday_name !== 'custom' ||
      (data.custom_holiday_name && data.custom_holiday_name.trim().length > 0),
    { message: 'Custom holiday name is required', path: ['custom_holiday_name'] }
  )

export const birthdayDetailSchema = z.object({
  birthday_person_id: z.string().optional(),
  birthday_person_name: z.string().min(1, 'Birthday person name is required'),
  birth_date: z.string().optional(),
  age_turning: z.coerce.number().int().positive().optional(),
  is_secret: z.boolean().default(false),
  theme: optionalString,
})

export const babyShowerDetailSchema = z.object({
  parent1_name: z.string().min(1, 'Parent name is required').transform((v) => v.trim()),
  parent2_name: optionalString,
  baby_name: optionalString,
  gender: z.enum(['', 'boy', 'girl', 'unknown', 'surprise'])
    .transform((v) => v || undefined)
    .optional(),
  due_date: z.string().optional(),
  registry_url: optionalUrl,
  is_gender_reveal: z.boolean().default(false),
})

export const weddingDetailSchema = z.object({
  partner1_name: z.string().min(1, 'Partner 1 name is required').transform((v) => v.trim()),
  partner2_name: z.string().min(1, 'Partner 2 name is required').transform((v) => v.trim()),
  wedding_date: z.string().optional(),
  venue_name: optionalString,
  registry_url: optionalUrl,
  color_theme: optionalString,
})

export const weddingPartyMemberSchema = z.object({
  name: z.string().min(1, 'Name is required').transform((v) => v.trim()),
  role: z.enum([
    'best_man', 'maid_of_honor', 'bridesmaid', 'groomsman',
    'flower_girl', 'ring_bearer', 'officiant', 'usher', 'other',
  ]),
  side: z.enum(['', 'partner1', 'partner2', 'shared'])
    .transform((v) => v || undefined)
    .optional(),
  user_id: z.string().optional(),
})

// ============================================================================
// Family schemas
// ============================================================================

export const inviteMemberSchema = z.object({
  name: nameSchema,
  email: emailSchema,
})

// ============================================================================
// Wishlist schemas
// ============================================================================

export const wishlistItemSchema = z.object({
  name: z.string().min(1, 'Item name is required').transform((v) => v.trim()),
  description: optionalString,
  url: optionalUrl,
  price_range: z.enum(['', '$', '$$', '$$$']).transform((v) => v || undefined).optional(),
  priority: z.coerce.number().min(1).max(5).default(3),
})

// ============================================================================
// Potluck schemas
// ============================================================================

export const potluckItemSchema = z.object({
  name: z.string().min(1, 'Item name is required').transform((v) => v.trim()),
  category: z
    .enum(['', 'appetizer', 'main', 'side', 'dessert', 'drink', 'other'])
    .transform((v) => v || undefined)
    .optional(),
  description: optionalString,
  serves: optionalPositiveInt,
  dietary_info: optionalString,
  allergens: optionalString,
})

// ============================================================================
// Gift Exchange schemas
// ============================================================================

export const exclusionSchema = z.object({
  member1_id: z.string().min(1, 'Select first member'),
  member2_id: z.string().min(1, 'Select second member'),
}).refine((data) => data.member1_id !== data.member2_id, {
  message: 'Members must be different',
  path: ['member2_id'],
})

export const budgetRulesSchema = z.object({
  budget_min: optionalPositiveInt,
  budget_max: optionalPositiveInt,
  notes: optionalString,
}).refine(
  (data) => {
    if (data.budget_min !== undefined && data.budget_max !== undefined) {
      return data.budget_min <= data.budget_max
    }
    return true
  },
  {
    message: 'Minimum budget cannot exceed maximum',
    path: ['budget_max'],
  }
)

export const giftExchangeMessageSchema = z.object({
  content: z.string().min(1, 'Message cannot be empty').transform((v) => v.trim()),
})

// ============================================================================
// Poll schemas
// ============================================================================

export const pollOptionSchema = z.object({
  text: z.string().min(1, 'Option text is required').max(500, 'Option text must be 500 characters or less'),
})

export const createPollSchema = z.object({
  title: z.string().min(1, 'Title is required').max(300, 'Title must be 300 characters or less').transform((v) => v.trim()),
  description: optionalString,
  allow_multiple: z.boolean().default(false),
  is_anonymous: z.boolean().default(false),
  close_date: z.string().optional(),
  options: z.array(pollOptionSchema).min(2, 'At least 2 options required'),
})

// ============================================================================
// Event Comment schemas
// ============================================================================

export const eventCommentSchema = z.object({
  content: z.string().min(1, 'Comment cannot be empty').max(5000, 'Comment must be 5000 characters or less').transform((v) => v.trim()),
})

// ============================================================================
// Settings schemas
// ============================================================================

export const appSettingsSchema = z.object({
  app_name: z.string().min(1, 'App name is required').transform((v) => v.trim()),
  theme_color: z.string().regex(/^#[0-9A-Fa-f]{6}$/, 'Invalid color format'),
  magic_link_expiry_days: z.coerce
    .number()
    .int()
    .min(1, 'Must be at least 1 day')
    .max(365, 'Cannot exceed 365 days'),
})

export const smtpSettingsSchema = z.object({
  smtp_host: optionalString,
  smtp_port: z
    .string()
    .transform((v) => v.trim() || '587')
    .refine(
      (v) => {
        const port = parseInt(v, 10)
        return !isNaN(port) && port >= 1 && port <= 65535
      },
      { message: 'Port must be between 1 and 65535' }
    ),
  smtp_username: optionalString,
  smtp_password: optionalString,
  smtp_from_email: z
    .string()
    .email('Please enter a valid email')
    .or(z.literal(''))
    .transform((v) => v || undefined)
    .optional(),
  smtp_from_name: optionalString,
  smtp_use_tls: z.boolean().default(true),
})

// ============================================================================
// Type exports
// ============================================================================

export type LoginInput = z.infer<typeof loginSchema>
export type RegisterInput = z.infer<typeof registerSchema>
export type SetupInput = z.infer<typeof setupSchema>
export type ForgotPasswordInput = z.infer<typeof forgotPasswordSchema>
export type ResetPasswordInput = z.infer<typeof resetPasswordSchema>
export type EventTypeInput = z.infer<typeof eventTypeSchema>
export type EventFormInput = z.infer<typeof eventFormSchema>
export type HolidayDetailInput = z.infer<typeof holidayDetailSchema>
export type BirthdayDetailInput = z.infer<typeof birthdayDetailSchema>
export type BabyShowerDetailInput = z.infer<typeof babyShowerDetailSchema>
export type WeddingDetailInput = z.infer<typeof weddingDetailSchema>
export type WeddingPartyMemberInput = z.infer<typeof weddingPartyMemberSchema>
export type InviteMemberInput = z.infer<typeof inviteMemberSchema>
export type WishlistItemInput = z.infer<typeof wishlistItemSchema>
export type PotluckItemInput = z.infer<typeof potluckItemSchema>
export type ExclusionInput = z.infer<typeof exclusionSchema>
export type BudgetRulesInput = z.infer<typeof budgetRulesSchema>
export type GiftExchangeMessageInput = z.infer<typeof giftExchangeMessageSchema>
export type AppSettingsInput = z.infer<typeof appSettingsSchema>
export type SmtpSettingsInput = z.infer<typeof smtpSettingsSchema>

export type CreatePollInput = z.infer<typeof createPollSchema>
export type PollOptionInput = z.infer<typeof pollOptionSchema>
export type EventCommentInput = z.infer<typeof eventCommentSchema>

// Legacy type aliases
export type MagicLinkInput = ForgotPasswordInput
export type OrganizerLoginInput = LoginInput
export type JoinFamilyInput = RegisterInput
