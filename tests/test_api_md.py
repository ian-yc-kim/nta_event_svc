import re
from pathlib import Path


def _read_api_md() -> str:
    p = Path("API.md")
    assert p.exists(), "API.md must exist in repository root"
    return p.read_text(encoding="utf-8")


def _find_section(content: str, start_token: str, endpoints: list[str]) -> str:
    start_idx = content.find(start_token)
    assert start_idx != -1, f"Section for {start_token} not found"
    # find next endpoint occurrence after start_idx
    next_idxs = [content.find(ep, start_idx + 1) for ep in endpoints if content.find(ep, start_idx + 1) != -1]
    end_idx = min(next_idxs) if next_idxs else len(content)
    return content[start_idx:end_idx]


def test_api_md_contains_endpoints_and_sections():
    content = _read_api_md()
    endpoints = [
        "POST /events",
        "GET /events",
        "GET /events/{event_id}",
        "PUT /events/{event_id}",
        "DELETE /events/{event_id}",
    ]

    # Basic presence checks
    for ep in endpoints:
        assert ep in content, f"Expected endpoint {ep} documented"

    # For POST and PUT, ensure request body and responses are present in their sections
    post_section = _find_section(content, "POST /events", endpoints)
    assert re.search(r"Request body|Request:\n|Request", post_section, re.IGNORECASE), "POST section must document Request body"
    assert re.search(r"Responses|Response", post_section, re.IGNORECASE), "POST section must document Responses"
    assert re.search(r"Example request|Example", post_section, re.IGNORECASE), "POST section must include an example"

    put_section = _find_section(content, "PUT /events/{event_id}", endpoints)
    assert re.search(r"Request body|Request:\n|Request", put_section, re.IGNORECASE), "PUT section must document Request body"
    assert re.search(r"Responses|Response", put_section, re.IGNORECASE), "PUT section must document Responses"
    assert re.search(r"Example request|Example", put_section, re.IGNORECASE), "PUT section must include an example"

    # For GET (list) ensure Responses documented and example exists
    get_list_section = _find_section(content, "GET /events\n", endpoints)
    assert re.search(r"Responses|Response", get_list_section, re.IGNORECASE), "GET /events section must document Responses"
    assert re.search(r"Example request|Example", get_list_section, re.IGNORECASE), "GET /events section must include an example"

    # For single GET ensure Responses documented
    get_one_section = _find_section(content, "GET /events/{event_id}", endpoints)
    assert re.search(r"Responses|Response", get_one_section, re.IGNORECASE), "GET /events/{event_id} must document Responses"

    # For DELETE ensure Responses documented
    delete_section = _find_section(content, "DELETE /events/{event_id}", endpoints)
    assert re.search(r"Responses|Response", delete_section, re.IGNORECASE), "DELETE section must document Responses"
