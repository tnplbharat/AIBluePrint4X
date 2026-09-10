"""Jira Cloud REST v3 client.

Only two endpoints are used: the issue endpoint (to fetch a ticket) and
`/myself` (to validate credentials from the settings screen). Ticket keys that
start with `DEMO` are served from `templates/sample_ticket.json` so the chat flow
can be exercised without any live Jira access.
"""

from __future__ import annotations

import json
from pathlib import Path

import requests

import config_store

SAMPLE_TICKET_PATH = Path(__file__).resolve().parent / "templates" / "sample_ticket.json"

REQUEST_TIMEOUT = 20
FIELDS = "summary,description,status,issuetype"

_LABELS = {
    400: "Jira rejected the request (400). Check the issue key format.",
    401: "Jira authentication failed (401). Verify the email and API token in Settings.",
    403: "Your Jira account is not allowed to view this issue (403).",
    404: "Jira issue not found (404). Check the key, or your site URL in Settings.",
}


class JiraError(Exception):
    """Raised for any Jira failure, carrying a message safe to show in the UI."""


def _base_url(settings: dict) -> str:
    url = (settings.get("JIRA_URL") or "").strip().rstrip("/")
    if not url:
        raise JiraError(
            "Jira URL is not set. Open Settings and save your Jira site URL, "
            "or send `create test cases for DEMO-1` to try the app offline."
        )
    return url


def _explain(response: requests.Response) -> str:
    if response.status_code in _LABELS:
        return _LABELS[response.status_code]
    detail = ""
    try:
        payload = response.json()
        messages = payload.get("errorMessages") or []
        errors = payload.get("errors") or {}
        detail = " ".join(list(messages) + [f"{k}: {v}" for k, v in errors.items()])
    except ValueError:
        detail = (response.text or "").strip()[:200]
    suffix = f" Details: {detail}" if detail else ""
    return f"Jira returned HTTP {response.status_code}.{suffix}"


def adf_to_text(node) -> str:
    """Flatten an Atlassian Document Format tree into readable plain text."""
    if node is None:
        return ""
    if isinstance(node, str):
        return node
    if isinstance(node, list):
        return "\n".join(part for part in (adf_to_text(item) for item in node) if part)

    if not isinstance(node, dict):
        return ""

    node_type = node.get("type")

    if node_type == "text":
        return node.get("text", "")

    if node_type == "hardBreak":
        return "\n"

    if node_type in {"media", "mediaInline", "mediaSingle", "mediaGroup"}:
        return "[attachment]"

    if node_type == "mention":
        return node.get("attrs", {}).get("text", "")

    if node_type == "emoji":
        return node.get("attrs", {}).get("text", "")

    if node_type == "inlineCard":
        return node.get("attrs", {}).get("url", "")

    if node_type == "codeBlock":
        return f"\n```\n{adf_to_text(node.get('content'))}\n```\n"

    if node_type == "blockquote":
        return "\n".join(f"> {line}" for line in adf_to_text(node.get("content")).splitlines())

    if node_type == "rule":
        return "\n---\n"

    if node_type == "heading":
        level = node.get("attrs", {}).get("level", 1)
        return f"\n{'#' * int(level)} {adf_to_text(node.get('content'))}\n"

    if node_type == "bulletList":
        items = [adf_to_text(item) for item in node.get("content") or []]
        return "\n".join(f"- {item}" for item in items if item)

    if node_type == "orderedList":
        items = [adf_to_text(item) for item in node.get("content") or []]
        return "\n".join(f"{i}. {item}" for i, item in enumerate(items, 1) if item)

    if node_type == "listItem":
        parts = [adf_to_text(child) for child in node.get("content") or []]
        return " ".join(part.strip() for part in parts if part and part.strip())

    if node_type in {"table", "tableRow", "tableCell", "tableHeader"}:
        if node_type in {"tableCell", "tableHeader"}:
            return adf_to_text(node.get("content")).replace("\n", " ").strip()
        return "\n".join(
            part for part in (adf_to_text(child) for child in node.get("content") or []) if part
        )

    if node_type == "paragraph":
        return adf_to_text(node.get("content"))

    if node_type == "doc":
        blocks = [adf_to_text(child) for child in node.get("content") or []]
        return "\n\n".join(block.strip() for block in blocks if block and block.strip())

    return adf_to_text(node.get("content"))


