import json
import os
import secrets
from pathlib import Path
import uuid

from fastapi import APIRouter, Header, HTTPException

from osint_workbench.models.scan import ScanRequest, validate_scan_request


router = APIRouter()
JOBS_PENDING = Path("/data/jobs/pending")


def _verify_active_token(request: ScanRequest, supplied_token: str | None) -> None:
    if not request.active:
        return

    expected_token = os.environ.get("OSINT_ACTIVE_TOKEN", "").strip()

    if not expected_token:
        raise HTTPException(
            status_code=403,
            detail="ACTIVE mode is disabled: OSINT_ACTIVE_TOKEN is not configured",
        )

    if not supplied_token or not secrets.compare_digest(
        supplied_token,
        expected_token,
    ):
        raise HTTPException(
            status_code=403,
            detail="Invalid ACTIVE authorization token",
        )


@router.post("/api/scan", status_code=202)
def api_scan(
    request: ScanRequest,
    x_osint_active_token: str | None = Header(
        default=None,
        alias="X-OSINT-Active-Token",
    ),
):
    try:
        request = validate_scan_request(request)
    except ValueError as exc:
        message = str(exc)
        status = 403 if "authorization" in message.lower() else 400
        raise HTTPException(status_code=status, detail=message) from exc

    _verify_active_token(request, x_osint_active_token)

    job_id = uuid.uuid4().hex
    JOBS_PENDING.mkdir(parents=True, exist_ok=True)

    payload = {
        "id": job_id,
        "type": request.type,
        "target": request.target,
        "active": request.active,
        "authorized": request.authorized,
        "status": "PENDING",
    }

    tmp = JOBS_PENDING / f".{job_id}.tmp"
    dst = JOBS_PENDING / f"{job_id}.json"

    tmp.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    tmp.replace(dst)

    return payload
