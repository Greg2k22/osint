#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

usage() {
  cat <<'HELP'
Usage: ./scripts/backup.sh [--output DIR]

Creates a timestamped backup under backups/ by default.
Includes PostgreSQL custom dump and Neo4j database dump.
Does not stop or delete Docker volumes.
HELP
}

OUT_ROOT="$ROOT/backups"
while [ $# -gt 0 ]; do
  case "$1" in
    --help|-h) usage; exit 0 ;;
    --output) [ $# -ge 2 ] || { echo "Missing value for --output" >&2; exit 2; }; OUT_ROOT="$2"; shift 2 ;;
    *) echo "Unknown argument: $1" >&2; usage >&2; exit 2 ;;
  esac
done

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
DEST="$OUT_ROOT/$STAMP"
mkdir -p "$DEST"

POSTGRES_USER="${POSTGRES_USER:-osint}"
POSTGRES_DB="${POSTGRES_DB:-osint}"

echo "Backing up PostgreSQL..."
docker compose exec -T postgres pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc > "$DEST/postgres.dump"

echo "Backing up Neo4j..."
docker compose exec -T neo4j neo4j-admin database dump neo4j --to-path=/tmp --overwrite-destination=true >/dev/null
docker compose cp neo4j:/tmp/neo4j.dump "$DEST/neo4j.dump" >/dev/null

echo "Backup created: $DEST"
