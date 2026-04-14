# Changelog

All notable changes to FamilyCircle will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Dev Dependencies
- **@vitest/coverage-v8**: 4.1.2 → 4.1.4
- **@vitest/ui**: 4.1.2 → 4.1.4
- **globals**: 17.4.0 → 17.5.0
- **jsdom**: 29.0.1 → 29.0.2
- **pyright**: 1.1.400 → 1.1.408
- **pytest**: 9.0.2 → 9.0.3
- **typescript-eslint**: 8.58.0 → 8.58.2
- **vite**: 8.0.3 → 8.0.8
- **vitest**: 4.1.2 → 4.1.4

### App Dependencies
- **@tanstack/react-query**: 5.96.2 → 5.99.0
- **lucide-react**: 1.7.0 → 1.8.0
- **react**: 19.2.4 → 19.2.5
- **react-dom**: 19.2.4 → 19.2.5
- **react-router-dom**: 7.14.0 → 7.14.1

### Dockerfile Dependencies
- **oven/bun**: 1.3.11-alpine → 1.3.12-alpine

### HTTP Servers
- **granian**: 2.7.2 → 2.7.3

## [3.2.0] - 2026-04-05

### Security
- Gate password reset dev_token behind DEBUG mode
- Cookie-only auth — remove session tokens from JSON responses
- Authenticated photo serving — replace public /uploads with authorized endpoint
- Rate limiting on login, register, and forgot-password endpoints
- Require `PUBLIC_BASE_URL` in production (startup-validated)
- Reduce default magic link expiry from 90 days to 1 day
- Path traversal protection in file deletion
- Use `secrets` module for family code generation
- Notification dispatch method allowlist

### Added
- `slowapi` rate limiting with proxy-aware `TRUSTED_PROXY_CIDRS` support
- `PUBLIC_BASE_URL` env var for canonical email link generation

### Dev Dependencies
- **eslint**: 10.1.0 → 10.2.0
- **pytest-cov**: 7.0.0 → 7.1.0
- **ruff**: 0.15.8 → 0.15.9
- **typescript-eslint**: 8.57.2 → 8.58.0

### App Dependencies
- **@tanstack/react-query**: 5.95.2 → 5.96.2
- **fastapi**: 0.135.2 → 0.135.3
- **react-hook-form**: 7.72.0 → 7.72.1
- **react-router-dom**: 7.13.2 → 7.14.0

## [3.1.0] - 2026-03-28

### Dev Dependencies
- **@tailwindcss/vite**: 4.2.1 → 4.2.2
- **@vitejs/plugin-react**: 5.1.4 → 6.0.1
- **@vitest/ui**: 4.0.18 → 4.1.2
- **eslint**: 10.0.2 → 10.1.0
- **globals**: 17.3.0 → 17.4.0
- **jsdom**: 28.1.0 → 29.0.1
- **ruff**: 0.15.4 → 0.15.8
- **tailwindcss**: 4.2.1 → 4.2.2
- **typescript**: 5.9.3 → 6.0.2
- **typescript-eslint**: 8.56.1 → 8.57.2
- **vite**: 7.3.1 → 8.0.3
- **vitest**: 4.0.18 → 4.1.2

### App Dependencies
- **@tanstack/react-query**: 5.90.21 → 5.95.2
- **fastapi**: 0.134.0 → 0.135.2
- **lucide-react**: 0.575.0 → 1.7.0
- **react-router-dom**: 7.13.1 → 7.13.2
- **sqlalchemy**: 2.0.47 → 2.0.48

### Dockerfile Dependencies
- **oven/bun**: 1.3.10-alpine → 1.3.11-alpine

### Added
- Delete family (super admin only) with orphan-guard safety check
- Manage Families modal in Admin panel showing all families with member counts
- Auto-switch users to their next family when their active family is deleted

### Fixed
- Removing a user's last family membership no longer orphans them (400 guard added)

### Added
- Event detail handler registry for pluggable event types
- Token table with multi-session support (dual-write migration)
- Typed SettingsService (SmtpConfig, AppConfig, NotificationRetryConfig)
- Background notification helper via FastAPI BackgroundTasks
- `notify_family_member_joined` for register and admin invite flows
- TanStack Query hooks for all data fetching (5 query + 5 mutation modules)
- Backend test coverage: 133 tests (up from 13), including API lifecycle integration tests
- Frontend test coverage: 43 tests covering auth, events, hooks, and API client
- Daily expired token cleanup job
- httpOnly cookie authentication with bearer token fallback for API clients
- Compound database indexes on events(family_id, event_date) and event_rsvps(event_id, user_id)
- `openapi-typescript` pipeline for generated frontend types from OpenAPI schema
- `.env.example` for new developer setup
- `NotificationCategory` dataclass replacing parallel dispatcher dicts
- `constants.py` and `constants.ts` for application-wide magic numbers

