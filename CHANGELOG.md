# Changelog

All notable changes to FamilyCircle will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
