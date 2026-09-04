# OSINT Workbench

Local OSINT workbench for DOMAIN, PERSON and EMAIL investigations with FastAPI, PostgreSQL, Redis, Neo4j and Docker Compose.

## Requirements

- macOS Apple Silicon or a compatible Docker host
- Docker Desktop with Compose v2
- Python 3.12+ for local tests
- Git
- Node.js is optional and used for JavaScript syntax validation

## Installation

```bash
git clone https://github.com/Greg2k22/osint.git
cd osint
cp .env.example .env
```

Edit `.env` before first start. Never commit `.env`.

## Configuration

`.env.example` contains placeholders only. Set database credentials consistently with your Compose configuration.

`OSINT_ACTIVE_TOKEN` is required only for DOMAIN ACTIVE requests. Generate a random token locally, for example:

```bash
python3 -c 'import secrets; print(secrets.token_urlsafe(32))'
```

Do not put the token in source code, screenshots, tickets or Git history.

## Start

```bash
docker compose build api
docker compose up -d
curl http://127.0.0.1:8088/health
```

UI: `http://127.0.0.1:8088/ui`

## Stop without deleting data

```bash
docker compose stop
```

To remove containers while keeping named volumes:

```bash
docker compose down
```

**Do not run `docker compose down -v` unless you deliberately intend to delete persistent database data.**

## Tests

```bash
python -m pip install -e '.[dev]'
python -m pytest -q
python -m compileall -q src
docker compose config -q
node --check src/osint_workbench/web/app.js
```

GitHub Actions runs non-OSINT CI checks for pull requests and pushes to `main`. CI does not use real secrets and does not run ACTIVE scans.

## Investigation types

- **DOMAIN** - domain and host observations; PASSIVE by default, optional ACTIVE mode.
- **PERSON** - username/profile candidate discovery; PASSIVE only.
- **EMAIL** - service signals for an email address; PASSIVE only.

### PASSIVE vs ACTIVE

PASSIVE is the default and should be used unless active network interaction is explicitly authorized.

ACTIVE is supported only for DOMAIN and requires both explicit authorization in the request and a matching server-side `OSINT_ACTIVE_TOKEN`.

## Data locations

- Runtime cases and job data: `data/`
- PostgreSQL: Docker named volume `postgres_data`
- Neo4j: Docker named volume `neo4j_data`
- Local backups: `backups/`
- Local configuration and secrets: `.env`

`data/`, `backups/` and `.env` are excluded from Git.

## Backup

Create a timestamped backup:

```bash
./scripts/backup.sh
```

Custom destination:

```bash
./scripts/backup.sh --output /secure/path/osint-backups
```

The backup includes `postgres.dump` and `neo4j.dump`. Store backups according to the sensitivity of collected OSINT data.

## Restore

Restore requires an explicit backup directory:

```bash
./scripts/restore.sh --from backups/20260904T120000Z
```

The script asks for the literal confirmation `RESTORE`. For controlled automation, `--yes` suppresses the prompt:

```bash
./scripts/restore.sh --from /secure/path/backup --yes
```

Restore overwrites database contents. Take a fresh backup first. The scripts never call `docker compose down -v`.

## Update

```bash
git checkout main
git pull --ff-only origin main
python -m pip install -e '.[dev]'
docker compose build api
docker compose up -d
python -m pytest -q
```

Take a backup before upgrades that may affect database formats or migration behavior.

## Troubleshooting

Check services:

```bash
docker compose ps
docker compose logs --tail=100 api
curl http://127.0.0.1:8088/health
curl http://127.0.0.1:8088/api/system/status
```

If ACTIVE returns HTTP 403, verify that `OSINT_ACTIVE_TOKEN` exists in `.env`, the API container received it, and the client sends the matching `X-OSINT-Active-Token` header.

If a collector fails, inspect the CASE `tool_runs.json` and job logs. Do not interpret a collector failure as proof that the target does not exist.

## Privacy and responsible use

OSINT results can contain personal data, identifiers, relationships and false positives. Use the workbench only for lawful, authorized purposes. Apply data minimization, restrict access to cases and backups, define retention periods, and verify important findings against independent evidence before acting on them.

ACTIVE scanning creates network traffic visible to the target and third parties. Run it only with appropriate authorization.
