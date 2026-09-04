from __future__ import annotations

import json
import os
import time
from pathlib import Path

from sqlalchemy import create_engine, text

from osint_workbench.settings import Settings

COLLECTORS = ('bbot', 'subfinder', 'theharvester', 'httpx', 'maigret', 'sherlock', 'holehe')


def runner_status(path: str | Path, *, now: float | None = None, max_age: int = 120) -> dict:
    heartbeat = Path(path)
    if not heartbeat.exists():
        return {'status': 'ERROR', 'age_seconds': None}
    current = time.time() if now is None else now
    age = max(0, int(current - heartbeat.stat().st_mtime))
    return {'status': 'OK' if age <= max_age else 'ERROR', 'age_seconds': age}


def read_collectors_snapshot(path: str | Path) -> dict:
    snapshot = Path(path)
    try:
        raw = json.loads(snapshot.read_text())
    except Exception:
        raw = {}
    result = {}
    for name in COLLECTORS:
        item = raw.get(name)
        if isinstance(item, dict):
            result[name] = {
                'status': str(item.get('status', 'NOT_CONFIGURED')),
                'version': item.get('version'),
                'image': item.get('image'),
            }
        else:
            result[name] = {'status': 'NOT_CONFIGURED', 'version': None, 'image': None}
    return result


def _postgres_status(settings: Settings) -> str:
    engine = create_engine(settings.database_url, pool_pre_ping=True)
    try:
        with engine.connect() as connection:
            connection.execute(text('SELECT 1'))
        return 'OK'
    finally:
        engine.dispose()


def _redis_status(settings: Settings) -> str:
    from redis import Redis
    client = Redis.from_url(settings.redis_url, socket_connect_timeout=2, socket_timeout=2)
    try:
        return 'OK' if client.ping() else 'ERROR'
    finally:
        client.close()


def _neo4j_status() -> str:
    from neo4j import GraphDatabase
    auth = os.environ.get('NEO4J_AUTH', '')
    if '/' not in auth:
        return 'NOT_CONFIGURED'
    user, password = auth.split('/', 1)
    uri = os.environ.get('NEO4J_URI', 'bolt://neo4j:7687')
    driver = GraphDatabase.driver(uri, auth=(user, password), connection_timeout=2)
    try:
        driver.verify_connectivity()
        return 'OK'
    finally:
        driver.close()


def _safe_probe(fn) -> str:
    try:
        return fn()
    except Exception:
        return 'ERROR'


def build_system_status(settings: Settings | None = None) -> dict:
    cfg = settings or Settings()
    jobs_root = Path(os.environ.get('OSINT_JOBS_ROOT', '/data/jobs'))
    system_root = Path(os.environ.get('OSINT_SYSTEM_ROOT', '/data/system'))
    return {
        'api': 'OK',
        'postgres': _safe_probe(lambda: _postgres_status(cfg)),
        'redis': _safe_probe(lambda: _redis_status(cfg)),
        'neo4j': _safe_probe(_neo4j_status),
        'runner': runner_status(jobs_root / 'runner.heartbeat'),
        'tools': read_collectors_snapshot(system_root / 'collectors.json'),
    }
