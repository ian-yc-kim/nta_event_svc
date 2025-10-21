from typing import List
import logging
import copy

from fastapi import APIRouter, Depends, HTTPException, Response, status, BackgroundTasks
from sqlalchemy import select
from sqlalchemy.orm import Session

from event_service.database import get_db, SessionLocal
from event_service.models.event import Event
from event_service.schemas.event import EventCreate, EventUpdate, EventResponse
from event_service.services.smtp import SMTPService
from event_service.core.config import Settings, settings

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


def _participants_changed(orig: List[str] | None, new: List[str] | None) -> bool:
    # Normalize None vs empty list semantics: None != []
    try:
        if orig is None and new is None:
            return False
        if orig is None and new is not None:
            return True
        if orig is not None and new is None:
            return True
        # both lists: compare sorted values
        return sorted(orig) != sorted(new)
    except Exception as e:
        logging.error(e, exc_info=True)
        # If comparison fails, assume changed to be safe
        return True


def _field_changed(orig, new) -> bool:
    try:
        return orig != new
    except Exception as e:
        logging.error(e, exc_info=True)
        return True


def _send_event_update_email_task(event_id: int, db: Session, settings: Settings) -> None:
    """Background task: fetch latest event and send update emails to participants."""
    try:
        try:
            stmt = select(Event).where(Event.id == event_id)
            ev = db.execute(stmt).scalar_one_or_none()
            if ev is None:
                logging.info("Event not found in background task: %s", event_id)
                return

            participants = ev.participants or []
            if not participants:
                logging.info("No participants to notify for event %s", event_id)
                return

            smtp_service = SMTPService.from_settings(settings)

            subject = f"Event Update: {ev.name}"
            # Build a concise body summarizing key fields
            body_lines = [f"Event '{ev.name}' has been updated.", "", "Updated details:"]
            body_lines.append(f"Description: {ev.description}")
            body_lines.append(f"Start time: {ev.start_time}")
            body_lines.append(f"End time: {ev.end_time}")
            body_lines.append(f"Location: {ev.location}")
            body_lines.append(f"Participants: {', '.join(participants)}")
            body = "\n".join(body_lines)

            try:
                smtp_service.send_email(to_emails=participants, subject=subject, body=body)
                logging.info("Sent event update email for event %s to %s", event_id, participants)
            except Exception as e:
                logging.error(e, exc_info=True)
        except Exception as e:
            logging.error(e, exc_info=True)
    finally:
        try:
            db.close()
        except Exception:
            logging.error("Failed to close DB session in background task", exc_info=True)


@router.put("/{event_id}", response_model=EventResponse)
def update_event(event_id: int, event_in: EventUpdate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)) -> Event:
    try:
        # Retrieve existing event and snapshot fields for comparison
        stmt = select(Event).where(Event.id == event_id)
        ev = db.execute(stmt).scalar_one_or_none()
        if ev is None:
            raise HTTPException(status_code=404, detail="Event not found")

        # Make deep copies of list fields to avoid mutation issues
        orig_start = copy.deepcopy(ev.start_time)
        orig_end = copy.deepcopy(ev.end_time)
        orig_location = copy.deepcopy(ev.location)
        orig_participants = copy.deepcopy(ev.participants)

        update_data = event_in.model_dump(exclude_none=True)
        for key, value in update_data.items():
            setattr(ev, key, value)

        db.add(ev)
        db.commit()
        db.refresh(ev)

        # Compare relevant fields to decide whether to schedule emails
        changed = False
        if _field_changed(orig_start, ev.start_time):
            changed = True
        if _field_changed(orig_end, ev.end_time):
            changed = True
        if _field_changed(orig_location, ev.location):
            changed = True
        if _participants_changed(orig_participants, ev.participants):
            changed = True

        if changed:
            # Provide a separate DB session for the background task
            db_task_session = None
            try:
                db_task_session = SessionLocal()
                background_tasks.add_task(_send_event_update_email_task, ev.id, db_task_session, settings)
            except Exception as e:
                logging.error(e, exc_info=True)
                if db_task_session is not None:
                    try:
                        db_task_session.close()
                    except Exception:
                        logging.error("Failed to close db_task_session after scheduling failure", exc_info=True)

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
