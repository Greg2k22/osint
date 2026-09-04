from fastapi import APIRouter, HTTPException

from osint_workbench.services.neo4j_service import get_neo4j_service

router = APIRouter()


@router.get('/api/cases')
def api_cases():
    try:
        return {'cases': get_neo4j_service().list_cases()}
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f'Neo4j unavailable: {type(exc).__name__}') from exc


@router.get('/api/cases/{case_id}')
def api_case_detail(case_id: str):
    try:
        result = get_neo4j_service().get_case(case_id)
        if result is None:
            raise HTTPException(status_code=404, detail='Case not found')
        return result
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f'Neo4j unavailable: {type(exc).__name__}') from exc
