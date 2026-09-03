import os
from fastapi import APIRouter, HTTPException

router = APIRouter()


def _neo4j_config():
    auth = os.environ.get("NEO4J_AUTH", "")
    uri = os.environ.get("NEO4J_URI", "bolt://neo4j:7687")
    if "/" not in auth:
        raise HTTPException(status_code=503, detail="Neo4j credentials are not configured")
    user, password = auth.split("/", 1)
    return uri, user, password


def _driver():
    from neo4j import GraphDatabase
    uri, user, password = _neo4j_config()
    return GraphDatabase.driver(uri, auth=(user, password))


@router.get("/api/cases")
def api_cases():
    try:
        driver = _driver()
        with driver:
            with driver.session(database="neo4j") as session:
                rows = session.run("""
                    MATCH (c:Case)
                    OPTIONAL MATCH (x)-[:OBSERVED_IN]->(c)
                    RETURN c.id AS id, c.type AS type, c.path AS path,
                           count(DISTINCT x) AS observed
                    ORDER BY c.id DESC LIMIT 100
                """)
                return {"cases": [{"id": r["id"], "type": r["type"], "path": r["path"], "observed": r["observed"]} for r in rows]}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Neo4j unavailable: {type(exc).__name__}") from exc


@router.get("/api/cases/{case_id}")
def api_case_detail(case_id: str):
    try:
        driver = _driver()
        with driver:
            with driver.session(database="neo4j") as session:
                case_row = session.run("""
                    MATCH (c:Case {id: $case_id})
                    RETURN c.id AS id, c.type AS type, c.path AS path
                """, case_id=case_id).single()
                if not case_row:
                    raise HTTPException(status_code=404, detail="Case not found")
                observed_rows = session.run("""
                    MATCH (n)-[:OBSERVED_IN]->(c:Case {id: $case_id})
                    RETURN labels(n) AS labels, properties(n) AS node
                    ORDER BY labels(n)
                """, case_id=case_id)
                observed = [{"labels": r["labels"], "node": r["node"]} for r in observed_rows]
                relation_rows = session.run("""
                    MATCH (a)-[r]->(b)
                    WHERE r.case_id = $case_id
                    RETURN labels(a) AS from_labels, properties(a) AS from_node,
                           type(r) AS relation_type, properties(r) AS relation,
                           labels(b) AS to_labels, properties(b) AS to_node
                    ORDER BY relation_type
                """, case_id=case_id)
                relations = [{
                    "from_labels": r["from_labels"], "from": r["from_node"],
                    "type": r["relation_type"], "relation": r["relation"],
                    "to_labels": r["to_labels"], "to": r["to_node"],
                } for r in relation_rows]
                return {
                    "case": {"id": case_row["id"], "type": case_row["type"], "path": case_row["path"]},
                    "observed": observed,
                    "relations": relations,
                }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Neo4j unavailable: {type(exc).__name__}") from exc
