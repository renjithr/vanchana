#!/usr/bin/env bash
# Preview the site with inline editing.
#   ./preview.sh             build, serve, open — Edit button enabled
#   ./preview.sh --no-edit   exactly what production gets, no editor at all
set -euo pipefail
cd "$(dirname "$0")"
PORT="${CMS_PORT:-8765}"
lsof -ti tcp:$PORT | xargs kill -9 2>/dev/null || true
( sleep 2; open "http://127.0.0.1:$PORT/" 2>/dev/null || true ) &
exec python3 src/cms_server.py "$@"
