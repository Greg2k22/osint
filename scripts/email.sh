#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
COMPOSE=(-f "$ROOT/compose.yaml" -f "$ROOT/compose.osint.yaml")

[[ $# -eq 1 ]] || {
  echo "Użycie: ./osint email ADRES_EMAIL"
  exit 1
}

EMAIL="$1"

if [[ ! "$EMAIL" =~ ^[^[:space:]@]+@[^[:space:]@]+\.[^[:space:]@]+$ ]]; then
  echo "BŁĄD: nieprawidłowy adres e-mail"
  exit 2
fi

STAMP="$(date +%Y%m%d-%H%M%S)"
SAFE="$(echo "$EMAIL" | tr '@.' '__' | tr -cd 'A-Za-z0-9_-')"
CASE="$ROOT/data/cases/email-${SAFE}-${STAMP}"

mkdir -p "$CASE"
TOOL_STATUS="$CASE/.tool-status.tsv"
: > "$TOOL_STATUS"
record_tool() { printf '%s\t%s\n' "$1" "$2" >> "$TOOL_STATUS"; }

EMAIL="$EMAIL" CASE="$CASE" python3 <<'META'
import json
import os
from pathlib import Path

case = Path(os.environ["CASE"])

(case / "meta.json").write_text(
    json.dumps({
        "type": "EMAIL",
        "email": os.environ["EMAIL"],
        "case_id": case.name
    }, indent=2, ensure_ascii=False)
)
META

echo
echo "======================================"
echo " OSINT EMAIL"
echo " Email: $EMAIL"
echo " Mode:  PASSIVE"
echo " Case:  $CASE"
echo "======================================"
echo

echo "[1/1] Holehe..."

set +e
docker compose "${COMPOSE[@]}" \
  run --rm holehe "$EMAIL" --only-used \
  > "$CASE/holehe.txt" 2>&1
CODE=$?
set -e
record_tool "holehe" "$CODE"

EMAIL="$EMAIL" CASE="$CASE" python3 <<'PY'
import json
import os
import re
from pathlib import Path

email = os.environ["EMAIL"]
case = Path(os.environ["CASE"])
p = case / "holehe.txt"

results = []

if p.exists():
    for raw in p.read_text(errors="ignore").splitlines():
        line = raw.strip()

        if not line:
            continue

        if "[+]" not in line:
            continue

        clean = re.sub(r"\x1b\[[0-9;]*m", "", line)
        clean = clean.replace("[+]", "").strip()

        if not clean:
            continue

        service = clean.split()[0].strip(":")
        if service:
            results.append({
                "email": email,
                "service": service,
                "status": "FOUND",
                "source": "holehe",
                "confidence": "MEDIUM"
            })

unique = {}
for item in results:
    unique[item["service"].lower()] = item

results = sorted(unique.values(), key=lambda x: x["service"].lower())

(case / "services.json").write_text(
    json.dumps(results, indent=2, ensure_ascii=False)
)

(case / "services.txt").write_text(
    "\n".join(x["service"] for x in results) +
    ("\n" if results else "")
)

print()
print("=== USŁUGI ===")

if not results:
    print("Brak potwierdzonych usług w wyniku Holehe.")
else:
    for item in results:
        print(
            f'{item["confidence"]:6} '
            f'{item["service"]}'
        )

print()
print(f"Usług po deduplikacji: {len(results)}")
PY

echo
echo "======================================"
echo " GOTOWE"
echo "======================================"
echo "RAW:  $CASE/holehe.txt"
echo "TXT:  $CASE/services.txt"
echo "JSON: $CASE/services.json"
echo "CASE: $CASE"

echo
echo "[NORMALIZE] CASE v2..."
PYTHONPATH="$ROOT/src${PYTHONPATH:+:$PYTHONPATH}" python3 "$ROOT/scripts/case-v2.py" "$CASE"

echo "[FINALIZE] status narzędzi..."
PYTHONPATH="$ROOT/src${PYTHONPATH:+:$PYTHONPATH}" python3 "$ROOT/scripts/finalize-tools.py" "$CASE"

echo "[AUTO-IMPORT] Neo4j..."
"$ROOT/scripts/graph.sh" "$CASE"
