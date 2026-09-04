#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

usage() {
  cat <<'HELP'
Usage: ./scripts/restore.sh --from BACKUP_DIR [--yes]

Restores PostgreSQL and Neo4j from an explicitly selected backup directory.

Restore overwrites database contents.
Without --yes, interactive confirmation is required.

API and Neo4j are stopped before destructive restore operations.
No Docker volumes are automatically deleted.
HELP
}

SOURCE=""
YES=0

while [ $# -gt 0 ]; do
  case "$1" in
    --help|-h)
      usage
      exit 0
      ;;
    --from)
      [ $# -ge 2 ] || {
        echo "Missing value for --from" >&2
        exit 2
      }
      SOURCE="$2"
      shift 2
      ;;
    --yes)
      YES=1
      shift
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

[ -n "$SOURCE" ] || {
  echo "--from is required" >&2
  exit 2
}

SOURCE="$(cd "$SOURCE" 2>/dev/null && pwd)" || {
  echo "Backup directory not found" >&2
  exit 2
}

[ -f "$SOURCE/postgres.dump" ] || {
  echo "Missing postgres.dump" >&2
  exit 2
}

[ -f "$SOURCE/neo4j.dump" ] || {
  echo "Missing neo4j.dump" >&2
  exit 2
}

if [ "$YES" -ne 1 ]; then
  printf \
    'Restore will overwrite PostgreSQL and Neo4j data from %s. Type RESTORE to continue: ' \
    "$SOURCE"

  read -r answer

  [ "$answer" = "RESTORE" ] || {
    echo "Restore cancelled"
    exit 1
  }
fi

POSTGRES_USER="${POSTGRES_USER:-osint}"
POSTGRES_DB="${POSTGRES_DB:-osint}"

echo "Stopping API and Neo4j..."
docker compose stop api neo4j >/dev/null

echo "Restoring PostgreSQL..."

docker compose cp \
  "$SOURCE/postgres.dump" \
  postgres:/tmp/osint-postgres.dump >/dev/null

docker compose exec -T postgres \
  dropdb \
  --force \
  -U "$POSTGRES_USER" \
  --if-exists "$POSTGRES_DB"

docker compose exec -T postgres \
  createdb \
  -U "$POSTGRES_USER" \
  "$POSTGRES_DB"

docker compose exec -T postgres \
  pg_restore \
  -U "$POSTGRES_USER" \
  -d "$POSTGRES_DB" \
  /tmp/osint-postgres.dump

echo "Restoring Neo4j..."

docker compose run --rm --no-deps \
  -v "$SOURCE:/restore:ro" \
  neo4j \
  neo4j-admin database load neo4j \
  --from-path=/restore \
  --overwrite-destination=true >/dev/null

echo "Starting Neo4j and API..."
docker compose start neo4j api >/dev/null

echo "Restore completed from: $SOURCE"
