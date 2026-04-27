# FamilyCircle E2E

Hard release gate. Builds the production image, brings up a SQLite-backed
FamilyCircle instance, and runs an HTTP smoke test.

## Run

```bash
bash tests/e2e/run.sh
```

Takes ~60 seconds on a warm Docker cache (no Docker proxy or PG
sidecar — FamilyCircle is SQLite-only and doesn't talk to Docker).
Always tears down on exit.

## What it covers

- All migrations apply cleanly on a fresh SQLite DB.
- Health endpoint responds.
- Setup → login → cookie-authenticated GET /api/auth/me round-trip.

## Knobs

- `E2E_KEEP=1` — on failure, leave the stack up so you can poke at it.
  Run `bash tests/e2e/teardown.sh` when done.
- `E2E_NO_BUILD=1` — reuse the existing `familycircle:e2e` image.
