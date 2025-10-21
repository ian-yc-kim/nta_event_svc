from datetime import datetime
from types import SimpleNamespace
from typing import Any

import pytest
from pydantic import ValidationError

from event_service.schemas.event import (
    EventBase,
    EventCreate,
    EventUpdate,
    EventResponse,
)


def test_event_create_serialization_deserialization():
    payload = {
        "name": "Conference",
        "description": "Annual conf",
        "start_time": "2025-10-01T09:00:00Z",
        "end_time": "2025-10-01T17:00:00Z",
        "location": "Convention Center",
        "participants": ["alice@example.com", "bob@example.com"],
    }

    # model_validate should parse ISO datetimes to datetime objects
    model = EventCreate.model_validate(payload)
    assert isinstance(model, EventCreate)
    assert model.name == "Conference"
    assert isinstance(model.start_time, datetime)
    assert isinstance(model.end_time, datetime)
    assert model.participants == ["alice@example.com", "bob@example.com"]

    dumped = model.model_dump()
    # Ensure serialization retains the fields
    assert dumped["name"] == "Conference"
    assert dumped["participants"] == ["alice@example.com", "bob@example.com"]


def test_event_update_optional_fields_and_validation():
    # empty update should be allowed and produce no fields when excluding None
    upd = EventUpdate()
    assert isinstance(upd, EventUpdate)
    assert upd.model_dump(exclude_none=True) == {}

    # partial update should only include provided fields
    partial = EventUpdate(name="New Name", participants=["x"])
    dumped_partial = partial.model_dump(exclude_none=True)
    assert dumped_partial == {"name": "New Name", "participants": ["x"]}

    # invalid participants type should raise ValidationError
    with pytest.raises(ValidationError):
        EventUpdate.model_validate({"participants": "not-a-list"})


def test_event_response_orm_mode_parses_attributes():
    now = datetime.utcnow()
    # create a simple object that mimics ORM object attributes
    obj = SimpleNamespace(
        id=123,
        name="Meeting",
        description="Team sync",
        start_time=now,
        end_time=now,
        location="Room 1",
        participants=["alice", "bob"],
        created_at=now,
        updated_at=now,
    )

    resp = EventResponse.model_validate(obj)
    assert isinstance(resp, EventResponse)
    assert resp.id == 123
    assert resp.name == "Meeting"
    assert resp.created_at == now
    assert resp.updated_at == now

    dumped = resp.model_dump()
    assert dumped["id"] == 123
    assert dumped["participants"] == ["alice", "bob"]
