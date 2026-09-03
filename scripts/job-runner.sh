#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PENDING="$ROOT/data/jobs/pending"
RUNNING="$ROOT/data/jobs/running"
DONE="$ROOT/data/jobs/done"
FAILED="$ROOT/data/jobs/failed"

mkdir -p "$PENDING" "$RUNNING" "$DONE" "$FAILED"

JOB="$(find "$PENDING" -maxdepth 1 -type f -name '*.json' | sort | head -1 || true)"

if [ -z "$JOB" ]; then
  echo "Brak zadań PENDING"
  exit 0
fi

BASENAME="$(basename "$JOB")"
RUNFILE="$RUNNING/$BASENAME"
LOGFILE="$RUNNING/${BASENAME%.json}.log"

mv "$JOB" "$RUNFILE"

ID="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1])).get("id",""))' "$RUNFILE")"
TYPE="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1])).get("type",""))' "$RUNFILE")"
TARGET="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1])).get("target",""))' "$RUNFILE")"
ACTIVE="$(python3 -c 'import json,sys; print("1" if json.load(open(sys.argv[1])).get("active") else "0")' "$RUNFILE")"
AUTHORIZED="$(python3 -c 'import json,sys; print("1" if json.load(open(sys.argv[1])).get("authorized") else "0")' "$RUNFILE")"

fail_job() {
  REASON="$1"

  python3 -c '
import json,sys
p=sys.argv[1]
reason=sys.argv[2]
j=json.load(open(p))
j["status"]="FAILED"
j["error"]=reason
json.dump(j,open(p,"w"),indent=2,ensure_ascii=False)
' "$RUNFILE" "$REASON"

  mv "$RUNFILE" "$FAILED/$BASENAME"

  if [ -f "$LOGFILE" ]; then
    mv "$LOGFILE" "$FAILED/${BASENAME%.json}.log"
  fi

  echo "FAILED: $REASON"
  exit 1
}

[ -n "$ID" ] || fail_job "Missing job id"
[ -n "$TARGET" ] || fail_job "Missing target"

case "$TYPE" in
  DOMAIN)
    if ! printf '%s' "$TARGET" | grep -Eq '^([A-Za-z0-9-]+\.)+[A-Za-z]{2,63}$'; then
      fail_job "Invalid DOMAIN target"
    fi

    if [ "$ACTIVE" = "1" ]; then
      [ "$AUTHORIZED" = "1" ] || fail_job "ACTIVE requires authorization"
      CMD=("$ROOT/osint" domain "$TARGET" --active --authorized)
    else
      CMD=("$ROOT/osint" domain "$TARGET")
    fi
    ;;

  PERSON)
    if ! printf '%s' "$TARGET" | grep -Eq '^[A-Za-z0-9._-]{1,64}$'; then
      fail_job "Invalid PERSON target"
    fi

    [ "$ACTIVE" = "0" ] || fail_job "ACTIVE unsupported for PERSON"
    CMD=("$ROOT/osint" person "$TARGET")
    ;;

  EMAIL)
    if ! printf '%s' "$TARGET" | grep -Eq '^[^[:space:]@]+@[^[:space:]@]+\.[^[:space:]@]+$'; then
      fail_job "Invalid EMAIL target"
    fi

    [ "$ACTIVE" = "0" ] || fail_job "ACTIVE unsupported for EMAIL"
    CMD=("$ROOT/osint" email "$TARGET")
    ;;

  *)
    fail_job "Unsupported job type: $TYPE"
    ;;
esac

python3 -c '
import json,sys
p=sys.argv[1]
j=json.load(open(p))
j["status"]="RUNNING"
json.dump(j,open(p,"w"),indent=2,ensure_ascii=False)
' "$RUNFILE"

echo "RUNNING: $ID $TYPE $TARGET"

if "${CMD[@]}" > "$LOGFILE" 2>&1; then
  python3 -c '
import json,sys
p=sys.argv[1]
j=json.load(open(p))
j["status"]="DONE"
json.dump(j,open(p,"w"),indent=2,ensure_ascii=False)
' "$RUNFILE"

  mv "$RUNFILE" "$DONE/$BASENAME"
  mv "$LOGFILE" "$DONE/${BASENAME%.json}.log"

  echo "DONE: $ID"
  exit 0
fi

CODE=$?

python3 -c '
import json,sys
p=sys.argv[1]
j=json.load(open(p))
j["status"]="FAILED"
j["exit_code"]=int(sys.argv[2])
json.dump(j,open(p,"w"),indent=2,ensure_ascii=False)
' "$RUNFILE" "$CODE"

mv "$RUNFILE" "$FAILED/$BASENAME"
mv "$LOGFILE" "$FAILED/${BASENAME%.json}.log"

echo "FAILED: $ID exit=$CODE"
exit "$CODE"
