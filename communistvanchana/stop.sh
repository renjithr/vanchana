#!/usr/bin/env bash
# Stop the preview server started by ./start.sh.
#
#   ./stop.sh           stop it and say so
#   ./stop.sh --quiet    say nothing (used by start.sh)
#
# Only ever kills our own preview server: every candidate process is checked
# against its command line first, so an unrelated program that happens to hold
# the port is reported, not killed.
set -euo pipefail
cd "$(dirname "$0")"

PORT="${CMS_PORT:-8765}"
PIDFILE=".preview/server.pid"

QUIET=0
[ "${1:-}" = "--quiet" ] && QUIET=1
say() { [ "$QUIET" = 1 ] || echo "$@"; }

is_ours() {
  ps -p "$1" -o command= 2>/dev/null | grep -q 'cms_server\.py'
}

TARGETS=""

if [ -f "$PIDFILE" ]; then
  P="$(cat "$PIDFILE" 2>/dev/null || true)"
  if [ -n "$P" ] && is_ours "$P"; then
    TARGETS="$P"
  fi
  rm -f "$PIDFILE"
fi

# Also sweep the port, in case the server was started some other way
# (./preview.sh, or a start.sh whose pid file was removed).
FOREIGN=""
for P in $(lsof -ti "tcp:$PORT" 2>/dev/null || true); do
  if is_ours "$P"; then
    case " $TARGETS " in *" $P "*) ;; *) TARGETS="$TARGETS $P" ;; esac
  else
    FOREIGN="$FOREIGN $P"
  fi
done

if [ -z "${TARGETS// /}" ]; then
  if [ -n "${FOREIGN// /}" ]; then
    say "nothing of ours to stop, but port $PORT is held by pid(s):$FOREIGN"
    for P in $FOREIGN; do
      ps -p "$P" -o pid=,command= 2>/dev/null | sed 's/^ */  /' || true
    done
    say "left alone — it is not the preview server"
  else
    say "nothing to stop — no preview server on port $PORT"
  fi
  exit 0
fi

kill $TARGETS 2>/dev/null || true

for _ in $(seq 1 40); do
  STILL=""
  for P in $TARGETS; do
    if kill -0 "$P" 2>/dev/null; then STILL="$STILL $P"; fi
  done
  [ -z "${STILL// /}" ] && break
  sleep 0.25
done

# anything that ignored TERM
for P in $TARGETS; do
  if kill -0 "$P" 2>/dev/null; then kill -9 "$P" 2>/dev/null || true; fi
done

if lsof -ti "tcp:$PORT" >/dev/null 2>&1; then
  say "stopped, but something is still listening on port $PORT"
else
  say "stopped — port $PORT is free"
fi
exit 0
