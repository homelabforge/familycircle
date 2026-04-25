"""End-to-end smoke test for FamilyCircle.

Verifies the high-value paths that unit tests can't catch:

- Health endpoint responds.
- Setup flow: POST /api/auth/setup creates super admin + first family.
- Login flow: POST /api/auth/login sets the session cookie.
- Authenticated GET /api/auth/me round-trips the session cookie.

FamilyCircle uses httpOnly session cookies, not JWT tokens. httpx's
Client carries cookies between requests automatically.

Usage:
    python smoke.py http://app:8080
"""

from __future__ import annotations

import sys

import httpx


def banner(msg: str) -> None:
    print(f"\n=== {msg} ===")


def main(base: str) -> int:
    fails = 0
    with httpx.Client(base_url=base, timeout=20.0, follow_redirects=True) as c:
        banner("Health check")
        r = c.get("/api/health")
        print(f"  GET /api/health -> {r.status_code}")
        if r.status_code != 200:
            print("  body:", r.text[:200])
            return 1

        banner("Initial setup (super admin + first family)")
        r = c.post(
            "/api/auth/setup",
            json={
                "email": "smoke@example.com",
                "password": "SmokePass123!",
                "display_name": "Smoke Test",
                "family_name": "Smoke Family",
            },
        )
        print(f"  POST /api/auth/setup -> {r.status_code}")
        if r.status_code != 200:
            print("  body:", r.text[:300])
            return 1
        # Setup also sets the session cookie, but log in explicitly to
        # exercise the login path too.

        banner("Login")
        r = c.post(
            "/api/auth/login",
            json={"email": "smoke@example.com", "password": "SmokePass123!"},
        )
        print(f"  POST /api/auth/login -> {r.status_code}")
        if r.status_code != 200:
            print("  body:", r.text[:200])
            return 1
        # Confirm a session cookie was set.
        cookies = list(c.cookies.jar)
        if not cookies:
            print("  ✗ login did not set any cookies")
            return 1
        print(f"  ✓ session cookie set ({cookies[0].name})")

        banner("Authenticated GET /api/auth/me")
        r = c.get("/api/auth/me")
        print(f"  GET /api/auth/me -> {r.status_code}")
        if r.status_code != 200:
            print("  body:", r.text[:200])
            fails += 1
        else:
            data = r.json()
            print(f"  ✓ /me returned user with email: {data.get('email')}")

    banner("RESULT")
    if fails:
        print(f"  ✗ {fails} check(s) failed")
        return 1
    print("  ✓ all checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8080"))