### Changed
- Event type branching replaced with registry pattern across events, validation, and recurrence
- Notification dispatch moved from synchronous to BackgroundTasks with own db session
- Auth helpers are now flush-only; single commit at request boundary for transaction atomicity
- Auth token storage uses Token table exclusively (legacy User column dual-write removed)
- Auth lookups split into lightweight (identity-only) and family-loaded (for user responses)
- All Event model relationships changed to `lazy="raise"` with explicit per-endpoint loading
- Renamed `secret_santa` columns/fields to `gift_exchange` across backend and frontend
- `current_family_id` now has a foreign key constraint to families(id) with ON DELETE SET NULL
- Frontend `api.ts` split into 19 per-domain modules under `src/lib/api/`
- `CreateEventModal` split from 2,050-line monolith into 13 focused components
- CORS origins configurable via `CORS_ORIGINS` environment variable
- Query cache invalidation targeted per event for cancel/RSVP mutations
- Frontend auth uses `credentials: 'include'` instead of manual token headers
- Pydantic schemas migrated from `class Config` to `model_config = ConfigDict()`
- Forms migrated from custom `useZodForm` to `react-hook-form` with Zod resolver
- Version in `__init__.py` corrected from 1.0.0 to 3.0.0

### Fixed
- Wishlist schema module updated to match live API fields (was stale dead code)
- Backend password validation now enforces min_length=6 (matching frontend Zod schema)
- Auth flows (register, setup) are now atomic — partial failures roll back completely

### Removed
- Legacy session/magic token fallback code paths in auth service
- `Dockerfile.backup` artifact from repository
- Custom `useZodForm` hook (replaced by `react-hook-form`)

## [3.0.0] - 2026-03-10

### Added
- **Event types**: Specialized support for birthdays, baby showers, weddings, and holidays with type-specific detail models and schemas
- **Polls and voting**: Create polls on events with multiple choice options, vote tracking, and deadline support
- **Poll templates**: Reusable poll templates for common event decisions (venue, date, menu, etc.)
- **Comment threads**: Threaded comments on events with Markdown support via react-markdown
- **Comment reactions**: Emoji reactions on comments with per-user tracking
- **@mentions**: Tag family members in comments with mention parsing and notification delivery
- **Event photos**: Photo uploads with file storage service, per-event galleries, and image validation via python-magic
- **iCal calendar feeds**: Per-user calendar feed tokens for subscribing to family events in any calendar app via icalendar library
- **Notification system**: Background scheduler (APScheduler) for event reminders with per-user notification preferences and email delivery
- **Registry items**: Gift registry for baby showers and weddings with claiming support
- **RSVP guest management**: Attendees can add plus-ones and named guests to RSVPs
- **Event recurrences**: Recurring event support with configurable frequency and automatic instance generation via python-dateutil
- **Event templates**: Save and reuse event configurations as templates
- **Baby shower updates**: Post updates to baby shower events with timeline tracking
- **Wedding party permissions**: Role-based access control for wedding event management
- **Wedding templates**: Pre-built wedding event templates with ceremony/reception structure
- **Settings page enhancements**: Expanded admin settings with notification configuration and calendar feed management
- New backend dependencies: `apscheduler`, `python-magic`, `icalendar`, `python-dateutil`
- 14 new database migrations (004-017) for all feature additions

### Changed
- **BREAKING**: Renamed "Secret Santa" to "Gift Exchange" throughout the application (API endpoints, models, schemas, services, and UI)
- **BREAKING**: Removed `/api/secret-santa/*` endpoints; replaced by `/api/gift-exchange/*`
- Deleted `secret_santa.py` model, schema, service, and API modules; replaced by `gift_exchange.py` equivalents
- Event creation modal expanded with type-specific fields for each event category
- Event detail page enhanced with tabbed interface for comments, photos, polls, and registry
- Events list page updated with type filtering and enhanced card display
- Dashboard updated with richer upcoming event previews
- Permissions service expanded for event-type-specific access control

