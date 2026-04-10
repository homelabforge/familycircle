#!/usr/bin/env bash
# Security tripwire: catches raw Event lookups that bypass
# resolve_event_or_404() tenant boundary enforcement in route handlers.
# event_helpers.py is exempt (it defines the helper itself).
# polls.py is exempt (batch .in_() query after per-event auth).
set -euo pipefail

FOUND=0
if grep -rPn 'select\(Event\)\.where\(Event\.id' backend/app/api/ | grep -v 'event_helpers.py' | grep -v 'polls.py'; then
  echo "ERROR: Found raw Event queries in route files."
  echo "Use resolve_event_or_404() instead. See: backend/app/api/event_helpers.py"
  FOUND=1
fi
exit $FOUND
