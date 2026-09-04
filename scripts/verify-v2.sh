#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BASE="${OSINT_BASE_URL:-http://127.0.0.1:8088}"

say() { printf '\n=== %s ===\n' "$1"; }

say HEALTH
curl -fsS "$BASE/health"

say SYSTEM
curl -fsS "$BASE/api/system/status" | python3 -m json.tool

say UI
for path in /ui /ui/static/app.css /ui/static/app.js /ui/static/vendor/cytoscape.min.js; do
  code="$(curl -s -o /dev/null -w '%{http_code}' "$BASE$path")"
  printf '%-48s %s\n' "$path" "$code"
  [ "$code" = "200" ] || exit 1
done

say ROUTES
curl -fsS "$BASE/openapi.json" | python3 -c 'import json,sys; p=json.load(sys.stdin)["paths"]; [print(x) for x in sorted(p) if x.startswith("/api/")]'

case_dir="$(find "$ROOT/data/cases" -mindepth 1 -maxdepth 1 -type d 2>/dev/null | sort | tail -1 || true)"
if [ -n "$case_dir" ]; then
  case_id="$(basename "$case_dir")"
  say "CASE $case_id"
  for suffix in report report.md export.json export.csv graph analysis; do
    code="$(curl -s -o /dev/null -w '%{http_code}' "$BASE/api/cases/$case_id/$suffix")"
    printf '%-48s %s\n' "$suffix" "$code"
  done
fi

if [ "${1:-}" = "--live" ]; then
  say LIVE_QUEUE
  payload="$(curl -fsS -X POST "$BASE/api/scan" -H 'Content-Type: application/json' -d '{"type":"EMAIL","target":"wave5-e2e@example.com","active":false,"authorized":false}')"
  printf '%s\n' "$payload" | python3 -m json.tool
  job_id="$(printf '%s' "$payload" | python3 -c 'import json,sys; print(json.load(sys.stdin)["id"])')"
  for _ in $(seq 1 24); do
    state="$(curl -fsS "$BASE/api/jobs" | JOB_ID="$job_id" python3 -c 'import json,os,sys; jobs=json.load(sys.stdin).get("jobs",[]); print(next((x.get("status",x.get("queue","")) for x in jobs if x.get("id")==os.environ["JOB_ID"]),"MISSING"))')"
    printf 'job=%s status=%s\n' "$job_id" "$state"
    case "$state" in DONE|DONE_WITH_WARNINGS) exit 0;; FAILED) exit 1;; esac
    sleep 5
  done
  echo "Timeout waiting for live job" >&2
  exit 1
fi

say RESULT
echo "VERIFY V2: OK"
