#!/bin/sh
set -eu
docker compose config >/dev/null
docker compose up -d
for i in 1 2 3 4 5 6 7 8 9 10; do
  if curl -fsS http://127.0.0.1:8088/health >/dev/null 2>&1; then break; fi
  sleep 2
done
curl -fsS http://127.0.0.1:8088/health
docker compose exec -T postgres pg_isready -U osint -d osint
docker compose exec -T redis redis-cli ping
echo 'Smoke OK'
