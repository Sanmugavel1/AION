"""
AION Dialect-Agnostic Column Types
Uses native PostgreSQL UUID/JSONB when running on Postgres, and falls back to
CHAR(36)/JSON on SQLite (or any other backend) so the same models run against
either database with zero code changes at the call site.
"""
from __future__ import annotations

import uuid as uuid_pkg

from sqlalchemy import CHAR, JSON, TypeDecorator
from sqlalchemy.dialects.postgresql import JSONB as PG_JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID


class UUID(TypeDecorator):
    """Platform-independent UUID type."""

    impl = CHAR
    cache_ok = True

    def __init__(self, as_uuid: bool = True, *args, **kwargs) -> None:
        self.as_uuid = as_uuid
        super().__init__(*args, **kwargs)

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PG_UUID(as_uuid=self.as_uuid))
        return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        if dialect.name == "postgresql":
            return value
        if not isinstance(value, uuid_pkg.UUID):
            value = uuid_pkg.UUID(str(value))
        return str(value)

    def process_result_value(self, value, dialect):
        if value is None or dialect.name == "postgresql":
            return value
        if not isinstance(value, uuid_pkg.UUID):
            return uuid_pkg.UUID(str(value))
        return value


class JSONB(TypeDecorator):
    """Platform-independent JSON type."""

    impl = JSON
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PG_JSONB())
        return dialect.type_descriptor(JSON())
