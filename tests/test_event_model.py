import os
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from event_service.database import Base
from event_service.models.event import Event


def test_event_crud_sqlite_in_memory():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    try:
        ev = Event(name="Test Event", description="A test", location="Nowhere", participants=["alice", "bob"])
        session.add(ev)
        session.commit()
        assert ev.id is not None

        stmt = select(Event).where(Event.id == ev.id)
        result = session.execute(stmt).scalar_one()
        assert result.name == "Test Event"

        # update
        result.name = "Updated"
        session.commit()
        result2 = session.execute(select(Event).where(Event.id == ev.id)).scalar_one()
        assert result2.name == "Updated"

        # delete
        session.delete(result2)
        session.commit()
        res = session.execute(select(Event).where(Event.id == ev.id)).all()
        assert res == []
    finally:
        session.close()
