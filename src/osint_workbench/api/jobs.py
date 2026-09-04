import json
from pathlib import Path
from fastapi import APIRouter

router = APIRouter()
JOBS_ROOT = Path("/data/jobs")


@router.get("/api/jobs")
def api_jobs():
    result = []
    for status in ("pending", "running", "done", "failed"):
        folder = JOBS_ROOT / status
        if not folder.exists():
            continue
        for item in sorted(folder.glob("*.json"), reverse=True):
            try:
                payload = json.loads(item.read_text(encoding="utf-8"))
            except Exception:
                continue
            payload["queue"] = status.upper()
            payload["file"] = item.name
            result.append(payload)
    return {"jobs": result}
