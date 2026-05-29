import argparse

from backend.app.config import get_settings
from backend.app.database import SessionLocal, init_db
from backend.app.models import SeedExample, TestFailure
from backend.app.services.embeddings import get_embedding_service
from backend.app.services.gemini import generate_seed_cases
from backend.app.services.payload_types import SeedCase


def failure_text(case: SeedCase) -> str:
    return "\n".join(
        [
            case["test_name"],
            case["failure_signature"],
            case["stack_trace"],
            case["root_cause"],
            case["fix_hint"],
        ]
    )


def seed(count: int, reset: bool = False) -> int:
    init_db()
    embedder = get_embedding_service()
    cases = generate_seed_cases(count)

    with SessionLocal() as db:
        if reset:
            db.query(SeedExample).delete()
            db.query(TestFailure).delete()
            db.commit()

        inserted = 0
        for case in cases:
            failure = TestFailure(
                test_name=case["test_name"],
                suite=case.get("suite"),
                failure_signature=case["failure_signature"],
                stack_trace=case["stack_trace"],
                root_cause=case["root_cause"],
                fix_hint=case["fix_hint"],
                category=case.get("category", "unknown"),
                embedding=embedder.embed(failure_text(case)),
            )
            db.add(failure)
            db.flush()
            db.add(
                SeedExample(
                    bug_title=case["title"],
                    bug_description=case["description"],
                    bug_stack_trace=case.get("stack_trace"),
                    severity=case.get("severity", "medium"),
                    environment=case.get("environment"),
                    test_failure_id=failure.id,
                )
            )
            inserted += 1
        db.commit()
        return inserted


def main() -> None:
    settings = get_settings()
    parser = argparse.ArgumentParser(description="Seed BugTrace synthetic failures")
    parser.add_argument("--count", type=int, default=settings.seed_record_count)
    parser.add_argument("--reset", action="store_true")
    args = parser.parse_args()

    inserted = seed(args.count, reset=args.reset)
    print(f"Seeded {inserted} synthetic failure records.")


if __name__ == "__main__":
    main()
