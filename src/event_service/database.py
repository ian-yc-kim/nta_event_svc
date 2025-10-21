from typing import Iterator
import logging
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, Session

from event_service.core.config import settings

# Create engine with sqlite connect args when needed
try:
    database_url = settings.DATABASE_URL
except Exception as e:
    logging.error(e, exc_info=True)
    # fallback to sqlite local file
    database_url = os.environ.get("DATABASE_URL", "sqlite:///./local.db")

connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}

engine = create_engine(database_url, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logging.error(e, exc_info=True)
        raise
    finally:
        db.close()
