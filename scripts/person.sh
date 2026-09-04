#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
COMPOSE=(-f "$ROOT/compose.yaml" -f "$ROOT/compose.osint.yaml")

[[ $# -eq 1 ]] || {
  echo "Użycie: ./osint person USERNAME"
  exit 1
}

USERNAME="$1"

if [[ ! "$USERNAME" =~ ^[A-Za-z0-9._-]{1,64}$ ]]; then
  echo "BŁĄD: nieprawidłowa nazwa użytkownika"
  exit 2
fi

STAMP="$(date +%Y%m%d-%H%M%S)"
SAFE="$(echo "$USERNAME" | tr -cd 'A-Za-z0-9._-')"
CASE="$ROOT/data/cases/person-${SAFE}-${STAMP}"

mkdir -p "$CASE"

USERNAME="$USERNAME" CASE="$CASE" python3 <<'META'
import json
import os
from pathlib import Path

case = Path(os.environ["CASE"])
(case / "meta.json").write_text(
    json.dumps({
        "type": "PERSON",
        "username": os.environ["USERNAME"],
        "case_id": case.name
    }, indent=2, ensure_ascii=False)
)
META

echo
echo "======================================"
echo " OSINT PERSON"
echo " Username: $USERNAME"
echo " Mode:     PASSIVE"
echo " Case:     $CASE"
echo "======================================"
echo

echo "[1/2] Maigret..."
docker compose "${COMPOSE[@]}" \
  run --rm maigret "$USERNAME" \
  > "$CASE/maigret.txt" 2>&1 || true

echo "[2/2] Sherlock..."
docker compose "${COMPOSE[@]}" \
  run --rm sherlock "$USERNAME" --print-found --no-color \
  > "$CASE/sherlock.txt" 2>&1 || true

USERNAME="$USERNAME" CASE="$CASE" python3 <<'PY'
import json
import os
import re
from collections import defaultdict
from pathlib import Path

username = os.environ["USERNAME"]
case = Path(os.environ["CASE"])

sources = defaultdict(set)

url_re = re.compile(r'https?://[^\s<>"\']+')

for source, filename in (
    ("maigret", "maigret.txt"),
    ("sherlock", "sherlock.txt"),
):
    p = case / filename
    if not p.exists():
        continue

    for line in p.read_text(errors="ignore").splitlines():
        for url in url_re.findall(line):
            url = url.rstrip(".,);]}")
            sources[url].add(source)

results = []

for url in sorted(sources):
    src = sorted(sources[url])

    confidence = "HIGH" if len(src) >= 2 else "LOW"

    results.append({
        "username": username,
        "url": url,
        "sources": src,
        "confidence": confidence,
    })

(case / "profiles.json").write_text(
    json.dumps(results, indent=2, ensure_ascii=False)
)

(case / "profiles.txt").write_text(
    "\n".join(x["url"] for x in results) + ("\n" if results else "")
)

print()
print("=== PROFILE ===")

if not results:
    print("Brak profili znalezionych przez aktualne źródła.")
else:
    for x in results:
        print(
            f'{x["confidence"]:4}  '
            f'{x["url"]}  '
            f'[{", ".join(x["sources"])}]'
        )

print()
print(f"Profili po deduplikacji: {len(results)}")
PY

echo
echo "======================================"
echo " GOTOWE"
echo "======================================"
echo "TXT:  $CASE/profiles.txt"
echo "JSON: $CASE/profiles.json"
echo "CASE: $CASE"

echo
echo "[NORMALIZE] CASE v2..."
PYTHONPATH="$ROOT/src${PYTHONPATH:+:$PYTHONPATH}" python3 "$ROOT/scripts/case-v2.py" "$CASE"

echo "[AUTO-IMPORT] Neo4j..."
"$ROOT/scripts/graph.sh" "$CASE"
