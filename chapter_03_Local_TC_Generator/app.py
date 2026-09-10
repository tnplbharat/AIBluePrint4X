"""Screen 1 — Chat.

Type a request such as "create test cases for QA-102". The app parses the Jira
issue key, fetches the ticket, merges it into the local template, asks the
selected LLM backend, and renders the generated test cases in the chat pane.
"""

from __future__ import annotations

import re
from pathlib import Path

import streamlit as st

import config_store
import jira_client
import llm_client

TEMPLATE_PATH = Path(__file__).resolve().parent / "templates" / "TestCaseGen.md"
DEFAULT_TEST_CASE_COUNT = 8

ISSUE_KEY_PATTERN = re.compile(r"\b([A-Za-z][A-Za-z0-9]*-\d+)\b")
COUNT_PATTERN = re.compile(r"\b(\d{1,3})\s+(?:test\s*cases|tests|cases)\b", re.IGNORECASE)

st.set_page_config(page_title="Jira Test Case Generator", page_icon="🧪", layout="wide")

settings = config_store.load_settings()
st.session_state.setdefault("messages", [])


def read_template() -> str:
    if not TEMPLATE_PATH.exists():
        raise FileNotFoundError(f"Template not found: {TEMPLATE_PATH}")
    return TEMPLATE_PATH.read_text(encoding="utf-8")


def parse_request(message: str) -> tuple[str | None, int]:
    key_match = ISSUE_KEY_PATTERN.search(message)
    key = key_match.group(1).upper() if key_match else None

    count_match = COUNT_PATTERN.search(message)
    count = int(count_match.group(1)) if count_match else DEFAULT_TEST_CASE_COUNT
    count = max(1, min(count, 50))

    return key, count


def render_sidebar() -> None:
    with st.sidebar:
        st.subheader("Status")

        ready, reason = llm_client.ollama_status(settings)
        provider = (settings.get("LLM_PROVIDER") or "ollama").lower()

        if provider == "groq":
            st.info("Provider: Groq (selected in Settings)")
        elif ready:
            st.success(f"Ollama ready — {settings.get('OLLAMA_MODEL')}")
        elif (settings.get("GROQ_API_KEY") or "").strip():
            st.warning("Ollama unavailable — Groq fallback armed")
            st.caption(reason)
        else:
            st.error("No LLM backend available")
            st.caption(reason)

        if config_store.is_configured(settings):
            st.success("Jira credentials saved")
            st.caption(settings.get("JIRA_URL", ""))
        else:
            st.warning("Jira credentials not set")
            st.caption("You can still try `DEMO-1` offline.")

        st.divider()
        st.page_link("pages/settings.py", label="Open Settings", icon="⚙️")

        if st.button("Clear chat", use_container_width=True):
            st.session_state.messages = []
            st.rerun()

        st.divider()
        st.caption(
            "Try:\n\n"
            "- `create test cases for QA-102`\n"
            "- `give me 12 test cases for DEMO-1`"
        )


def render_assistant_message(message: dict, index: int) -> None:
    st.markdown(message["content"])

    if message.get("error"):
        return

    meta_bits = [f"Provider: {message.get('provider', 'unknown')}"]
    if message.get("ticket_key"):
        meta_bits.append(f"Ticket: {message['ticket_key']}")
    if message.get("source"):
        meta_bits.append(f"Source: {message['source']}")
    st.caption(" · ".join(meta_bits))

    if message.get("note"):
        st.warning(message["note"])

    ticket = message.get("ticket")
    if ticket:
        with st.expander("Fetched ticket"):
            st.markdown(f"**{ticket.get('key')} — {ticket.get('summary')}**")
            st.caption(f"{ticket.get('issue_type')} · {ticket.get('status')}")
            st.markdown(ticket.get("description") or "_No description_")
            if ticket.get("acceptance_criteria"):
                st.markdown("**Acceptance criteria**")
                st.markdown(ticket["acceptance_criteria"])

    st.download_button(
        "Download as Markdown",
        data=message["content"],
        file_name=f"{message.get('ticket_key', 'test-cases')}_test_cases.md",
        mime="text/markdown",
        key=f"download_{index}",
    )


def answer(message: str) -> dict:
    key, count = parse_request(message)

    if not key:
        return {
            "role": "assistant",
            "error": True,
            "content": (
                "I could not find a Jira issue key in that message.\n\n"
                "Try something like `create test cases for QA-102`, "
                "or `create test cases for DEMO-1` to run offline."
            ),
        }

    with st.spinner(f"Fetching {key} from Jira…"):
        try:
            ticket = jira_client.fetch_ticket(key, settings)
        except jira_client.JiraError as exc:
            return {"role": "assistant", "error": True, "content": f"**Jira error**\n\n{exc}"}

    try:
        template_text = read_template()
    except FileNotFoundError as exc:
        return {"role": "assistant", "error": True, "content": f"**Template error**\n\n{exc}"}

    prompt = llm_client.build_test_case_prompt(template_text, ticket, count)

    with st.spinner(f"Generating {count} test cases with {config_store.provider_label(settings)}…"):
        try:
            content, provider, note = llm_client.generate(prompt, settings)
        except llm_client.LLMError as exc:
            return {
                "role": "assistant",
                "error": True,
                "content": f"**LLM error**\n\n{exc}",
                "ticket": ticket,
                "ticket_key": ticket.get("key"),
                "source": ticket.get("source"),
            }

    return {
        "role": "assistant",
        "content": content,
        "provider": provider,
        "note": note,
        "ticket": ticket,
        "ticket_key": ticket.get("key"),
        "source": ticket.get("source"),
    }


render_sidebar()

st.title("Jira Test Case Generator")
st.caption("Ask for test cases using a Jira issue key. Ollama runs locally by default.")

if not config_store.is_configured(settings):
    st.warning("Jira credentials are not set. Open **Settings**, or try `create test cases for DEMO-1`.")

for index, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        if message["role"] == "assistant":
            render_assistant_message(message, index)
        else:
            st.markdown(message["content"])

user_input = st.chat_input("e.g. create test cases for QA-102")

if user_input:
    with st.chat_message("user"):
        st.markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})

    with st.chat_message("assistant"):
        reply = answer(user_input)
        render_assistant_message(reply, len(st.session_state.messages))

    st.session_state.messages.append(reply)
