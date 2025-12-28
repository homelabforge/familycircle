# FamilyCircle - Project Overview

**Project Name:** FamilyCircle  
**Version:** 1.0.0  
**Status:** Development  
**Last Updated:** November 2025

---

## Purpose

FamilyCircle is a family event coordination platform designed specifically for elderly users who need simple, password-free access to manage family gatherings, Secret Santa exchanges, and potluck dinners.

---

## Target Users

### Primary: Elderly Family Members
- Non-technical users who struggle with passwords
- Need large, clear interfaces with accessible design
- Prefer email-based access (magic links)
- Want to participate in family events without complex registration

### Secondary: Family Organizers
- Tech-savvy family members who plan events
- Need tools to coordinate Secret Santa, potlucks, birthdays, and other popular events
- Want to track RSVPs and contributions
- Require automated email reminders

---

## Key Features

1. **Magic Link Authentication** - Participants click email links - no passwords required
2. **Family Code Join** - Simple 6-character code (e.g., `SMITH-24`) for easy family joining without email hunting
3. **Secret Santa Management** - Smart algorithm handles assignments, exclusions, repeat prevention
4. **Potluck Coordination** - Track contributions with dietary information
5. **RSVP Tracking** - Simple yes/no/maybe responses
6. **Gift Wishlists** - Easy wishlist creation for Secret Santa
7. **Anonymous Messaging** - Secret Santa pairs can communicate privately
8. **Email Automation** - Invitations, reminders, and assignment notifications
9. **QR Code Sharing** - Generate QR codes for events/invites (printable for easy sharing)
10. **Big Mode** - Accessibility toggle for enhanced readability (larger text, bigger touch targets)
11. **Offline Event Cache** - View event details, assignments, and contributions without internet

---

## Technology Stack (Latest Stable Versions)

### Backend

| Technology | Version | Notes |
|------------|---------|-------|
| **Python** | 3.14.x | Released Oct 2025. Features: deferred annotations, t-strings, free-threading support, Zstandard compression |
| **FastAPI** | Latest | Modern async framework |
| **Granian** | 2.6.x | Rust-based ASGI server with free-threaded Python support since v2.0 |
| **SQLite** | Latest | Single-file database |
| **Pydantic** | v2 | Data validation |

### Frontend

| Technology | Version | Notes |
|------------|---------|-------|
| **Node.js** | 24.x LTS "Krypton" | Released Oct 2025. LTS support through Apr 2028 |
| **Vite** | 7.x | ESM-only distribution. Requires Node.js 20.19+ or 22.12+ |
| **TypeScript** | 5.x | Latest stable |
| **Tailwind CSS** | 4.x | Ground-up rewrite with Rust engine, 5x faster builds |
| **React** | 19.x | Latest stable |

### Docker Base Images

| Stage | Image | Notes |
|-------|-------|-------|
| Frontend Builder | `node:24-alpine` | LTS "Krypton" |
| Backend Builder | `python:3.14-slim` | Smallest viable Python image |
| Production | `python:3.14-slim` | Runtime-only dependencies |

---

## Theme System

### Design Philosophy
Clean, accessible design with full dark/light mode support. Theme preference is stored per-user in the database and respects system preference as default.

### Color Palette

#### Light Theme
| Role | Color | Tailwind | Usage |
|------|-------|----------|-------|
| **Primary** | Teal 600 | `bg-teal-600` | Buttons, links, accents |
| **Primary Hover** | Teal 700 | `hover:bg-teal-700` | Interactive states |
| **Background** | White | `bg-white` | Page background |
| **Surface** | Gray 50 | `bg-gray-50` | Cards, panels |
| **Border** | Gray 200 | `border-gray-200` | Dividers, inputs |
| **Text** | Gray 900 | `text-gray-900` | Primary text |
| **Text Muted** | Gray 600 | `text-gray-600` | Secondary text |
| **Success** | Green 600 | `text-green-600` | Confirmations |
| **Warning** | Amber 600 | `text-amber-600` | Cautions |
| **Error** | Red 600 | `text-red-600` | Errors, destructive |

#### Dark Theme
| Role | Color | Tailwind | Usage |
|------|-------|----------|-------|
| **Primary** | Teal 400 | `dark:bg-teal-400` | Buttons, links, accents |
| **Primary Hover** | Teal 300 | `dark:hover:bg-teal-300` | Interactive states |
| **Background** | Gray 950 | `dark:bg-gray-950` | Page background |
| **Surface** | Gray 900 | `dark:bg-gray-900` | Cards, panels |
| **Border** | Gray 700 | `dark:border-gray-700` | Dividers, inputs |
| **Text** | Gray 100 | `dark:text-gray-100` | Primary text |
| **Text Muted** | Gray 400 | `dark:text-gray-400` | Secondary text |
| **Success** | Green 400 | `dark:text-green-400` | Confirmations |
| **Warning** | Amber 400 | `dark:text-amber-400` | Cautions |
| **Error** | Red 400 | `dark:text-red-400` | Errors, destructive |