def _split_acceptance_criteria(text: str) -> tuple[str, str]:
    """Split an 'Acceptance Criteria' section out of the description text."""
    lines = text.splitlines()
    start = None

    for index, line in enumerate(lines):
        normalised = line.strip().lower().lstrip("#*").strip()
        if normalised.startswith("acceptance criteria") or normalised.startswith("acceptance criterion"):
            start = index
            break

    if start is None:
        return text.strip(), ""

    _, _, after_colon = lines[start].partition(":")
    if after_colon.strip():
        criteria_lines = [after_colon, *lines[start + 1:]]
    else:
        criteria_lines = lines[start + 1:]

    description = "\n".join(lines[:start]).strip()
    criteria = "\n".join(criteria_lines).strip()
    return description, criteria


def _load_sample(key: str) -> dict:
    if not SAMPLE_TICKET_PATH.exists():
        raise JiraError(f"Demo ticket file is missing: {SAMPLE_TICKET_PATH}")

    ticket = json.loads(SAMPLE_TICKET_PATH.read_text(encoding="utf-8"))
    ticket["key"] = key.upper()
    ticket["source"] = "demo"

    description = ticket.get("description") or ""
    criteria = (ticket.get("acceptance_criteria") or "").strip()
    if not criteria:
        description, criteria = _split_acceptance_criteria(description)

    ticket["description"] = description
    ticket["acceptance_criteria"] = criteria
    ticket.setdefault("summary", "")
    ticket.setdefault("status", "")
    ticket.setdefault("issue_type", "")
    return ticket


def fetch_ticket(key: str, settings: dict) -> dict:
    """Fetch one Jira issue as a plain dict.

    Returns keys: key, summary, description, acceptance_criteria, status,
    issue_type, source.
    """
    key = (key or "").strip().upper()
    if not key:
        raise JiraError("No Jira issue key was found in your message.")

    if key.startswith("DEMO"):
        return _load_sample(key)

    if not config_store.is_configured(settings):
        raise JiraError(
            f"Jira credentials are not set, so {key} cannot be fetched. "
            "Open Settings and save your Jira URL, email and API token, "
            "or send `create test cases for DEMO-1` to try the app offline."
        )

    url = f"{_base_url(settings)}/rest/api/3/issue/{key}"

    try:
        response = requests.get(
            url,
            params={"fields": FIELDS},
            auth=(settings["JIRA_EMAIL"], settings["JIRA_API_TOKEN"]),
            headers={"Accept": "application/json"},
            timeout=REQUEST_TIMEOUT,
        )
    except requests.RequestException as exc:
        raise JiraError(f"Could not reach Jira at {_base_url(settings)}: {exc}") from exc

    if response.status_code != 200:
        raise JiraError(_explain(response))

    try:
        payload = response.json()
    except ValueError as exc:
        raise JiraError("Jira returned a response that was not valid JSON.") from exc

    fields = payload.get("fields") or {}
    description_text = adf_to_text(fields.get("description"))
    description, criteria = _split_acceptance_criteria(description_text)

    ac_field = (settings.get("JIRA_AC_FIELD") or "").strip()
    if ac_field:
        custom = adf_to_text(fields.get(ac_field))
        if custom.strip():
            criteria = custom.strip()

    status = (fields.get("status") or {}).get("name", "")
    issue_type = (fields.get("issuetype") or {}).get("name", "")

    return {
        "key": payload.get("key", key),
        "summary": (fields.get("summary") or "").strip(),
        "description": description,
        "acceptance_criteria": criteria,
        "status": status,
        "issue_type": issue_type,
        "source": "jira",
    }


def ping(settings: dict) -> tuple[bool, str]:
    """Validate stored credentials against `/myself`. Returns (ok, message)."""
    if not config_store.is_configured(settings):
        return False, "Jira URL, email and API token must all be filled in."

    url = f"{_base_url(settings)}/rest/api/3/myself"

    try:
        response = requests.get(
            url,
            auth=(settings["JIRA_EMAIL"], settings["JIRA_API_TOKEN"]),
            headers={"Accept": "application/json"},
            timeout=REQUEST_TIMEOUT,
        )
    except requests.RequestException as exc:
        return False, f"Could not reach Jira at {_base_url(settings)}: {exc}"

    if response.status_code != 200:
        return False, _explain(response)

    try:
        account = response.json()
    except ValueError:
        return True, "Connected to Jira."

    name = account.get("displayName") or account.get("emailAddress") or "authenticated user"
    return True, f"Connected to Jira as {name}."