### Fixed
- Toggle switch knob positioning and off-state color
- Missing `has_rsvp`, `potluck_mode`, `potluck_host_providing` fields in EventCreate schema causing 500 on event creation
- MissingGreenlet 500 error on event list/detail endpoints caused by async lazy-load of `sub_events`; added explicit `selectinload` to all `event_to_dict` call paths
- Broken `/api/auth/magic-link` backwards-compat endpoint passing `db` as `req`, causing AttributeError on password reset for existing users

### HTTP Servers
- **granian**: 2.7.1 → 2.7.2

### Dev Dependencies
- **@eslint/js**: 9.39.2 → 10.0.1
- **@types/react**: 19.2.10 → 19.2.14
- **@vitejs/plugin-react**: 5.1.2 → 5.1.4
- **eslint**: 9.39.2 → 10.0.2
- **eslint-plugin-react-refresh**: 0.4.26 → 0.5.2
- **jsdom**: 27.4.0 → 28.1.0
- **ruff**: 0.14.14 → 0.15.4
- **tailwindcss**: 4.1.18 → 4.2.1
- **@tailwindcss/vite**: 4.1.18 → 4.2.1
- **typescript-eslint**: 8.54.0 → 8.56.1

### App Dependencies
- **@tanstack/react-query**: 5.90.20 → 5.90.21
- **aiosqlite**: 0.21.0 → 0.22.1
- **fastapi**: 0.121.0 → 0.134.0
- **granian**: 2.7.0 → 2.7.2
- **lucide-react**: 0.563.0 → 0.575.0
- **react-router-dom**: 7.13.0 → 7.13.1
- **sqlalchemy**: 2.0.44 → 2.0.47

### Dockerfile Dependencies
- **oven/bun**: 1.3.8-alpine → 1.3.10-alpine

## [2.1.0] - 2025-02-01

### Dev Dependencies
- **@testing-library/react**: 16.3.1 -> 16.3.2
- **@types/react**: 19.2.7 -> 19.2.10
- **@vitest/ui**: 4.0.16 -> 4.0.18
- **globals**: 16.5.0 -> 17.3.0
- **ruff**: 0.14.10 -> 0.14.14
- **typescript-eslint**: 8.50.1 -> 8.54.0
- **vite**: 7.3.0 -> 7.3.1
- **vitest**: 4.0.16 -> 4.0.18

### App Dependencies
- **@tanstack/react-query**: 5.90.13 -> 5.90.20
- **lucide-react**: 0.562.0 -> 0.563.0
- **react**: 19.2.3 -> 19.2.4
- **react-dom**: 19.2.3 -> 19.2.4
- **react-router-dom**: 7.11.0 -> 7.13.0
- **zod**: 4.2.1 -> 4.3.6

### Dockerfile Dependencies
- **oven/bun**: 1.3.5-alpine -> 1.3.8-alpine

### Added
- Vitest test runner with React Testing Library
- Frontend test infrastructure with jsdom and coverage reporting
- Example test suite demonstrating testing capabilities

### Changed
- Migrated frontend build from Node.js 24 to Bun 1.3.5
- Upgraded pytest from 8.5.0 to 9.0.2
- Upgraded pytest-asyncio from 0.26.0 to 1.3.0

### Performance
- Frontend builds ~4-7x faster with Bun package manager
- Improved async test handling with pytest-asyncio 1.3.0

## [2.0.1] - 2025-11-29

### Changed
- Admin panel converted from separate pages to modal dialogs
- All admin functions now open as overlays with blurred backdrop
- Removed admin sub-routes (`/admin/events`, `/admin/secret-santa`, `/admin/potluck`, `/admin/family`, `/admin/settings`)

### Added
- ManageEventsModal component for event CRUD operations
- SecretSantaModal component for assignment management
- PotluckModal component for potluck item management
- FamilyMembersModal component for member management and invitations
- AppSettingsModal component for app customization and settings

### Removed
- AdminEvents.tsx, AdminSecretSanta.tsx, AdminPotluck.tsx, AdminFamily.tsx, AdminSettings.tsx pages
- SuperAdminRoute wrapper (no longer needed)

## [2.0.0] - 2025-11-29