#### Alternative: Rose Theme
If Teal feels too clinical, swap to Rose for a warmer family vibe:
- Light primary: `rose-600` / Dark primary: `rose-400`
- Configurable in Settings (theme color preference)

### Implementation
```css
/* src/index.css */
@import "tailwindcss";

@theme {
  --color-primary: var(--color-indigo-600);
  --color-surface: var(--color-gray-50);
  /* ... custom semantic tokens */
}
```

```typescript
// Theme toggle uses class strategy
document.documentElement.classList.toggle('dark');
```

### Theme Modes
| Mode | Behavior |
|------|----------|
| `light` | Always light theme |
| `dark` | Always dark theme |
| `system` | Follows OS preference via `prefers-color-scheme` |

---

### Database: SQLite (not PostgreSQL)
**Why:**
- Family-scale application (dozens of users, not thousands)
- Low concurrent write requirements
- Simplified deployment and backups
- Single-file database is trivial to manage and backup
- No need for PostgreSQL-specific features
- WAL mode for concurrent reads and safe writes

**Required PRAGMA settings (applied on every connection):**
```sql
PRAGMA journal_mode=WAL;
PRAGMA busy_timeout=5000;
PRAGMA foreign_keys=ON;
PRAGMA synchronous=NORMAL;
```

### Frontend: Vite 7 + TypeScript + Tailwind CSS 4
**Why Vite 7:**
- ESM-only distribution aligns with modern JS ecosystem
- Baseline Widely Available browser targeting
- 10-100x faster than alternatives like CRA
- Superior HMR (Hot Module Replacement)
- Native TypeScript support
- Smaller production bundles

**Why Tailwind CSS 4:**
- Ground-up rewrite with Rust-powered engine (Oxide)
- Full builds 5x faster, incremental builds 100x faster
- Zero-config content detection (auto-ignores .gitignore patterns)
- First-party Vite plugin (`@tailwindcss/vite`)
- Modern CSS features: cascade layers, `@property`, `color-mix()`
- CSS-based configuration (no `tailwind.config.js` required)
- Single `@import "tailwindcss"` setup

### Server: Granian 2.6.x
**Why:**
- Rust-based ASGI server for superior performance
- 15MB base memory footprint (vs 20-40MB for alternatives)
- 50,000+ req/s in benchmarks (Hello World)
- Native free-threaded Python support (Python 3.14 feature)
- HTTP/1, HTTP/2, and WebSocket support
- Production-grade reliability (used by paperless-ngx, searxng, Weblate, Microsoft, Mozilla, Sentry)
- Still fully compatible with FastAPI

### Python 3.14
**Why:**
- Deferred annotation evaluation (better startup, cleaner type hints)
- Template strings (t-strings) for custom string processing
- Native Zstandard compression (`compression.zstd`)
- Multiple interpreters in stdlib
- Free-threaded support (experimental but promising)
- 3-5% performance improvement with tail-call interpreter
- Security patches through Oct 2030

---

## Architecture

### Multi-Stage Docker Build

```dockerfile
# Stage 1: Frontend Builder
FROM node:24-alpine AS frontend-builder
# Install dependencies, build Vite app

# Stage 2: Backend Builder  
FROM python:3.14-slim AS backend-builder
# Install Python dependencies

# Stage 3: Production
FROM python:3.14-slim AS production
# Copy built frontend assets
# Copy Python dependencies
# Run with Granian
```

### Security
- Non-root user (uid 1000)
- `no-new-privileges` security option
- JWT authentication for organizers
- Time-limited magic links (90-day default, configurable via settings)
- Argon2id password hashing (organizer accounts) - memory-hard, GPU-resistant
- HTTPS required in production
- SECRET_KEY auto-generated and stored in database on first run

### Database Migrations
- Automatic migration runner on application startup
- Schema version tracking in dedicated table
- Idempotent migrations (safe to re-run)
- Inspired by proven patterns (MyGarage)

---

## Development Standards

### Version Control
- Semantic versioning (MAJOR.MINOR.PATCH)
- Version synchronized across:
  - `backend/pyproject.toml`
  - `frontend/package.json`
  - `CHANGELOG.md`
  - Docker labels

### Dependency Policy
**All dependencies must use the latest stable versions.** Before any release:
1. Check PyPI for Python package updates
2. Check npm for Node.js package updates
3. Verify compatibility with base Docker images
4. Run full test suite against updated dependencies
5. Document any breaking changes in CHANGELOG.md

### Docker Naming Convention
| Property | Value |
|----------|-------|
| Service | `familycircle-dev` |
| Container | `familycircle-dev` |
| Image | `familycircle:dev` |
| Port Mapping | `12345:8080` |

### File Structure
```
familycircle/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── api/
│   │   ├── models/
│   │   ├── services/
│   │   └── migrations/
│   ├── pyproject.toml
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── hooks/
│   │   └── utils/
│   ├── package.json
│   ├── vite.config.ts
│   └── index.html
├── compose.yml
├── Dockerfile
├── CHANGELOG.md
└── README.md
```

