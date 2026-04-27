#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
docker compose -p familycircle-release-smoke -f "$HERE/compose.yml" down -v --remove-orphans