### Added
- **Multi-family support**: Users can now belong to multiple families
- New User model replacing old Member model for authentication
- Family model for managing family groups
- FamilyMembership model linking users to families with roles
- UserProfile model for extended profile data (phone, address, health info)
- ProfileVisibility model for per-family privacy settings
- Family selector in header for users with multiple families
- Profile page with contact info, address, and health information
- Health info sharing toggle with privacy controls
- Per-family visibility settings (email, phone, address)
- Event cancellation with optional reason
- Health summary for event organizers (anonymous aggregate of attendee health info)
- Password-based authentication (replaces magic-link-only for primary auth)
- Password reset flow via magic link
- Super admin role for platform-wide management
- Family admin role for per-family management
- Create new family feature for super admins
- Email settings configuration for super admins
- Cancelled event retention setting

### Changed
- Complete database schema redesign for multi-tenancy
- Authentication flow: email + password (magic links for password recovery only)
- Login page redesigned with login/register/forgot password views
- Setup wizard now creates super admin + first family
- Family page enhanced as address book with privacy indicators
- All API endpoints scoped by family_id
- Version bumped to 2.0.0

### Fixed
- Theme sync issues between Settings and quick access toggles
- Setup wizard visibility issues (CSS class fixes)
- Password input losing focus while typing

## [1.3.0] - 2025-11-29

### Added
- Zod schema validation library for type-safe form validation
- Custom `useZodForm` hook for consistent form handling across the app
- Client-side validation with inline error messages for all forms:
  - Login forms (magic link, organizer, join family)
  - Setup wizard
  - Wishlist items
- Comprehensive validation schemas for all form types in `lib/schemas.ts`

### Changed
- Login, Setup, and Wishlist forms now use Zod validation
- Form errors display inline below fields with visual feedback (red borders)
- Improved form UX with immediate validation feedback

## [1.2.0] - 2025-11-29

### Added
- Automated Python-based database migration system (runs on container startup)
- Secret Santa budget rules support (min/max values per event)
- Potluck dietary info and allergen fields
- Admin SMTP/email configuration settings UI

### Fixed
- Secret Santa "Send Anonymous Message" button now works correctly
- Clipboard copy fallback for non-HTTPS environments (family code, magic links)
- SQLite columns now auto-created via migration system

### Changed
- Updated all frontend dependencies to latest versions:
  - React 19.2.0, Vite 7.2.4, TypeScript 5.9.3
  - @vitejs/plugin-react 5.1.1 (uses Oxc for faster builds)
  - eslint-plugin-react-hooks 7.0.1
  - TanStack Query 5.90.11
  - Tailwind CSS 4.1.17
  - All other dependencies updated to latest patch versions
- ESLint configuration updated for react-hooks v7 compatibility

## [1.1.0] - 2025-11-29

### Added
- Admin Potluck management page for organizers (add, edit, delete items)
- Remove RSVP functionality (click same RSVP button to toggle off)
- Organizers can unclaim potluck items from other members

### Changed
- Error messages now context-specific throughout backend API
- Frontend passes through backend error messages instead of generic fallbacks
- Improved error clarity for authentication, events, family, settings, secret santa, potluck, and wishlist operations

## [1.0.0] - 2025-11-29

### Added
- Card-based dashboard UI optimized for elderly users
- Big Mode toggle for enhanced accessibility (larger fonts, bigger touch targets)
- Dark/Light/System theme support with Teal color palette
- Secret Santa management with derangement assignment algorithm
- Secret Santa exclusion rules (e.g., spouses can't be paired)
- Anonymous Secret Santa messaging between giver and receiver
- Potluck coordination with category support (appetizer, main, side, dessert, drink)
- Potluck item claiming/unclaiming system
- Event management with RSVP tracking (yes/no/maybe)
- Gift wishlists with priority levels and price ranges
- Family member directory
- Magic link authentication (90-day expiry, no passwords for participants)
- Password authentication for organizers
- Family join code for easy onboarding
- Organizer-only admin panel with:
  - Event CRUD management
  - Secret Santa assignment runner
  - Family member invitations
  - Toggle organizer permissions
  - App settings (name, theme, magic link expiry)
  - Family code regeneration
- User preference sync (theme, Big Mode)
- Error boundaries for graceful error handling
- 404 Not Found page
- Loading states and empty states throughout
- Toast notifications for user feedback
- SQLite database with WAL mode for concurrent access
- Multi-stage Docker build (Python 3.14 + Node 24)
- FastAPI backend with async SQLAlchemy (aiosqlite)
- Granian ASGI server for high performance
- React 19 + Vite 7 + Tailwind CSS 4 frontend
- TanStack Query for data fetching
- Code splitting with React lazy loading
