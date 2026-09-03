from datetime import datetime, timezone
from pydantic import BaseModel, Field


class Evidence(BaseModel):
    type: str
    value: str
    collector: str
    source_group: str
    case_id: str
    provider: str | None = None
    confidence: str = "UNVERIFIED"
    observed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    raw_reference: str | None = None