### Data Persistence
- Database path: `/data/familycircle.db` (hardcoded default)
- Volume mount: `/data/` directory
- Backup strategy: Copy SQLite file (automatic WAL checkpoint)

---

## Deployment

### Development
```bash
# Build and run
docker compose up -d --build

# View logs
docker compose logs -f familycircle-dev

# Rebuild after changes
docker compose up -d --build --force-recreate
```

### Production Checklist
- [ ] Build multi-stage Dockerfile
- [ ] Configure SendGrid/Resend for email delivery
- [ ] Generate and store production `SECRET_KEY` in database
- [ ] Enable SSL/TLS (via Traefik or similar reverse proxy)
- [ ] Configure backup strategy for `/data/` volume
- [ ] Set appropriate magic link expiration
- [ ] Review and adjust rate limiting settings
- [ ] Configure health check endpoints

---

## Technical Debt

| Item | Priority | Notes |
|------|----------|-------|
| Accessibility audit (WCAG 2.1 AA) | High | Critical for elderly users |
| CI/CD pipeline (GitHub Actions) | High | Standard workflow |
| Test suite (pytest + Vitest) | Medium | Basic coverage |
| API documentation (OpenAPI/Swagger) | Low | Nice to have |

---

## Configuration

### Philosophy
**No environment variables unless absolutely necessary.** All configuration is managed through the Settings page in the application UI and stored in the database.

### Database-Stored Settings
| Setting | Default | Description |
|---------|---------|-------------|
| `secret_key` | Auto-generated | JWT signing key (created on first run) |
| `magic_link_expiry_days` | 90 | How long magic links remain valid |
| `family_code` | Auto-generated | 6-char join code (e.g., `SMITH-24`), regenerable |
| `email_from` | (required) | Sender email address |
| `smtp_host` | - | SMTP server hostname |
| `smtp_port` | 587 | SMTP server port |
| `smtp_username` | - | SMTP authentication |
| `smtp_password` | - | SMTP authentication (encrypted) |
| `smtp_use_tls` | true | Enable TLS for email |
| `app_name` | FamilyCircle | Display name in emails/UI |
| `theme` | system | Default theme (light/dark/system) |
| `theme_color` | teal | Primary color (teal/rose) |
| `qr_codes_enabled` | true | Generate QR codes for events/invites |

### Per-User Preferences (stored in database)
| Setting | Default | Description |
|---------|---------|-------------|
| `theme` | system | User's theme preference |
| `big_mode` | false | Enhanced accessibility mode |
| `offline_cache` | true | Cache event details locally |

### Required Environment Variables (Minimal)
Only these are required as env vars since they're needed before the database is accessible:

```bash
# Required - path to SQLite database
DATABASE_PATH=/data/familycircle.db

# Optional - override default port
PORT=8080
```

### First-Run Setup
On first application start:
1. Database is created at `DATABASE_PATH`
2. Migrations run automatically
3. `SECRET_KEY` is generated (64 bytes, cryptographically secure) and stored
4. User is prompted to configure email settings via Settings page

### Granian Configuration
```bash
granian \
  --interface asgi \
  --host 0.0.0.0 \
  --port 8080 \
  --workers 4 \
  --http auto \
  --ws \
  app.main:app
```

---

## Accessibility Considerations

Since the primary users are elderly, the frontend must prioritize:
- **Large touch targets** (minimum 44x44px, 56px in Big Mode)
- **High contrast ratios** (WCAG AAA where possible)
- **Large, readable fonts** (18px minimum base, scalable)
- **Simple navigation** (minimal nesting)
- **Clear error messages** (plain language)
- **Keyboard navigation** (full accessibility)
- **Screen reader compatibility** (proper ARIA labels)

### Big Mode
A single toggle that enhances the entire UI for users who need extra help:

| Normal | Big Mode |
|--------|----------|
| 18px base font | 24px base font (+33%) |
| 44px touch targets | 56px touch targets |
| Standard padding | 1.5x padding |
| Full UI | Simplified (hides secondary info) |

Stored per-user in database, persists across sessions.

---

## Offline Support

### What's Cached
Once a user RSVPs to an event, the following is cached locally via localStorage:
- Event date, time, location
- Their Secret Santa assignment (who they're buying for)
- Their potluck contribution
- Gift wishlist for their assignee

### Implementation
- Service Worker for asset caching
- localStorage for event data (JSON)
- Sync indicator in UI ("Last synced: 5 min ago")
- Auto-sync when connection restored

### Why This Matters
Elderly users often have:
- Spotty wifi/cellular
- Devices that go offline unexpectedly
- Need to reference event details at the grocery store (no signal)

---

## Project History

**Maintainer:** HomeLabForge  
**Website:** https://www.homelabforge.io  
**Repository:** [To be created]

---

## Version History

| Version | Date | Notes |
|---------|------|-------|
| 1.0.0 | TBD | Initial release |

---

## License

MIT
