"""Add the SRS v2 enterprise tables and the approval-chain columns on knowledge_items.

Idempotent: safe to re-run. SQLite cannot add a column that already exists, so each
column is checked against PRAGMA table_info first.
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import text

import app.models  # noqa: F401  — registers every model on the shared metadata
from app.core.database import engine
from app.models.base import Base

NEW_KNOWLEDGE_COLUMNS = {
    "workflow_status": "VARCHAR(30) NOT NULL DEFAULT 'approved'",
    "submitted_by_id": "CHAR(32)",
    "reviewed_by_id": "CHAR(32)",
    "approved_by_id": "CHAR(32)",
    "approved_at": "DATETIME",
    "is_published": "BOOLEAN DEFAULT 0",
}


async def main() -> None:
    async with engine.begin() as conn:
        before = set(await conn.run_sync(lambda c: set(Base.metadata.tables)))
        await conn.run_sync(Base.metadata.create_all)

        rows = await conn.execute(text("PRAGMA table_info(knowledge_items)"))
        existing = {r[1] for r in rows}

        added = []
        for col, ddl in NEW_KNOWLEDGE_COLUMNS.items():
            if col not in existing:
                await conn.execute(text(f"ALTER TABLE knowledge_items ADD COLUMN {col} {ddl}"))
                added.append(col)

        tables = await conn.execute(
            text("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        )
        names = [t[0] for t in tables]

    print(f"knowledge_items columns added: {added or 'none (already present)'}")
    print(f"tables now in database ({len(names)}):")
    for n in names:
        marker = "  NEW ->" if n in {
            "approval_logs", "marketplace_items", "marketplace_reuses",
            "notifications", "timeline_events", "learning_records", "audit_logs",
        } else "        "
        print(f"{marker} {n}")
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
