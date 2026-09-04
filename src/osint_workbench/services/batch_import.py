from __future__ import annotations

import json


def _q(value) -> str:
    return json.dumps(str(value), ensure_ascii=False)


def _list(values) -> str:
    return '[' + ','.join(_q(v) for v in values) + ']'


def _maps(rows: list[dict], fields: list[str]) -> str:
    chunks = []
    for row in rows:
        parts = []
        for field in fields:
            value = row.get(field)
            if isinstance(value, list):
                rendered = _list(value)
            else:
                rendered = _q(value if value is not None else '')
            parts.append(f'{field}:{rendered}')
        chunks.append('{' + ','.join(parts) + '}')
    return '[' + ','.join(chunks) + ']'


def build_case_statements(case: dict, records: list[dict]) -> list[str]:
    case_id = case['case_id']
    case_type = case.get('type', '')
    target = case.get('target', '')
    path = case.get('path', '')
    statements = [
        f'MERGE (c:Case {{id:{_q(case_id)}}}) SET c.type={_q(case_type)}, c.target={_q(target)}, c.path={_q(path)};'
    ]

    if case_type == 'DOMAIN':
        statements.append(
            f'MERGE (d:Domain {{name:{_q(target)}}}) MERGE (c:Case {{id:{_q(case_id)}}}) MERGE (d)-[:OBSERVED_IN]->(c);'
        )
        hosts = []
        ips = []
        for r in records:
            if r.get('type') != 'HOST' or r.get('confidence') not in {'HIGH','MEDIUM'}:
                continue
            hosts.append({'host': r.get('value',''), 'confidence': r.get('confidence',''), 'sources': r.get('sources',[])})
            for ip in r.get('resolved_ips', []) or []:
                ips.append({'host': r.get('value',''), 'ip': ip, 'confidence': r.get('confidence',''), 'sources': r.get('sources',[])})
        if hosts:
            statements.append(
                f'UNWIND {_maps(hosts,["host","confidence","sources"])} AS row '
                f'MERGE (d:Domain {{name:{_q(target)}}}) MERGE (h:Host {{name:row.host}}) '
                f'MERGE (d)-[r:HAS_HOST {{case_id:{_q(case_id)}}}]->(h) SET r.confidence=row.confidence, r.sources=row.sources '
                f'WITH h MERGE (c:Case {{id:{_q(case_id)}}}) MERGE (h)-[:OBSERVED_IN]->(c);'
            )
        if ips:
            statements.append(
                f'UNWIND {_maps(ips,["host","ip","confidence","sources"])} AS row '
                f'MERGE (h:Host {{name:row.host}}) MERGE (i:IP {{address:row.ip}}) '
                f'MERGE (h)-[r:RESOLVES_TO {{case_id:{_q(case_id)}}}]->(i) SET r.confidence=row.confidence, r.sources=row.sources;'
            )

    elif case_type == 'PERSON':
        username = target
        statements.append(
            f'MERGE (u:Username {{value:{_q(username)}}}) MERGE (c:Case {{id:{_q(case_id)}}}) MERGE (u)-[:OBSERVED_IN]->(c);'
        )
        profiles = [
            {'url': r.get('value',''), 'confidence': r.get('confidence',''), 'sources': r.get('sources',[])}
            for r in records if r.get('type') == 'PROFILE_CANDIDATE' and r.get('confidence') in {'HIGH','MEDIUM'}
        ]
        if profiles:
            statements.append(
                f'UNWIND {_maps(profiles,["url","confidence","sources"])} AS row '
                f'MERGE (u:Username {{value:{_q(username)}}}) MERGE (p:Profile {{url:row.url}}) '
                f'MERGE (u)-[r:FOUND_ON {{case_id:{_q(case_id)}}}]->(p) SET r.confidence=row.confidence, r.sources=row.sources;'
            )

    elif case_type == 'EMAIL':
        email = target
        statements.append(
            f'MERGE (e:Email {{value:{_q(email)}}}) MERGE (c:Case {{id:{_q(case_id)}}}) MERGE (e)-[:OBSERVED_IN]->(c);'
        )
        services = [
            {'service': r.get('value',''), 'confidence': r.get('confidence',''), 'sources': r.get('sources',[])}
            for r in records if r.get('type') == 'SERVICE_SIGNAL' and r.get('confidence') in {'HIGH','MEDIUM'}
        ]
        if services:
            statements.append(
                f'UNWIND {_maps(services,["service","confidence","sources"])} AS row '
                f'MERGE (e:Email {{value:{_q(email)}}}) MERGE (s:Service {{name:row.service}}) '
                f'MERGE (e)-[r:FOUND_ON {{case_id:{_q(case_id)}}}]->(s) SET r.confidence=row.confidence, r.sources=row.sources;'
            )
    return statements
