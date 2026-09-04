from __future__ import annotations

import os
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from osint_workbench.services.pivot_service import auto_enqueue, build_pivot_plan, enqueue_pivot

router = APIRouter()
CASES_ROOT = Path(os.environ.get("OSINT_CASES_ROOT", "/data/cases"))
JOBS_ROOT = Path(os.environ.get("OSINT_JOBS_ROOT", "/data/jobs"))


class AutoEnqueueRequest(BaseModel):
    min_score: int = Field(default=60, ge=0, le=100)
    max_count: int = Field(default=5, ge=1, le=10)
    max_depth: int = Field(default=2, ge=1, le=3)


@router.get("/api/cases/{case_id}/pivots")
def api_pivots(case_id: str, max_depth: int = Query(2, ge=1, le=3), limit: int = Query(50, ge=1, le=100)):
    try:
        return build_pivot_plan(case_id, CASES_ROOT, JOBS_ROOT, max_depth=max_depth, limit=limit)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Case not found") from exc


@router.post("/api/cases/{case_id}/pivots/{pivot_id}/enqueue", status_code=202)
def api_enqueue_pivot(case_id: str, pivot_id: str):
    try:
        return enqueue_pivot(case_id, pivot_id, CASES_ROOT, JOBS_ROOT)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Case not found") from exc
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Pivot not found") from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/api/cases/{case_id}/pivots/auto-enqueue", status_code=202)
def api_auto_enqueue(case_id: str, request: AutoEnqueueRequest):
    try:
        enqueued = auto_enqueue(
            case_id,
            CASES_ROOT,
            JOBS_ROOT,
            min_score=request.min_score,
            max_count=request.max_count,
            max_depth=request.max_depth,
        )
        return {"case_id": case_id, "enqueued": enqueued, "active": False}
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Case not found") from exc
