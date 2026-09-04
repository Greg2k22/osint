from fastapi import APIRouter

from osint_workbench.services.system_status import build_system_status

router = APIRouter()


@router.get('/api/system/status')
def api_system_status():
    return build_system_status()
