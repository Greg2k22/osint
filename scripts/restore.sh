#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

usage() {
  cat <<'HELP'
Usage: ./scripts/restore.sh --from BACKUP_DIR [--yes]

Restores PostgreSQL and Neo4j from an explicitly selected backup directory.
This overwrites database contents. Without --yes, interactive confirmation is required.
Never removes Docker volumes or persistent data automatically.
HELP
}

SOURCE=""
YES=0
while [ $# -gt 0 ]; do
  case "$1" in
    --help|-h) usage; exit 0 ;;
    --from) [ $# -ge 2 ] || { echo "Missing value for --from" >&2; exit 2; }; SOURCE="$2"; shift 2 ;;
    --yes) YES=1; shift ;;
    *) echo "Unknown argument: $1" >&2; usage >&2; exit 2 ;;
  esac
done

[ -n "$SOURCE" ] || { echo "--from is required" >&2; exit 2; }
SOURCE="$(cd "$SOURCE" 2>/dev/null && pwd)" || { echo "Backup directory not found" >&2; exit 2; }
[ -f "$SOURCE/postgres.dump" ] || { echo "Missing postgres.dump" >&2; exit 2; }
[ -f "$SOURCE/neo4j.dump" ] || { echo "Missing neo4j.dump" >&2; exit 2; }

if [ "$YES" -ne 1 ]; then
  printf 'Restore will overwrite PostgreSQL and Neo4j data from %s. Type RESTORE to continue: ' "$SOURCE"
  read -r answer
  [ "$answer" = "RESTORE" ] || { echo "Restore cancelled"; exit 1; }
fi

POSTGRES_USER="${POSTGRES_USER:-osint}"
POSTGRES_DB="${POSTGRES_DB:-osint}"

echo "Restoring PostgreSQL..."
docker compose cp "$SOURCE/postgres.dump" postgres:/tmp/osint-postgres.dump >/dev/null
docker compose exec -T postgres sh -lc "dropdb -U '$POSTGRES_USER' --if-exists '$POSTGRES_DB' && createdb -U '$POSTGRES_USER' '$POSTGRES_DB' && pg_restore -U '$POSTGRES_USER' -d '$POSTGRES_DB' --clean --if-exists /tmp/osint-postgres.dump"

echo "Restoring Neo4j..."
docker compose exec -T neo4j mkdir -p /data/backups
docker compose cp "$SOURCE/neo4j.dump" neo4j:/data/backups/neo4j.dump >/dev/null
docker compose stop api neo4j >/dev/null
docker compose run --rm --no-deps neo4j neo4j-admin database load neo4j --from-path=/data/backups --overwrite-destination=true >/dev/null || {
  echo "Neo4j restore failed. Database remains stopped for safety." >&2
  exit 1
}
docker compose start neo4j api >/dev/null

echo "Restore completed from: $SOURCE"
