import math

from sqlalchemy.orm import Session

from backend.app.models import TestFailure


def cosine_similarity(left: list[float], right: list[float]) -> float:
    if not left or not right or len(left) != len(right):
        return 0.0
    dot = sum(a * b for a, b in zip(left, right))
    left_norm = math.sqrt(sum(a * a for a in left))
    right_norm = math.sqrt(sum(b * b for b in right))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return dot / (left_norm * right_norm)


def find_top_matches(
    db: Session, query_embedding: list[float], limit: int = 5
) -> list[tuple[TestFailure, float]]:
    failures = db.query(TestFailure).filter(TestFailure.embedding.is_not(None)).all()
    scored = [
        (failure, cosine_similarity(query_embedding, failure.embedding or []))
        for failure in failures
    ]
    scored.sort(key=lambda item: item[1], reverse=True)
    return scored[:limit]
