from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.types import TypeDecorator, JSON as SAJSON
from sqlalchemy.dialects.postgresql import ARRAY as PG_ARRAY
from sqlalchemy import String as SAString
from event_service.database import Base
from typing import Optional, List
import logging
from datetime import datetime


class ParticipantsType(TypeDecorator):
    """Dialect-aware participants type.

    Uses PostgreSQL ARRAY(String) on Postgres and JSON on other dialects (SQLite).
    This keeps the SQLAlchemy model compatible with both DB backends while
    matching the specification semantics for Postgres.
    """

    impl = SAJSON
    cache_ok = True

    def load_dialect_impl(self, dialect):
        try:
            if getattr(dialect, "name", None) == "postgresql":
                return dialect.type_descriptor(PG_ARRAY(SAString()))
        except Exception as e:
            logging.error(e, exc_info=True)
        # Fallback to JSON for non-postgres dialects
        return dialect.type_descriptor(SAJSON())

    def process_bind_param(self, value: Optional[List[str]], dialect):
        try:
            # for both ARRAY and JSON we can pass the python list through
            return value
        except Exception as e:
            logging.error(e, exc_info=True)
            raise

    def process_result_value(self, value, dialect):
        try:
            return value
        except Exception as e:
            logging.error(e, exc_info=True)
            raise


class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    start_time = Column(DateTime, nullable=True)
    end_time = Column(DateTime, nullable=True)
    location = Column(String, nullable=True)
    # Dialect-aware participants column: Postgres ARRAY(String) else JSON
    participants = Column(ParticipantsType(), nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self) -> str:
        return f"<Event(id={self.id}, name='{self.name}')>"
