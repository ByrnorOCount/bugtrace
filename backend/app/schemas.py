from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


Severity = Literal["low", "medium", "high", "critical"]


class BugCreate(BaseModel):
    title: str = Field(min_length=4, max_length=180)
    description: str = Field(min_length=10)
    stack_trace: str | None = None
    severity: Severity = "medium"
    environment: str | None = Field(default=None, max_length=120)


class TestFailureOut(BaseModel):
    id: int
    test_name: str
    suite: str | None
    failure_signature: str
    stack_trace: str
    root_cause: str
    fix_hint: str
    category: str

    model_config = {"from_attributes": True}


class MatchOut(BaseModel):
    score: float
    failure: TestFailureOut


class AnalysisOut(BaseModel):
    category: str
    root_cause: str
    suggested_fix: str
    confidence: float
    status: str
    used_fallback: bool = False
    reasoning_notes: list[str] = []


class BugOut(BaseModel):
    id: int
    title: str
    description: str
    stack_trace: str | None
    severity: str
    environment: str | None
    category: str | None
    status: str
    analysis: dict[str, Any] | None
    matches: list[dict[str, Any]] | None
    created_at: datetime

    model_config = {"from_attributes": True}


class BugDetailOut(BaseModel):
    bug: BugOut
    analysis: AnalysisOut | None
    matches: list[MatchOut]


class HealthOut(BaseModel):
    app: str
    database: bool
    ai_provider: str
    mock_fallback_enabled: bool
