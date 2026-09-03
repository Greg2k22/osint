from datetime import datetime, timezone
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class Profile(StrEnum):
    PERSON = "PERSON"
    DOMAIN = "DOMAIN"
    ORG = "ORG"
    FULL = "FULL"


class RetentionMode(StrEnum):
    EPHEMERAL = "EPHEMERAL"
    CASE = "CASE"
    ARCHIVE = "ARCHIVE"


class ExecutionMode(StrEnum):
    PASSIVE = "PASSIVE"
    ACTIVE = "ACTIVE"


class Confidence(StrEnum):
    CONFIRMED = "CONFIRMED"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    UNVERIFIED = "UNVERIFIED"


class RunRequest(BaseModel):
    profile: Profile
    target: str = Field(min_length=1)
    retention: RetentionMode
    mode: ExecutionMode = ExecutionMode.PASSIVE
    active_authorized: bool = False
    active_scope: str | None = None


class NormalizedFinding(BaseModel):
    entity_type: str
    value: str
    source: str
    tool: str
    confidence: Confidence = Confidence.UNVERIFIED
    acquired_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    case_id: str | None = None
    run_id: str | None = None
    attributes: dict[str, Any] = Field(default_factory=dict)
