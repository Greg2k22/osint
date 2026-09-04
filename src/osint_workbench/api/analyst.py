from __future__ import annotations

import os
import re
from pathlib import Path

from fastapi import APIRouter, HTTPException

from osint_workbench.services.analyst_service import AnalystService

router = APIRouter()
_SAFE_CASE = re.compile(r'^[A-Za-z0-9._-]{1,200}$')


def _case_dir(case_id: str) -> Path:
    if not _SAFE_CASE.fullmatch(case_id):
        raise HTTPException(status_code=400, detail='Invalid case id')
    case = Path(os.environ.get('OSINT_CASES_ROOT', '/data/cases')) / case_id
    if not case.is_dir():
        raise HTTPException(status_code=404, detail='Case not found')
    return case


@router.get('/api/cases/{case_id}/analysis')
def api_case_analysis(case_id: str):
    return AnalystService().analyze_case(_case_dir(case_id))
