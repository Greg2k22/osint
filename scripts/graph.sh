#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CASES="$ROOT/data/cases"
CASE_ONLY="${1:-}"
TMP="$(mktemp)"
trap 'rm -f "$TMP"' EXIT

[[ -d "$CASES" ]] || {
  echo "BŁĄD: brak katalogu $CASES"
  exit 1
}

CASES="$CASES" CASE_ONLY="$CASE_ONLY" python3 > "$TMP" <<'PY'
import json
import os
from pathlib import Path

cases = Path(os.environ["CASES"])
case_only = os.environ.get("CASE_ONLY", "").strip()

def q(value):
    return json.dumps(str(value), ensure_ascii=False)

def qlist(values):
    return json.dumps([str(v) for v in values], ensure_ascii=False)

def emit(text):
    print(text)

if case_only:
    selected = [Path(case_only)]
else:
    selected = sorted(cases.iterdir())

for case in selected:
    if not case.is_dir():
        continue

    case_id = case.name
    case_path = str(case)

    hosts_file = case / "hosts.json"
    profiles_file = case / "profiles.json"
    services_file = case / "services.json"
    meta_file = case / "meta.json"

    if meta_file.exists():
        try:
            meta = json.loads(meta_file.read_text())
        except Exception:
            meta = {}

        if meta.get("type") == "EMAIL" and meta.get("email"):
            email = meta["email"]

            emit(
                f'MERGE (c:Case {{id:{q(case_id)}}}) '
                f'SET c.type="EMAIL", c.path={q(case_path)};'
            )

            emit(
                f'MERGE (e:Email {{value:{q(email)}}}) '
                f'MERGE (c:Case {{id:{q(case_id)}}}) '
                f'MERGE (e)-[:OBSERVED_IN]->(c);'
            )

    if hosts_file.exists():
        try:
            records = json.loads(hosts_file.read_text())
        except Exception:
            records = []

        domain = None
        for item in records:
            if "target" in item.get("sources", []):
                domain = item.get("host")
                break

        if domain:
            emit(
                f'MERGE (c:Case {{id:{q(case_id)}}}) '
                f'SET c.type="DOMAIN", c.path={q(case_path)};'
            )
            emit(
                f'MERGE (d:Domain {{name:{q(domain)}}}) '
                f'MERGE (c:Case {{id:{q(case_id)}}}) '
                f'MERGE (d)-[:OBSERVED_IN]->(c);'
            )

            for item in records:
                host = item.get("host")
                if not host:
                    continue

                if item.get("confidence") not in {"MEDIUM", "HIGH"}:
                    continue

                sources = item.get("sources", [])
                confidence = item.get("confidence", "UNVERIFIED")
                ips = item.get("resolved_ips", [])

                emit(
                    f'MERGE (h:Host {{name:{q(host)}}}) '
                    f'MERGE (d:Domain {{name:{q(domain)}}}) '
                    f'MERGE (d)-[r:HAS_HOST {{case_id:{q(case_id)}}}]->(h) '
                    f'SET r.sources={qlist(sources)}, '
                    f'r.confidence={q(confidence)};'
                )

                emit(
                    f'MERGE (h:Host {{name:{q(host)}}}) '
                    f'MERGE (c:Case {{id:{q(case_id)}}}) '
                    f'MERGE (h)-[:OBSERVED_IN]->(c);'
                )

                for ip in ips:
                    emit(
                        f'MERGE (h:Host {{name:{q(host)}}}) '
                        f'MERGE (ip:IP {{address:{q(ip)}}}) '
                        f'MERGE (h)-[r:RESOLVES_TO {{case_id:{q(case_id)}}}]->(ip) '
                        f'SET r.sources={qlist(sources)}, '
                        f'r.confidence={q(confidence)};'
                    )

    if profiles_file.exists():
        try:
            records = json.loads(profiles_file.read_text())
        except Exception:
            records = []

        usernames = sorted({
            str(x.get("username"))
            for x in records
            if x.get("username")
        })

        for username in usernames:
            emit(
                f'MERGE (c:Case {{id:{q(case_id)}}}) '
                f'SET c.type="PERSON", c.path={q(case_path)};'
            )
            emit(
                f'MERGE (u:Username {{value:{q(username)}}}) '
                f'MERGE (c:Case {{id:{q(case_id)}}}) '
                f'MERGE (u)-[:OBSERVED_IN]->(c);'
            )

        for item in records:
            username = item.get("username")
            url = item.get("url")
            if not username or not url:
                continue

            if item.get("confidence") not in {"MEDIUM", "HIGH"}:
                continue

            sources = item.get("sources", [])
            confidence = item.get("confidence", "UNVERIFIED")

            emit(
                f'MERGE (u:Username {{value:{q(username)}}}) '
                f'MERGE (p:Profile {{url:{q(url)}}}) '
                f'MERGE (u)-[r:FOUND_ON {{case_id:{q(case_id)}}}]->(p) '
                f'SET r.sources={qlist(sources)}, '
                f'r.confidence={q(confidence)};'
            )

    if services_file.exists():
        try:
            records = json.loads(services_file.read_text())
        except Exception:
            records = []

        emails = sorted({
            str(x.get("email"))
            for x in records
            if x.get("email")
        })

        if not emails:
            name = case.name
            if name.startswith("email-"):
                pass

        for email in emails:
            emit(
                f'MERGE (c:Case {{id:{q(case_id)}}}) '
                f'SET c.type="EMAIL", c.path={q(case_path)};'
            )
            emit(
                f'MERGE (e:Email {{value:{q(email)}}}) '
                f'MERGE (c:Case {{id:{q(case_id)}}}) '
                f'MERGE (e)-[:OBSERVED_IN]->(c);'
            )

        for item in records:
            email = item.get("email")
            service = item.get("service")
            if not email or not service:
                continue

            source = item.get("source", "holehe")
            confidence = item.get("confidence", "UNVERIFIED")

            emit(
                f'MERGE (e:Email {{value:{q(email)}}}) '
                f'MERGE (s:Service {{name:{q(service)}}}) '
                f'MERGE (e)-[r:FOUND_ON {{case_id:{q(case_id)}}}]->(s) '
                f'SET r.source={q(source)}, '
                f'r.confidence={q(confidence)};'
            )

emit('MATCH (c:Case) RETURN count(c) AS cases;')
emit('MATCH (d:Domain) RETURN count(d) AS domains;')
emit('MATCH (h:Host) RETURN count(h) AS hosts;')
emit('MATCH (u:Username) RETURN count(u) AS usernames;')
emit('MATCH (p:Profile) RETURN count(p) AS profiles;')
emit('MATCH (e:Email) RETURN count(e) AS emails;')
emit('MATCH (s:Service) RETURN count(s) AS services;')
PY

echo "=== IMPORT NEO4J ==="

docker compose exec -T neo4j sh -lc '
AUTH="$NEO4J_AUTH"
USER="${AUTH%%/*}"
PASS="${AUTH#*/}"
/var/lib/neo4j/bin/cypher-shell -u "$USER" -p "$PASS" --format plain
' < "$TMP"

echo
echo "GRAPH IMPORT: OK"
