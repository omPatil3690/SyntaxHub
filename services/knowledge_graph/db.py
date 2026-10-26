"""
The API Knowledge Graph: Framework -> Version -> API -> Status -> Replacement.
This is the deterministic source of truth every other phase (analyzer,
migration planner, patch generator) queries against — never let an LLM
originate a "this API is deprecated" claim; it should only ever explain
or act on what's here.
"""
from __future__ import annotations

from sqlalchemy import String, Text, UniqueConstraint, select
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from packages.schemas.models import ApiStatus, ChangeType, KnowledgeGraphEntry, Severity
from settings import Settings


class Base(AsyncAttrs, DeclarativeBase):
    pass


class ApiEntry(Base):
    __tablename__ = "api_knowledge_graph"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    framework: Mapped[str] = mapped_column(String(64), index=True)
    api_name: Mapped[str] = mapped_column(String(256), index=True)
    introduced_in: Mapped[str | None] = mapped_column(String(32), nullable=True)
    deprecated_in: Mapped[str | None] = mapped_column(String(32), nullable=True)
    removed_in: Mapped[str | None] = mapped_column(String(32), nullable=True)
    status: Mapped[str] = mapped_column(String(16))
    replacement: Mapped[str | None] = mapped_column(String(256), nullable=True)
    change_type: Mapped[str] = mapped_column(String(32))
    severity: Mapped[str] = mapped_column(String(16))
    detection_pattern: Mapped[str] = mapped_column(Text)
    migration_hint: Mapped[str] = mapped_column(Text)
    doc_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)

    __table_args__ = (UniqueConstraint("framework", "api_name", name="uq_framework_api"),)


def make_engine(settings: Settings):
    url = settings.database_url.replace("postgresql+psycopg://", "postgresql+asyncpg://")
    return create_async_engine(url, pool_size=5, max_overflow=10, pool_pre_ping=True)


async def init_db(settings: Settings) -> None:
    engine = make_engine(settings)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()


def make_session_factory(settings: Settings):
    return async_sessionmaker(make_engine(settings), expire_on_commit=False)


async def upsert_entries(session, entries: list[KnowledgeGraphEntry]) -> int:
    count = 0
    for e in entries:
        existing = await session.scalar(
            select(ApiEntry).where(ApiEntry.framework == e.framework, ApiEntry.api_name == e.api_name)
        )
        if existing:
            for field in ("introduced_in", "deprecated_in", "removed_in", "replacement",
                           "detection_pattern", "migration_hint", "doc_url"):
                setattr(existing, field, getattr(e, field))
            existing.status = e.status.value
            existing.change_type = e.change_type.value
            existing.severity = e.severity.value
        else:
            session.add(ApiEntry(
                framework=e.framework, api_name=e.api_name,
                introduced_in=e.introduced_in, deprecated_in=e.deprecated_in, removed_in=e.removed_in,
                status=e.status.value, replacement=e.replacement, change_type=e.change_type.value,
                severity=e.severity.value, detection_pattern=e.detection_pattern,
                migration_hint=e.migration_hint, doc_url=e.doc_url,
            ))
            count += 1
    return count


async def entries_for_framework(session, framework: str) -> list[KnowledgeGraphEntry]:
    rows = (await session.scalars(select(ApiEntry).where(ApiEntry.framework == framework))).all()
    return [
        KnowledgeGraphEntry(
            framework=r.framework, introduced_in=r.introduced_in, deprecated_in=r.deprecated_in,
            removed_in=r.removed_in, api_name=r.api_name, status=ApiStatus(r.status),
            replacement=r.replacement, change_type=ChangeType(r.change_type),
            severity=Severity(r.severity), detection_pattern=r.detection_pattern,
            migration_hint=r.migration_hint, doc_url=r.doc_url,
        )
        for r in rows
    ]
