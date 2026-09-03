from typing import Any

from pydantic import BaseModel, Field

from osint_workbench.domain.models import NormalizedFinding


class WorkerResult(BaseModel):
    tool: str
    findings: list[NormalizedFinding] = Field(default_factory=list)
    raw: dict[str, Any] = Field(default_factory=dict)
