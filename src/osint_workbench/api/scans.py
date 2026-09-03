import json
from pathlib import Path
import uuid
from fastapi import APIRouter, HTTPException
from osint_workbench.models.scan import ScanRequest, validate_scan_request

router = APIRouter()
JOBS_PENDING = Path("/data/jobs/pending")


@router.post("/api/scan", status_code=202)
def api_scan(request: ScanRequest):
    try:
        request = validate_scan_request(request)
    except ValueError as exc:
        message = str(exc)
        status = 403 if "authorization" in message.lower() else 400
        raise HTTPException(status_code=status, detail=message) from exc

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
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(dst)
    return payload
