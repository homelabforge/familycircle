"""Export OpenAPI schema from FastAPI app for frontend type generation.

Usage: PYTHONPATH=. python3 scripts/export_openapi.py <output_path>

FamilyCircle-specific: Sets DATABASE_PATH to a temp file to avoid
touching /data/ or running migrations during schema export.
"""

import json
import logging
import os
import sys
import tempfile
from pathlib import Path

from starlette.staticfiles import StaticFiles

# Suppress app startup logs
logging.disable(logging.WARNING)

# Set DATABASE_PATH to temp to avoid touching production data
_tmpdir = tempfile.TemporaryDirectory(prefix="familycircle-openapi-")
_tmp = _tmpdir.name
os.environ["DATABASE_PATH"] = os.path.join(_tmp, "openapi.db")

# Patch Path.mkdir and StaticFiles to avoid touching /data/ at module level
_orig_mkdir = Path.mkdir


def _patched_mkdir(self, *args, **kwargs):
    if str(self).startswith("/data"):
        Path(_tmp, "uploads").mkdir(parents=True, exist_ok=True)
        return
    return _orig_mkdir(self, *args, **kwargs)


_orig_staticfiles_init = StaticFiles.__init__


def _patched_staticfiles_init(self, *args, **kwargs):
    directory = kwargs.get("directory") or (args[0] if args else None)
    if directory and str(directory).startswith("/data"):
        kwargs["directory"] = str(Path(_tmp, "uploads"))
        if args:
            args = (str(Path(_tmp, "uploads")),) + args[1:]
    return _orig_staticfiles_init(self, *args, **kwargs)


Path.mkdir = _patched_mkdir  # type: ignore[assignment]
StaticFiles.__init__ = _patched_staticfiles_init  # type: ignore[assignment]

try:
    from app.main import app

    schema = app.openapi()
except Exception as e:
    print(f"ERROR: Failed to generate OpenAPI schema: {e}", file=sys.stderr)
    sys.exit(1)
finally:
    Path.mkdir = _orig_mkdir  # type: ignore[assignment]
    StaticFiles.__init__ = _orig_staticfiles_init  # type: ignore[assignment]
    _tmpdir.cleanup()

output = json.dumps(schema, indent=2, sort_keys=True) + "\n"

if len(sys.argv) < 2:
    print(output, end="")
    sys.exit(0)

output_path = os.path.abspath(sys.argv[1])
output_dir = os.path.dirname(output_path)

tmp_path: str | None = None
try:
    fd, tmp_path = tempfile.mkstemp(dir=output_dir, suffix=".json.tmp")
    with os.fdopen(fd, "w") as f:
        f.write(output)
    os.replace(tmp_path, output_path)
except Exception as e:
    if tmp_path is not None and os.path.exists(tmp_path):
        os.unlink(tmp_path)
    print(f"ERROR: Failed to write {output_path}: {e}", file=sys.stderr)
    sys.exit(1)
