from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class CustomerBug(Base):
    __tablename__ = "customer_bugs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(180), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    stack_trace: Mapped[str | None] = mapped_column(Text)
    severity: Mapped[str] = mapped_column(String(24), default="medium")
    environment: Mapped[str | None] = mapped_column(String(120))
    category: Mapped[str | None] = mapped_column(String(80))
    status: Mapped[str] = mapped_column(String(32), default="analyzed")
    embedding: Mapped[list[float] | None] = mapped_column(JSONB)
    analysis: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    matches: Mapped[list[dict[str, Any]] | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class TestFailure(Base):
    __tablename__ = "test_failures"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    test_name: Mapped[str] = mapped_column(String(180), nullable=False)
    suite: Mapped[str | None] = mapped_column(String(120))
    failure_signature: Mapped[str] = mapped_column(String(220), nullable=False)
    stack_trace: Mapped[str] = mapped_column(Text, nullable=False)
    root_cause: Mapped[str] = mapped_column(Text, nullable=False)
    fix_hint: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(80), default="unknown")
    embedding: Mapped[list[float] | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class SeedExample(Base):
    __tablename__ = "seed_examples"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    bug_title: Mapped[str] = mapped_column(String(180), nullable=False)
    bug_description: Mapped[str] = mapped_column(Text, nullable=False)
    bug_stack_trace: Mapped[str | None] = mapped_column(Text)
    severity: Mapped[str] = mapped_column(String(24), default="medium")
    environment: Mapped[str | None] = mapped_column(String(120))
    test_failure_id: Mapped[int] = mapped_column(ForeignKey("test_failures.id"))
    test_failure: Mapped[TestFailure] = relationship()
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
