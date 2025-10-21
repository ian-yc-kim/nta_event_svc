from __future__ import annotations
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class EventBase(BaseModel):
    """Base schema containing common Event fields."""

    name: str
    description: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    location: Optional[str] = None
    participants: Optional[List[str]] = None


class EventCreate(EventBase):
    """Schema used when creating an Event (POST).

    Inherits validation rules from EventBase.
    """


class EventUpdate(BaseModel):
    """Schema used when updating an Event (PUT/PATCH).

    All fields are optional to allow partial updates.
    """

    name: Optional[str] = None
    description: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    location: Optional[str] = None
    participants: Optional[List[str]] = None


class EventResponse(EventBase):
    """Schema returned in API responses for Event resources.

    Adds id, created_at and updated_at fields. Configured to support
    ORM-style objects via from_attributes so SQLAlchemy models or
    SimpleNamespace-like objects can be validated.
    """

    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    # pydantic v2 ORM support
    model_config = ConfigDict(from_attributes=True)
