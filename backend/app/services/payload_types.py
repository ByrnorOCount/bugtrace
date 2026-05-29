from typing import NotRequired, TypedDict


class SeedCase(TypedDict):
    title: str
    description: str
    stack_trace: str
    severity: str
    environment: str
    test_name: str
    suite: str
    failure_signature: str
    root_cause: str
    fix_hint: str
    category: str


class FailurePayload(TypedDict):
    id: int
    test_name: str
    suite: str | None
    failure_signature: str
    stack_trace: str
    root_cause: str
    fix_hint: str
    category: str


class MatchPayload(TypedDict):
    score: float
    failure: FailurePayload


class BugPayload(TypedDict):
    title: str
    description: str
    stack_trace: str | None
    severity: str
    environment: str | None


class AnalysisPayload(TypedDict):
    category: str
    root_cause: str
    suggested_fix: str
    confidence: float
    status: str
    used_fallback: bool
    reasoning_notes: list[str]


class GeminiAnalysisPayload(TypedDict):
    category: str
    root_cause: str
    suggested_fix: str
    confidence: float
    status: str
    reasoning_notes: list[str]
    used_fallback: NotRequired[bool]
