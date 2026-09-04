#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TMP="$(mktemp)"
trap 'rm -f "$TMP"' EXIT

if [ "$#" -gt 0 ] && [ -n "${1:-}" ]; then
  PYTHONPATH="$ROOT/src" python3 "$ROOT/scripts/graph-v2.py" "$1" > "$TMP"
else
  PYTHONPATH="$ROOT/src" python3 "$ROOT/scripts/graph-v2.py" > "$TMP"
fi

echo "=== IMPORT NEO4J ==="
docker compose exec -T neo4j sh -lc '
AUTH="$NEO4J_AUTH"
USER="${AUTH%%/*}"
PASS="${AUTH#*/}"
/var/lib/neo4j/bin/cypher-shell -u "$USER" -p "$PASS" --format plain
' < "$TMP"

echo
echo "GRAPH IMPORT: OK"
