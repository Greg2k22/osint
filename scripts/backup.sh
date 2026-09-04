#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

usage() {
  cat <<'HELP'
Usage: ./scripts/backup.sh [--output DIR]

Creates a timestamped backup under backups/ by default.
PostgreSQL is dumped online.
Neo4j Community is stopped temporarily because neo4j-admin database dump
requires the database to be offline.

No Docker volumes or persistent data are deleted.
HELP
}

OUT_ROOT="$ROOT/backups"

while [ $# -gt 0 ]; do
  case "$1" in
    --help|-h)
      usage
      exit 0
      ;;
    --output)
      [ $# -ge 2 ] || {
        echo "Missing value for --output" >&2
        exit 2
      }
      OUT_ROOT="$2"
      shift 2
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
DEST="$OUT_ROOT/$STAMP"
mkdir -p "$DEST"

POSTGRES_USER="${POSTGRES_USER:-osint}"
POSTGRES_DB="${POSTGRES_DB:-osint}"

echo "Backing up PostgreSQL..."
docker compose exec -T postgres \
  pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc \
  > "$DEST/postgres.dump"

echo "Preparing offline Neo4j backup..."

NEO4J_WAS_RUNNING=0
API_WAS_RUNNING=0

if docker compose ps --status running --services | grep -qx neo4j; then
  NEO4J_WAS_RUNNING=1
fi

if docker compose ps --status running --services | grep -qx api; then
  API_WAS_RUNNING=1
fi

restart_services() {
  if [ "$NEO4J_WAS_RUNNING" -eq 1 ]; then
    docker compose start neo4j >/dev/null 2>&1 || true
  fi

  if [ "$API_WAS_RUNNING" -eq 1 ]; then
    docker compose start api >/dev/null 2>&1 || true
  fi
}

trap restart_services EXIT

if [ "$API_WAS_RUNNING" -eq 1 ]; then
  docker compose stop api >/dev/null
fi

if [ "$NEO4J_WAS_RUNNING" -eq 1 ]; then
  docker compose stop neo4j >/dev/null
fi

docker compose run --rm --no-deps neo4j \
  neo4j-admin database dump neo4j \
  --to-path=/data/backups \
  --overwrite-destination=true >/dev/null

docker compose cp \
  neo4j:/data/backups/neo4j.dump \
  "$DEST/neo4j.dump" >/dev/null

restart_services
trap - EXIT

echo "Backup created: $DEST"
