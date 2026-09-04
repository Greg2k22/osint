from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_ci_workflow_is_safe_and_complete():
    ci = text(".github/workflows/ci.yml")
    assert "pull_request:" in ci
    assert "push:" in ci and "main" in ci
    assert "python -m pytest -q" in ci
    assert "python -m compileall -q src" in ci
    assert "docker compose config -q" in ci
    assert "node --check src/osint_workbench/web/app.js" in ci
    assert "OSINT_ACTIVE_TOKEN" not in ci
    assert "./osint" not in ci


def test_env_example_has_placeholders_not_real_secrets():
    env = text(".env.example")
    assert "OSINT_ACTIVE_TOKEN=" in env
    assert "NEO4J_AUTH=" in env
    assert "DATABASE_URL=" in env
    assert "REDIS_URL=" in env
    assert "change-me-now" not in env
    assert "server-secret" not in env


def test_runtime_and_backups_are_ignored():
    ignore = text(".gitignore")
    assert ".env" in ignore
    assert "data/" in ignore
    assert "backups/" in ignore


def test_backup_restore_scripts_have_safety_contract():
    backup = text("scripts/backup.sh")
    restore = text("scripts/restore.sh")
    assert "--help" in backup
    assert "--help" in restore
    assert "backups" in backup
    assert "--yes" in restore
    assert "docker compose down -v" not in backup
    assert "docker compose down -v" not in restore
    assert "pg_dump" in backup
    assert "pg_restore" in restore or "psql" in restore
    assert "neo4j-admin" in backup
    assert "neo4j-admin" in restore


def test_readme_covers_operations_and_responsible_use():
    readme = text("README.md").lower()
    for term in [
        "requirements", "installation", "configuration", "domain", "person", "email",
        "passive", "active", "osint_active_token", "backup", "restore", "troubleshooting",
        "privacy", "responsible", "data/", "docker compose down -v",
    ]:
        assert term in readme


def test_neo4j_backup_is_offline_and_restore_stops_api_first():
    backup = text("scripts/backup.sh")
    restore = text("scripts/restore.sh")

    # Pomijamy tekst funkcji --help i sprawdzamy kolejność realnych poleceń.
    backup_exec = backup.split('OUT_ROOT="$ROOT/backups"', 1)[1]
    restore_exec = restore.split('SOURCE=""', 1)[1]

    assert "docker compose stop neo4j" in backup_exec
    assert "neo4j-admin database dump" in backup_exec
    assert backup_exec.index("docker compose stop neo4j") < backup_exec.index(
        "neo4j-admin database dump"
    )

    assert "docker compose stop api neo4j" in restore_exec
    assert "dropdb" in restore_exec
    assert restore_exec.index("docker compose stop api neo4j") < restore_exec.index(
        "dropdb"
    )

    assert "--force" in restore_exec
