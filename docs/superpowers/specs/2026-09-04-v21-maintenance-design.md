# OSINT Workbench v2.1 Maintenance Design

## Goal
Harden OSINT Workbench v2 with reproducible CI, safe configuration examples, backup/restore tooling and operational documentation without adding collectors or changing passive-by-default behavior.

## Design
- GitHub Actions validates Python tests/compile, Compose configuration and JavaScript syntax without secrets or real OSINT execution.
- `.env.example` contains placeholders only; `.env`, runtime data and backups remain untracked.
- Backup/restore scripts operate through existing Docker Compose services, never call `docker compose down -v`, require explicit restore input and confirmation.
- README documents install, configuration, operation, recovery, data locations and responsible use.

## Constraints
- macOS Apple Silicon remains supported.
- ACTIVE DOMAIN continues to require `OSINT_ACTIVE_TOKEN`.
- PASSIVE remains default.
- No new collectors.
- No destructive automatic restore and no volume deletion.
