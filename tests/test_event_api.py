from typing import Any, Dict
from unittest.mock import patch, MagicMock
import event_service.api.event as event_module
from datetime import datetime, timezone


def _create_payload(name: str = "Test Event") -> Dict[str, Any]:
    return {
        "name": name,
        "description": "A sample event",
        "location": "Virtual",
        "participants": ["alice@example.com", "bob@example.com"],
    }


def test_create_event_201(client):
    payload = _create_payload()
    res = client.post("/events", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert "id" in data
    assert data["name"] == payload["name"]


def test_list_events_200(client):
    payload = _create_payload("List Event")
    client.post("/events", json=payload)
    res = client.get("/events")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert any(item.get("name") == payload["name"] for item in data)


def test_get_event_by_id_200(client):
    payload = _create_payload("GetByID Event")
    create = client.post("/events", json=payload).json()
    ev_id = create["id"]
    res = client.get(f"/events/{ev_id}")
    assert res.status_code == 200
    data = res.json()
    assert data["id"] == ev_id
    assert data["name"] == payload["name"]


def test_get_event_404_for_invalid_id(client):
    res = client.get("/events/999999")
    assert res.status_code == 404


def test_update_event_200(client):
    payload = _create_payload("Update Event")
    created = client.post("/events", json=payload).json()
    ev_id = created["id"]

    update_payload = {"name": "Updated Name", "participants": ["x@example.com"]}
    res = client.put(f"/events/{ev_id}", json=update_payload)
    assert res.status_code == 200
    data = res.json()
    assert data["id"] == ev_id
    assert data["name"] == "Updated Name"
    assert data["participants"] == ["x@example.com"]


def test_update_event_404_for_invalid_id(client):
    res = client.put("/events/999999", json={"name": "nope"})
    assert res.status_code == 404


def test_delete_event_204(client):
    payload = _create_payload("Delete Event")
    created = client.post("/events", json=payload).json()
    ev_id = created["id"]
    res = client.delete(f"/events/{ev_id}")
    assert res.status_code == 204

    # subsequent get should be 404
    res2 = client.get(f"/events/{ev_id}")
    assert res2.status_code == 404


def test_delete_event_404_for_invalid_id(client):
    res = client.delete("/events/999999")
    assert res.status_code == 404


# New tests validating asynchronous email notification behavior

def test_put_update_name_and_description_only_no_email(client):
    payload = _create_payload()
    created = client.post("/events", json=payload).json()
    ev_id = created["id"]

    mock_smtp = MagicMock()
    # Ensure from_settings returns our mock
    with patch.object(event_module.SMTPService, "from_settings", return_value=mock_smtp):
        res = client.put(f"/events/{ev_id}", json={"name": "New Name", "description": "New Desc"})
        assert res.status_code == 200
        # Background task should not be scheduled, so no send_email call
        assert mock_smtp.send_email.call_count == 0


def test_put_update_location_triggers_email(client):
    payload = _create_payload("Location Notify")
    created = client.post("/events", json=payload).json()
    ev_id = created["id"]

    mock_smtp = MagicMock()
    with patch.object(event_module.SMTPService, "from_settings", return_value=mock_smtp):
        res = client.put(f"/events/{ev_id}", json={"location": "New Venue"})
        assert res.status_code == 200
        # BackgroundTasks run after response in TestClient; verify send_email called
        assert mock_smtp.send_email.call_count == 1

        # Inspect call args for recipients and body
        called_args, called_kwargs = mock_smtp.send_email.call_args
        to_emails = called_kwargs.get("to_emails") if "to_emails" in called_kwargs else called_args[0]
        assert set(to_emails) == set(payload["participants"])
        body = called_kwargs.get("body") if "body" in called_kwargs else called_args[2]
        assert "New Venue" in body or "Location" in body
        assert payload["name"] in (called_kwargs.get("subject") if "subject" in called_kwargs else called_args[1])


def test_put_update_start_time_triggers_email(client):
    payload = _create_payload("StartTime Notify")
    created = client.post("/events", json=payload).json()
    ev_id = created["id"]

    # Use an ISO 8601 string for start_time
    iso_time = datetime.now(timezone.utc).replace(microsecond=0).isoformat()

    mock_smtp = MagicMock()
    with patch.object(event_module.SMTPService, "from_settings", return_value=mock_smtp):
        res = client.put(f"/events/{ev_id}", json={"start_time": iso_time})
        assert res.status_code == 200
        assert mock_smtp.send_email.call_count == 1

        called_args, called_kwargs = mock_smtp.send_email.call_args
        body = called_kwargs.get("body") if "body" in called_kwargs else called_args[2]
        # Body should mention start time marker or include the ISO string
        assert "Start time" in body or iso_time.split("+")[0] in body or iso_time in body


def test_put_update_end_time_triggers_email(client):
    payload = _create_payload("EndTime Notify")
    created = client.post("/events", json=payload).json()
    ev_id = created["id"]

    iso_time = datetime.now(timezone.utc).replace(microsecond=0).isoformat()

    mock_smtp = MagicMock()
    with patch.object(event_module.SMTPService, "from_settings", return_value=mock_smtp):
        res = client.put(f"/events/{ev_id}", json={"end_time": iso_time})
        assert res.status_code == 200
        assert mock_smtp.send_email.call_count == 1

        called_args, called_kwargs = mock_smtp.send_email.call_args
        body = called_kwargs.get("body") if "body" in called_kwargs else called_args[2]
        assert "End time" in body or iso_time in body


def test_put_update_participants_triggers_email_to_new_list(client):
    payload = _create_payload("Participants Notify")
    created = client.post("/events", json=payload).json()
    ev_id = created["id"]

    new_participants = ["charlie@example.com", "dana@example.com"]

    mock_smtp = MagicMock()
    with patch.object(event_module.SMTPService, "from_settings", return_value=mock_smtp):
        res = client.put(f"/events/{ev_id}", json={"participants": new_participants})
        assert res.status_code == 200
        assert mock_smtp.send_email.call_count == 1

        called_args, called_kwargs = mock_smtp.send_email.call_args
        to_emails = called_kwargs.get("to_emails") if "to_emails" in called_kwargs else called_args[0]
        assert set(to_emails) == set(new_participants)


def test_put_update_location_with_no_participants_sends_no_email(client):
    payload = _create_payload("NoParticipants")
    # set participants explicitly to empty list
    payload["participants"] = []
    created = client.post("/events", json=payload).json()
    ev_id = created["id"]

    mock_smtp = MagicMock()
    with patch.object(event_module.SMTPService, "from_settings", return_value=mock_smtp):
        res = client.put(f"/events/{ev_id}", json={"location": "Nowhere"})
        assert res.status_code == 200
        # No participants should result in no email sent
        assert mock_smtp.send_email.call_count == 0
