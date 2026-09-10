# Chapter 03 — Local Jira → Test Case Generator

A two-screen Streamlit app that turns a Jira ticket into a draft test case table, using a
local Ollama model by default and Groq only as an explicit choice or fallback.

- **Screen 1 — Chat** (`app.py`): type `create test cases for QA-102`.
- **Screen 2 — Settings** (`pages/settings.py`): Jira credentials and LLM provider choice.

## Requirements

- Python 3.10+
- Ollama running locally at `http://localhost:11434` with the `gemma3:1b` model already pulled
  (`ollama list` should show it — the app never downloads models)

## Setup

```
pip install -r requirements.txt
```

Copy `.env.example` to `.env` and fill in the values, or enter them on the Settings screen:

| Key | Purpose |
|---|---|
| `JIRA_URL` | `https://your-site.atlassian.net` |
| `JIRA_EMAIL` | Atlassian account email |
| `JIRA_API_TOKEN` | Token from id.atlassian.com/manage-profile/security/api-tokens |
| `JIRA_AC_FIELD` | Optional custom field holding acceptance criteria |
| `LLM_PROVIDER` | `ollama` (default) or `groq` |
| `OLLAMA_BASE_URL` | Default `http://localhost:11434` |
| `OLLAMA_MODEL` | Default `gemma3:1b` |
| `GROQ_API_KEY` | Only needed for the Groq path |
| `GROQ_MODEL` | Default `openai/gpt-oss-120b` |

`.env` is gitignored. No credential is ever hardcoded in source.

## Run

```
streamlit run app.py
```

Then try `create test cases for DEMO-1` — that key is served from
`templates/sample_ticket.json`, so the whole flow works before any Jira credentials exist.

## How a request flows

1. The issue key (`[A-Z]+-\d+`) and an optional test case count are parsed from the message.
2. `jira_client.fetch_ticket` calls Jira Cloud REST v3 (`/rest/api/3/issue/{key}`) with Basic auth
   and flattens the Atlassian Document Format description into plain text.
3. `llm_client.build_test_case_prompt` merges the ticket into `templates/TestCaseGen.md`.
4. `llm_client.generate` calls **Ollama first**. Groq is contacted only if the provider was set to
   `groq` in Settings, or if Ollama is unreachable and a Groq key is saved.
5. The reply is rendered in the chat pane with the provider used, the ticket it came from, and a
   Markdown download button.

## Limitations

- Output quality from `gemma3:1b` on long tickets is limited; switch to Groq in Settings for better tables.
- Jira Cloud only. Jira Server/Data Center would need REST v2 with a bearer PAT in `jira_client.py`.
- Acceptance criteria are detected heuristically from the description unless `JIRA_AC_FIELD` is set.
- `.env` stores secrets in plain text on local disk — fine for an internal tool, not for a shared machine.
