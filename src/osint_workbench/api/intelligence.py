from __future__ import annotations

import os
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query

from osint_workbench.services.correlation_service import related_cases, search_cases

router = APIRouter()
CASES_ROOT = Path(os.environ.get("OSINT_CASES_ROOT", "/data/cases"))


@router.get("/api/search")
def api_search(q: str = Query(..., min_length=1, max_length=200), limit: int = Query(50, ge=1, le=100)):
    return {"query": q, "cases": search_cases(q, CASES_ROOT, limit=limit)}


@router.get("/api/cases/{case_id}/related")
def api_related(case_id: str, limit: int = Query(20, ge=1, le=100)):
    try:
        return {"case_id": case_id, "related": related_cases(case_id, CASES_ROOT, limit=limit)}
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Case not found") from exc
