from typing import List
import logging

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from event_service.database import get_db
from event_service.models.event import Event
from event_service.schemas.event import EventCreate, EventUpdate, EventResponse

router = APIRouter(prefix="/events", tags=["events"])


@router.post("", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
def create_event(event_in: EventCreate, db: Session = Depends(get_db)) -> Event:
    try:
        payload = event_in.model_dump()
        ev = Event(**payload)
        db.add(ev)
        db.commit()
        db.refresh(ev)
        return ev
    except Exception as e:
        logging.error(e, exc_info=True)
        try:
            db.rollback()
        except Exception:
            logging.error("Failed to rollback session", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to create event")


@router.get("", response_model=List[EventResponse])
def list_events(db: Session = Depends(get_db)) -> List[Event]:
    try:
        stmt = select(Event)
        results = db.execute(stmt).scalars().all()
        return results
    except Exception as e:
        logging.error(e, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to list events")


@router.get("/{event_id}", response_model=EventResponse)
def get_event(event_id: int, db: Session = Depends(get_db)) -> Event:
    try:
        stmt = select(Event).where(Event.id == event_id)
        ev = db.execute(stmt).scalar_one_or_none()
        if ev is None:
            raise HTTPException(status_code=404, detail="Event not found")
        return ev
    except HTTPException:
        raise
    except Exception as e:
        logging.error(e, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve event")


@router.put("/{event_id}", response_model=EventResponse)
def update_event(event_id: int, event_in: EventUpdate, db: Session = Depends(get_db)) -> Event:
    try:
        stmt = select(Event).where(Event.id == event_id)
        ev = db.execute(stmt).scalar_one_or_none()
        if ev is None:
            raise HTTPException(status_code=404, detail="Event not found")

        update_data = event_in.model_dump(exclude_none=True)
        for key, value in update_data.items():
            setattr(ev, key, value)

        db.add(ev)
        db.commit()
        db.refresh(ev)
        return ev
    except HTTPException:
        raise
    except Exception as e:
        logging.error(e, exc_info=True)
        try:
            db.rollback()
        except Exception:
            logging.error("Failed to rollback session", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to update event")


@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_event(event_id: int, db: Session = Depends(get_db)) -> Response:
    try:
        stmt = select(Event).where(Event.id == event_id)
        ev = db.execute(stmt).scalar_one_or_none()
        if ev is None:
            raise HTTPException(status_code=404, detail="Event not found")

        db.delete(ev)
        db.commit()
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except HTTPException:
        raise
    except Exception as e:
        logging.error(e, exc_info=True)
        try:
            db.rollback()
        except Exception:
            logging.error("Failed to rollback session", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to delete event")
