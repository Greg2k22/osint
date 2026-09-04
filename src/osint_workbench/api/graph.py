from fastapi import APIRouter, HTTPException, Query

from osint_workbench.services.graph_service import graph_response
from osint_workbench.services.neo4j_service import get_neo4j_service

router = APIRouter()


@router.get('/api/cases/{case_id}/graph')
def api_case_graph(
    case_id: str,
    confidence: str = Query('HIGH,MEDIUM'),
    limit: int = Query(500, ge=1, le=500),
):
    allowed = {x.strip().upper() for x in confidence.split(',') if x.strip()}
    allowed &= {'HIGH', 'MEDIUM', 'LOW'}
    if not allowed:
        raise HTTPException(status_code=400, detail='Invalid confidence filter')
    try:
        service = get_neo4j_service()
        if service.get_case(case_id) is None:
            raise HTTPException(status_code=404, detail='Case not found')
        return graph_response(service.case_graph_rows(case_id), allowed_confidence=allowed, limit=limit)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f'Neo4j unavailable: {type(exc).__name__}') from exc
