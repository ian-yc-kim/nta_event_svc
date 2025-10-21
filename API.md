# Events API

## Introduction

This document describes the Event CRUD HTTP API for the event-service.

Base URL (local development): http://localhost:8000

No authentication is required for the documented endpoints.

## Schemas

All timestamps use ISO 8601 format (e.g. 2025-01-02T15:04:05Z).

EventCreate (request body for POST):
- name: string (required)
- description: string (optional)
- start_time: datetime (ISO 8601, optional)
- end_time: datetime (ISO 8601, optional)
- location: string (optional)
- participants: array[string] (optional) -- list of participant emails or identifiers

EventUpdate (request body for PUT):
- All fields from EventCreate, but all are optional to allow partial updates.

EventResponse (successful response model):
- id: integer
- name: string
- description: string|null
- start_time: datetime|null
- end_time: datetime|null
- location: string|null
- participants: array[string]|null
- created_at: datetime|null
- updated_at: datetime|null

Error format (standard FastAPI error):
{
  "detail": "..."
}

## Endpoints

### POST /events

Description
Create a new event.

Request body
JSON matching EventCreate.

Responses
- 201 Created: returns EventResponse JSON for the created event
- 422 Unprocessable Entity: validation errors (FastAPI default)
- 500 Internal Server Error: {"detail": "Failed to create event"}

Example request (curl)
```
curl -X POST http://localhost:8000/events \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Team Meeting",
    "description": "Monthly sync",
    "start_time": "2025-10-01T10:00:00Z",
    "end_time": "2025-10-01T11:00:00Z",
    "location": "Conference Room",
    "participants": ["alice@example.com", "bob@example.com"]
  }'
```

Example response (201)
```
{
  "id": 1,
  "name": "Team Meeting",
  "description": "Monthly sync",
  "start_time": "2025-10-01T10:00:00Z",
  "end_time": "2025-10-01T11:00:00Z",
  "location": "Conference Room",
  "participants": ["alice@example.com", "bob@example.com"],
  "created_at": "2025-09-01T12:00:00Z",
  "updated_at": "2025-09-01T12:00:00Z"
}
```

---

### GET /events

Description
List all events.

Request
No request body.

Responses
- 200 OK: returns array of EventResponse objects
- 500 Internal Server Error: {"detail": "Failed to list events"}

Example request (curl)
```
curl http://localhost:8000/events
```

Example response (200)
```
[
  {
    "id": 1,
    "name": "Team Meeting",
    "description": "Monthly sync",
    "start_time": "2025-10-01T10:00:00Z",
    "end_time": "2025-10-01T11:00:00Z",
    "location": "Conference Room",
    "participants": ["alice@example.com", "bob@example.com"],
    "created_at": "2025-09-01T12:00:00Z",
    "updated_at": "2025-09-01T12:00:00Z"
  }
]
```

---

### GET /events/{event_id}

Description
Retrieve details for a single event by ID.

Path parameters
- event_id: integer (required)

Responses
- 200 OK: returns EventResponse
- 404 Not Found: {"detail": "Event not found"}
- 500 Internal Server Error: {"detail": "Failed to retrieve event"}

Example request (curl)
```
curl http://localhost:8000/events/1
```

Example responses
200 OK
```
{
  "id": 1,
  "name": "Team Meeting",
  "description": "Monthly sync",
  "start_time": "2025-10-01T10:00:00Z",
  "end_time": "2025-10-01T11:00:00Z",
  "location": "Conference Room",
  "participants": ["alice@example.com", "bob@example.com"],
  "created_at": "2025-09-01T12:00:00Z",
  "updated_at": "2025-09-01T12:00:00Z"
}
```

404 Not Found
```
{ "detail": "Event not found" }
```

---

### PUT /events/{event_id}

Description
Update an existing event. Partial updates supported; fields omitted remain unchanged.

Path parameters
- event_id: integer (required)

Request body
JSON matching EventUpdate (all fields optional).

Responses
- 200 OK: returns updated EventResponse
- 404 Not Found: {"detail": "Event not found"}
- 422 Unprocessable Entity: validation errors
- 500 Internal Server Error: {"detail": "Failed to update event"}

Example request (curl)
```
curl -X PUT http://localhost:8000/events/1 \
  -H "Content-Type: application/json" \
  -d '{ "name": "Updated Meeting", "participants": ["x@example.com"] }'
```

Example response (200)
```
{
  "id": 1,
  "name": "Updated Meeting",
  "description": "Monthly sync",
  "start_time": "2025-10-01T10:00:00Z",
  "end_time": "2025-10-01T11:00:00Z",
  "location": "Conference Room",
  "participants": ["x@example.com"],
  "created_at": "2025-09-01T12:00:00Z",
  "updated_at": "2025-09-02T09:00:00Z"
}
```

---

### DELETE /events/{event_id}

Description
Delete an event by ID.

Path parameters
- event_id: integer (required)

Responses
- 204 No Content: deletion successful
- 404 Not Found: {"detail": "Event not found"}
- 500 Internal Server Error: {"detail": "Failed to delete event"}

Example request (curl)
```
curl -X DELETE http://localhost:8000/events/1
```

Example response (204)
No body returned.

## Error handling

The API uses the standard FastAPI error format with a detail field. Typical errors include:
- 422 validation errors when request body fields are invalid
- 404 when a requested event_id does not exist
- 500 for unexpected server errors

## Example payloads

Minimal EventCreate
```
{ "name": "Quick Event" }
```

Full EventCreate
```
{
  "name": "Conference",
  "description": "Annual conference",
  "start_time": "2025-11-10T09:00:00Z",
  "end_time": "2025-11-10T17:00:00Z",
  "location": "Convention Center",
  "participants": ["john@example.com", "jane@example.com"]
}
```

## Testing notes

Unit and integration tests should assert that the API endpoints behave as documented. This repository includes pytest tests that exercise the event endpoints against an in-memory sqlite instance during test runs.
