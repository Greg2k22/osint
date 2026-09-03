from fastapi import APIRouter, HTTPException
from osint_workbench.domain.models import RunRequest
from osint_workbench.domain.policy import PolicyViolation
from osint_workbench.services.orchestrator import select_workers

router = APIRouter(prefix='/api/v1/runs', tags=['runs'])

@router.post('/validate')
def validate_run(request: RunRequest):
    try:
        workers = select_workers(request)
    except PolicyViolation as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {'workers': workers, 'mode': request.mode, 'profile': request.profile}
