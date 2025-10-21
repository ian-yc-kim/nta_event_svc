import re
from pathlib import Path


def _read_api_md() -> str:
    p = Path("API.md")
    assert p.exists(), "API.md must exist in repository root"
    return p.read_text(encoding="utf-8")


def _find_section(content: str, start_token: str, endpoints: list[str]) -> str:
    start_idx = content.find(start_token)
    assert start_idx != -1, f"Section for {start_token} not found"
    next_idxs = [content.find(ep, start_idx + 1) for ep in endpoints if content.find(ep, start_idx + 1) != -1]
    end_idx = min(next_idxs) if next_idxs else len(content)
    return content[start_idx:end_idx]


def test_put_section_documents_async_notifications():
    content = _read_api_md()
    endpoints = [
        "POST /events",
        "GET /events",
        "GET /events/{event_id}",
        "PUT /events/{event_id}",
        "DELETE /events/{event_id}",
    ]

    put_section = _find_section(content, "PUT /events/{event_id}", endpoints)

    # Check the section mentions asynchronous/background notification behavior
    assert re.search(r"asynchronous|background", put_section, re.IGNORECASE), "PUT section must mention asynchronous or background email notifications"
    assert re.search(r"not block|does not block|responds immediately|immediate", put_section, re.IGNORECASE), "PUT section must state the API response is not blocked by email sending"

    # Ensure the trigger fields are explicitly listed
    for field in ["start_time", "end_time", "location", "participants"]:
        assert field in put_section, f"PUT section must explicitly list field '{field}' as a trigger for notifications"
