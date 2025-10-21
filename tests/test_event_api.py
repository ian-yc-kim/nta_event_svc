from typing import Any, Dict


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
