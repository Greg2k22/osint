from __future__ import annotations

import os
from functools import lru_cache


class Neo4jService:
    def __init__(self, uri: str, user: str, password: str):
        from neo4j import GraphDatabase
        self._driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self) -> None:
        self._driver.close()

    def list_cases(self, limit: int = 100) -> list[dict]:
        with self._driver.session(database='neo4j') as session:
            rows = session.run('''
                MATCH (c:Case)
                OPTIONAL MATCH (x)-[:OBSERVED_IN]->(c)
                RETURN c.id AS id, c.type AS type, c.path AS path,
                       c.target AS target, count(DISTINCT x) AS observed
                ORDER BY c.id DESC LIMIT $limit
            ''', limit=int(limit))
            return [dict(r) for r in rows]

    def get_case(self, case_id: str) -> dict | None:
        with self._driver.session(database='neo4j') as session:
            case_row = session.run('''
                MATCH (c:Case {id: $case_id})
                RETURN c.id AS id, c.type AS type, c.path AS path, c.target AS target
            ''', case_id=case_id).single()
            if not case_row:
                return None
            observed_rows = session.run('''
                MATCH (n)-[:OBSERVED_IN]->(c:Case {id: $case_id})
                RETURN labels(n) AS labels, properties(n) AS node
                ORDER BY labels(n)
            ''', case_id=case_id)
            relation_rows = session.run('''
                MATCH (a)-[r]->(b)
                WHERE r.case_id = $case_id
                RETURN labels(a) AS from_labels, properties(a) AS from_node,
                       type(r) AS relation_type, properties(r) AS relation,
                       labels(b) AS to_labels, properties(b) AS to_node
                ORDER BY relation_type
            ''', case_id=case_id)
            return {
                'case': dict(case_row),
                'observed': [{'labels': r['labels'], 'node': r['node']} for r in observed_rows],
                'relations': [{
                    'from_labels': r['from_labels'], 'from': r['from_node'],
                    'type': r['relation_type'], 'relation': r['relation'],
                    'to_labels': r['to_labels'], 'to': r['to_node'],
                } for r in relation_rows],
            }

    def case_graph_rows(self, case_id: str) -> list[dict]:
        with self._driver.session(database='neo4j') as session:
            rows = session.run('''
                MATCH (a)-[r]->(b)
                WHERE r.case_id = $case_id
                  AND type(r) IN ['HAS_HOST','RESOLVES_TO','FOUND_ON','USES','BELONGS_TO','USES_TECHNOLOGY','CONCERNS']
                RETURN
                  head(labels(a)) AS from_type,
                  coalesce(a.name, a.value, a.url, a.address, a.id) AS from_value,
                  type(r) AS relation,
                  head(labels(b)) AS to_type,
                  coalesce(b.name, b.value, b.url, b.address, b.id) AS to_value,
                  coalesce(r.confidence, 'MEDIUM') AS confidence,
                  coalesce(r.sources, CASE WHEN r.source IS NULL THEN [] ELSE [r.source] END) AS sources
            ''', case_id=case_id)
            return [dict(r) for r in rows]


def _neo4j_config() -> tuple[str, str, str]:
    auth = os.environ.get('NEO4J_AUTH', '')
    uri = os.environ.get('NEO4J_URI', 'bolt://neo4j:7687')
    if '/' not in auth:
        raise RuntimeError('Neo4j credentials are not configured')
    user, password = auth.split('/', 1)
    return uri, user, password


@lru_cache(maxsize=1)
def get_neo4j_service() -> Neo4jService:
    return Neo4jService(*_neo4j_config())
