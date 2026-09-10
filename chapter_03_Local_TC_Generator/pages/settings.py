"""Screen 2 — Settings.

Credentials and provider choice are persisted to the `.env` file next to the
project root. Saved secrets are never echoed back into the form: leaving a
secret field blank keeps the stored value, and the explicit checkbox clears it.
"""

from __future__ import annotations

import streamlit as st

import config_store
import jira_client
import llm_client

st.set_page_config(page_title="Settings · Jira Test Case Generator", page_icon="⚙️", layout="centered")

stored = config_store.load_settings()

SECRET_PLACEHOLDER = "•••••••• saved — leave blank to keep"

st.title("Settings")
st.caption("Saved to `.env` in the project folder. Never committed to version control.")

if st.session_state.pop("settings_saved", False):
    st.success("Settings saved.")

with st.form("settings_form"):
    st.subheader("Jira")
    jira_url = st.text_input("Jira URL", value=stored["JIRA_URL"], placeholder="https://your-site.atlassian.net")
    jira_email = st.text_input("Jira email", value=stored["JIRA_EMAIL"], placeholder="you@company.com")
    jira_token = st.text_input(
        "Jira API token",
        value="",
        type="password",
        placeholder=SECRET_PLACEHOLDER if stored["JIRA_API_TOKEN"] else "Paste your API token",
        help="Create one at id.atlassian.com/manage-profile/security/api-tokens",
    )
    ac_field = st.text_input(
        "Acceptance criteria custom field (optional)",
        value=stored["JIRA_AC_FIELD"],
        placeholder="customfield_10016",
        help="Leave blank to read acceptance criteria from the description instead.",
    )

    st.divider()
    st.subheader("LLM backend")
    provider = st.selectbox(
        "Provider",
        options=["ollama", "groq"],
        index=0 if stored["LLM_PROVIDER"] != "groq" else 1,
        help="Ollama is the default and always tried first. Choose Groq to opt out, or to fall back automatically.",
    )
    ollama_base_url = st.text_input("Ollama base URL", value=stored["OLLAMA_BASE_URL"])
    ollama_model = st.text_input(
        "Ollama model",
        value=stored["OLLAMA_MODEL"],
        help="Must already be pulled locally. The app never downloads models.",
    )

    groq_key = st.text_input(
        "Groq API key",
        value="",
        type="password",
        placeholder=SECRET_PLACEHOLDER if stored["GROQ_API_KEY"] else "gsk_…",
        help="Only used when Groq is selected, or when Ollama is unavailable.",
    )
    groq_model = st.text_input("Groq model", value=stored["GROQ_MODEL"])

    st.divider()
    clear_secrets = st.checkbox("Clear saved secrets (Jira token and Groq key)")

    col_save, col_test = st.columns(2)
    save_clicked = col_save.form_submit_button("Save settings", use_container_width=True, type="primary")
    test_clicked = col_test.form_submit_button("Test Jira connection", use_container_width=True)

submitted = {
    "JIRA_URL": jira_url,
    "JIRA_EMAIL": jira_email,
    "JIRA_AC_FIELD": ac_field,
    "LLM_PROVIDER": provider,
    "OLLAMA_BASE_URL": ollama_base_url,
    "OLLAMA_MODEL": ollama_model,
    "GROQ_MODEL": groq_model,
}

if clear_secrets:
    submitted["JIRA_API_TOKEN"] = ""
    submitted["GROQ_API_KEY"] = ""
else:
    if jira_token.strip():
        submitted["JIRA_API_TOKEN"] = jira_token.strip()
    if groq_key.strip():
        submitted["GROQ_API_KEY"] = groq_key.strip()

if save_clicked:
    config_store.save_settings(submitted)
    st.session_state["settings_saved"] = True
    st.rerun()

st.divider()
st.subheader("Connection status")

test_settings = dict(stored)
test_settings.update(submitted)
if clear_secrets:
    test_settings["JIRA_API_TOKEN"] = ""
    test_settings["GROQ_API_KEY"] = ""

if test_clicked:
    with st.spinner("Contacting Jira…"):
        ok, message = jira_client.ping(test_settings)
    if ok:
        st.success(message)
    else:
        st.error(message)

ready, reason = llm_client.ollama_status(test_settings)
if ready:
    st.success(reason)
elif provider == "groq":
    st.info("Groq is selected as the provider.")
else:
    st.warning(reason)

if config_store.is_configured(test_settings):
    st.caption(
        f"Saved Jira token: {config_store.mask(test_settings['JIRA_API_TOKEN'])} · "
        f"Saved Groq key: {config_store.mask(test_settings['GROQ_API_KEY']) or 'none'}"
    )
else:
    st.caption("Jira credentials incomplete — live ticket fetching is disabled until all three are saved.")

st.page_link("app.py", label="Back to chat", icon="💬")
