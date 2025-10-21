from unittest.mock import MagicMock, patch
from event_service.schemas.event import EventUpdate
from event_service.database import SessionLocal
from event_service.core.config import settings
from event_service.api import event as event_module


def _create_payload(name: str = "Test Event") -> dict:
    return {
        "name": name,
        "description": "A sample event",
        "location": "Virtual",
        "participants": ["alice@example.com", "bob@example.com"],
    }


def test_no_email_for_name_or_description_change(client):
    payload = _create_payload()
    created = client.post("/events", json=payload).json()
    ev_id = created["id"]

    update = EventUpdate(name="New Name")
    mock_bg = MagicMock()
    db = SessionLocal()
    try:
        event_module.update_event(ev_id, update, db=db, background_tasks=mock_bg)
    finally:
        db.close()

    # No relevant fields changed, so add_task should not be called
    assert mock_bg.add_task.call_count == 0


def test_email_scheduled_on_relevant_changes(client):
    payload = _create_payload("Notify Event")
    created = client.post("/events", json=payload).json()
    ev_id = created["id"]

    # Change participants (relevant field)
    update = EventUpdate(participants=["x@example.com"]) 
    mock_bg = MagicMock()
    db = SessionLocal()
    try:
        event_module.update_event(ev_id, update, db=db, background_tasks=mock_bg)
    finally:
        db.close()

    # add_task should be scheduled once with our helper and args
    assert mock_bg.add_task.call_count == 1
    call_args = mock_bg.add_task.call_args[0]
    # first arg is the callable helper
    assert call_args[0] is event_module._send_event_update_email_task
    # second arg is the event id
    assert call_args[1] == ev_id
    # third arg is a Session-like object
    assert hasattr(call_args[2], "commit") or hasattr(call_args[2], "execute")
    # fourth arg is settings instance
    assert call_args[3] is settings


def test_background_task_sends_email(client):
    payload = _create_payload("EmailTask Event")
    created = client.post("/events", json=payload).json()
    ev_id = created["id"]

    # Prepare a mock SMTPService instance
    mock_smtp = MagicMock()

    # Patch the classmethod from_settings to return our mock instance
    with patch.object(event_module.SMTPService, "from_settings", return_value=mock_smtp):
        db_task = SessionLocal()
        try:
            event_module._send_event_update_email_task(ev_id, db_task, settings)
        finally:
            # helper should close the db passed in finally, but ensure safety
            try:
                db_task.close()
            except Exception:
                pass

    # send_email should have been called once with the current participants
    assert mock_smtp.send_email.call_count == 1
    called_args, called_kwargs = mock_smtp.send_email.call_args
    # First positional arg is to_emails
    to_emails = called_kwargs.get("to_emails") if "to_emails" in called_kwargs else called_args[0]
    assert set(to_emails) == set(payload["participants"])
    # subject should include Event Update and event name
    subject = called_kwargs.get("subject") if "subject" in called_kwargs else called_args[1]
    assert "Event Update" in subject
    assert payload["name"] in subject
    # body should include location and participants
    body = called_kwargs.get("body") if "body" in called_kwargs else called_args[2]
    assert "Location" in body or "Virtual" in body
    for p in payload["participants"]:
        assert p in body
