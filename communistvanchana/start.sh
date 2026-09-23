#!/usr/bin/env bash
# Start the preview server in the background and return the terminal to you.
#
#   ./start.sh              build, serve, open a browser — Edit button enabled
#   ./start.sh --no-edit    exactly what production gets, no editor at all
#   ./start.sh --no-open    leave the browser alone
#
# Stop it again with ./stop.sh. Use ./preview.sh instead if you want the server
# in the foreground with its log on screen.
set -euo pipefail
cd "$(dirname "$0")"

PORT="${CMS_PORT:-8765}"
RUN=".preview"
PIDFILE="$RUN/server.pid"
LOG="$RUN/server.log"
mkdir -p "$RUN"

OPEN=1
EDIT="ON — click Edit at the bottom of the page"
ARGS=()
for a in "$@"; do
  case "$a" in
    --no-open) OPEN=0 ;;
    --no-edit) EDIT="OFF — this is exactly what production gets"; ARGS+=("$a") ;;
    *)         ARGS+=("$a") ;;
  esac
done

# never leave two servers fighting over the same port
./stop.sh --quiet

: > "$LOG"
CMS_PORT="$PORT" nohup python3 -u src/cms_server.py ${ARGS[@]+"${ARGS[@]}"} >>"$LOG" 2>&1 &
PID=$!
echo "$PID" > "$PIDFILE"

# Wait until it is really serving. A failed build must not look like a success,
# so bail out and show the log rather than printing a URL that answers nothing.
READY=0
for _ in $(seq 1 60); do
  if ! kill -0 "$PID" 2>/dev/null; then
    echo "the server exited during startup:" >&2
    sed 's/^/  /' "$LOG" >&2
    rm -f "$PIDFILE"
    exit 1
  fi
  if curl -fsS -o /dev/null "http://127.0.0.1:$PORT/" 2>/dev/null; then
    READY=1
    break
  fi
  sleep 0.25
done

if [ "$READY" != 1 ]; then
  echo "the server did not answer on port $PORT within 15s:" >&2
  sed 's/^/  /' "$LOG" >&2
  ./stop.sh --quiet
  exit 1
fi

BRANCH="$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo '(not a git checkout)')"

echo
grep -E '^ *(pages:|total:|proofread\.html:)' "$LOG" | sed 's/^ */  /' || true
echo
echo "  site        http://127.0.0.1:$PORT/"
echo "  proofread   http://127.0.0.1:$PORT/proofread.html"
echo "  editing     $EDIT"
echo "  branch      $BRANCH"
echo "  log         $RUN/server.log"
echo "  pid         $PID"
echo
echo "  stop it     ./stop.sh"
echo

[ "$OPEN" = 1 ] && { open "http://127.0.0.1:$PORT/" 2>/dev/null || true; }
exit 0
