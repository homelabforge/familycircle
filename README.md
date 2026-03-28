<div align="center">

Self-hosted family event coordination with Gift Exchange, potluck management, and accessibility-first design for elderly users.

[![Python 3.14](https://img.shields.io/badge/Python-3.14-3776AB?logo=python&logoColor=white)](https://www.python.org)
[![React 19](https://img.shields.io/badge/React-19-61DAFB?logo=react&logoColor=black)](https://react.dev)
[![Bun 1.3.11](https://img.shields.io/badge/Bun-1.3.11-000000?logo=bun&logoColor=white)](https://bun.sh)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

</div>

---

## Key Features

- **Magic Link Authentication** - Passwordless access for participants via email links
- **Gift Exchange Management** - Smart assignment algorithm with exclusion rules and repeat prevention
- **Potluck Coordination** - Track contributions with dietary info and categories
- **Multi-Family Support** - Users can belong to multiple family groups
- **RSVP Tracking** - Simple yes/no/maybe responses for events
- **Gift Wishlists** - Easy wishlist creation with priority and price ranges
- **Anonymous Messaging** - Gift Exchange pairs can communicate privately
- **Big Mode** - Accessibility toggle for enhanced readability (larger text, bigger touch targets)
- **Dark/Light Themes** - Full theme support with system preference detection
- **Self-Hosted** - Your family data stays on your infrastructure

---

**Target Audience**: Designed specifically for elderly users who need simple, accessible interfaces without complex registration flows.

---

## Technology Stack

| Component | Technology |
|-----------|------------|
| Backend | Python 3.14, FastAPI, Granian (ASGI) |
| Frontend | React 19, TypeScript, Vite 7, Tailwind CSS 4 |
| Database | SQLite with WAL mode |
| Package Manager | Bun 1.3.8 |
| Authentication | JWT + Argon2id password hashing |

---

## Quick Start

```yaml
# docker-compose.yml
services:
  familycircle:
    image: familycircle:latest
    container_name: familycircle
    environment:
      - DATABASE_PATH=/data/familycircle.db
    volumes:
      - familycircle-data:/data
    ports:
      - "8080:8080"
```

On first startup, you'll be guided through a setup wizard to create a super admin account and your first family.

---

## Configuration

FamilyCircle uses database-stored settings managed through the Settings UI:

| Setting | Default | Description |
|---------|---------|-------------|
| `magic_link_expiry_days` | 90 | How long magic links remain valid |
| `family_code` | Auto-generated | 6-character join code (e.g., `SMITH-24`) |
| `theme` | system | Default theme (light/dark/system) |
| `theme_color` | teal | Primary color (teal/rose) |

Email settings (SMTP) are configured via the admin Settings page.

---

## Accessibility

Since the primary users are elderly, the frontend prioritizes:

- **Large touch targets** (minimum 44x44px, 56px in Big Mode)
- **High contrast ratios** (WCAG AA/AAA)
- **Large, readable fonts** (18px minimum, scalable)
- **Simple navigation** (minimal nesting)
- **Keyboard navigation** (full accessibility)
- **Screen reader compatibility** (proper ARIA labels)

---

## License

MIT License - see [LICENSE](LICENSE) file for details.

---

## Acknowledgments

Built for families who want to coordinate events without sending personal data to third-party services.

### Development Assistance

FamilyCircle was developed through AI-assisted pair programming with **Claude**, combining human vision with AI capabilities for architecture, accessibility patterns, and implementation.
