from __future__ import annotations

import json
import os
import re
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse, Response

from osint_workbench.services.report_service import build_report_from_case, render_csv, render_markdown

router = APIRouter()
_SAFE_CASE = re.compile(r'^[A-Za-z0-9._-]{1,200}$')


def _case_dir(case_id: str) -> Path:
    if not _SAFE_CASE.fullmatch(case_id):
        raise HTTPException(status_code=400, detail='Invalid case id')
    root = Path(os.environ.get('OSINT_CASES_ROOT', '/data/cases'))
    case = root / case_id
    if not case.is_dir():
        raise HTTPException(status_code=404, detail='Case not found')
    return case


@router.get('/api/cases/{case_id}/report')
def api_case_report(case_id: str):
    return build_report_from_case(_case_dir(case_id))


@router.get('/api/cases/{case_id}/report.md', response_class=PlainTextResponse)
def api_case_report_markdown(case_id: str):
    return render_markdown(build_report_from_case(_case_dir(case_id)))


@router.get('/api/cases/{case_id}/export.json')
def api_case_export_json(case_id: str):
    return build_report_from_case(_case_dir(case_id))


@router.get('/api/cases/{case_id}/export.csv')
def api_case_export_csv(case_id: str):
    body = render_csv(build_report_from_case(_case_dir(case_id)))
    return Response(content=body, media_type='text/csv; charset=utf-8')
