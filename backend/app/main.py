from contextlib import asynccontextmanager
from typing import Any

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from backend.app.config import get_settings
from backend.app.database import database_ready, get_db, init_db
from backend.app.models import CustomerBug, TestFailure
from backend.app.schemas import (
    AnalysisOut,
    BugCreate,
    BugDetailOut,
    BugOut,
    HealthOut,
    MatchOut,
    TestFailureOut,
)
from backend.app.services.embeddings import get_embedding_service
from backend.app.services.gemini import analyze_bug
from backend.app.services.payload_types import BugPayload, FailurePayload, MatchPayload
from backend.app.services.similarity import find_top_matches


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


settings = get_settings()
app = FastAPI(title=settings.app_name, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _bug_text(payload: BugCreate) -> str:
    return "\n".join(
        value
        for value in [payload.title, payload.description, payload.stack_trace or ""]
        if value
    )


def _failure_payload(failure: TestFailure) -> FailurePayload:
    return FailurePayload(**TestFailureOut.model_validate(failure).model_dump())


def _match_payload(matches: list[tuple[TestFailure, float]]) -> list[MatchPayload]:
    return [
        {"score": round(float(score), 4), "failure": _failure_payload(failure)}
        for failure, score in matches
    ]


@app.get("/health", response_model=HealthOut)
def health() -> HealthOut:
    return HealthOut(
        app=settings.app_name,
        database=database_ready(),
        ai_provider="gemini-2.5-flash",
        mock_fallback_enabled=settings.enable_mock_fallback,
    )


@app.post("/bugs", response_model=BugDetailOut)
def create_bug(payload: BugCreate, db: Session = Depends(get_db)) -> BugDetailOut:
    embedder = get_embedding_service()
    embedding = embedder.embed(_bug_text(payload))
    top_matches = find_top_matches(db, embedding, limit=5)
    matches = _match_payload(top_matches)

    bug_payload: BugPayload = {
            "title": payload.title,
            "description": payload.description,
            "stack_trace": payload.stack_trace,
            "severity": payload.severity,
            "environment": payload.environment,
    }
    analysis = analyze_bug(bug_payload, matches)

    bug = CustomerBug(
        title=payload.title,
        description=payload.description,
        stack_trace=payload.stack_trace,
        severity=payload.severity,
        environment=payload.environment,
        category=analysis.get("category"),
        status=analysis.get("status", "analyzed"),
        embedding=embedding,
        analysis=analysis,
        matches=matches,
    )
    db.add(bug)
    db.commit()
    db.refresh(bug)

    return BugDetailOut(
        bug=BugOut.model_validate(bug),
        analysis=AnalysisOut(**analysis),
        matches=[
            MatchOut(score=item["score"], failure=TestFailureOut(**item["failure"]))
            for item in matches
        ],
    )


@app.get("/bugs", response_model=list[BugOut])
def list_bugs(limit: int = 20, db: Session = Depends(get_db)) -> list[BugOut]:
    limit = max(1, min(limit, 100))
    bugs = (
        db.query(CustomerBug)
        .order_by(CustomerBug.created_at.desc(), CustomerBug.id.desc())
        .limit(limit)
        .all()
    )
    return [BugOut.model_validate(bug) for bug in bugs]


@app.get("/bugs/{bug_id}", response_model=BugDetailOut)
def get_bug(bug_id: int, db: Session = Depends(get_db)) -> BugDetailOut:
    bug = db.get(CustomerBug, bug_id)
    if bug is None:
        raise HTTPException(status_code=404, detail="Bug not found")

    raw_matches = bug.matches or []
    matches = [
        MatchOut(score=item["score"], failure=item["failure"])
        for item in raw_matches
        if "score" in item and "failure" in item
    ]
    analysis = AnalysisOut(**bug.analysis) if bug.analysis else None
    return BugDetailOut(bug=BugOut.model_validate(bug), analysis=analysis, matches=matches)
