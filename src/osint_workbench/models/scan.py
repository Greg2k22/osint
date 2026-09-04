from pydantic import BaseModel


class ScanRequest(BaseModel):
    type: str
    target: str
    active: bool = False
    authorized: bool = False


def validate_scan_request(request: ScanRequest) -> ScanRequest:
    scan_type = request.type.upper().strip()
    target = request.target.strip()
    if scan_type not in {"DOMAIN", "PERSON", "EMAIL"}:
        raise ValueError("Unsupported scan type")
    if not target:
        raise ValueError("Target is required")
    if request.active and not request.authorized:
        raise ValueError("ACTIVE mode requires explicit authorization")
    if request.active and scan_type != "DOMAIN":
        raise ValueError("ACTIVE mode is currently supported only for DOMAIN")
    return request.model_copy(update={"type": scan_type, "target": target})
