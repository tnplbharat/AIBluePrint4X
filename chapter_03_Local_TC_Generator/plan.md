# Plan — Chapter 03: Local Jira → Test Case Generator (RICE-POT)

## What I understand from the prompt

`chapter_03_Local_TC_Generator/src/prompt.md` is a RICE-POT spec with a **"plan first, then build one module at a time"** gate.

| Component | What it demands |
|---|---|
| **R**ole | Senior Python full-stack + AI app architect (Streamlit, Jira REST, Ollama/Groq) |
| **I**nstructions | Two screens: **Chat** (ChatGPT-style) and **Settings** (persisted config). Jira key in a chat message → fetch ticket → merge into local template → LLM → render in chat pane |
| **C**ontext | Internal QA productivity tool. No SaaS hardening, no premature abstraction |
| **E**xample | `create test cases for QA-102` → fetch → merge into `templates/` → render as ChatGPT-like structured output |
| **P**arameters | Default backend **Ollama @ `http://localhost:11434`, model `gemma3:1b`** (already pulled — never re-pull). Groq only on explicit opt-out or Ollama failure. Zero hardcoded credentials |
| **O**utput | Exactly: `app.py`, `pages/settings.py`, `config_store.py`, `jira_client.py`, `llm_client.py`, `templates/`, `requirements.txt` |
| **T**one | Minimal deps, working code, each module reviewable on its own |

**Decisions confirmed:** app lives at chapter 03 **root**; `.env` is the single source of truth for credentials; **Jira Cloud** REST v3 (email + API token); an **offline demo ticket** ships so the flow is demoable before real credentials land.

---

## File structure

All paths relative to `D:\AIBluePrint4X\chapter_03_Local_TC_Generator\`:

```
chapter_03_Local_TC_Generator/
├─ app.py                     # Screen 1 — chat, orchestration, prompt build
├─ pages/
│  └─ settings.py             # Screen 2 — credentials + provider config
├─ config_store.py            # .env read/write (single source of truth)
├─ jira_client.py             # Jira Cloud REST v3 fetch + ADF→text + demo fallback
├─ llm_client.py              # Ollama call, Groq call, fallback logic, prompt builder
├─ templates/
│  ├─ TestCaseGen.md          # pre-existing — reused, not rewritten
│  └─ sample_ticket.json      # demo ticket for offline runs
├─ .env                       # gitignored — holds the real credentials
├─ .env.example               # committed, blank values only
├─ .gitignore
├─ requirements.txt
├─ README.md
├─ plan.md                    # this file
└─ src/prompt.md              # pre-existing — untouched
```

---

## Config contract (`.env` keys)

```
JIRA_URL=https://<site>.atlassian.net
JIRA_EMAIL=
JIRA_API_TOKEN=
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=gemma3:1b
GROQ_API_KEY=
GROQ_MODEL=openai/gpt-oss-120b
JIRA_AC_FIELD=
```

`JIRA_AC_FIELD` is optional — when a custom field holds acceptance criteria, use it; otherwise AC is parsed out of the description.

---

## Module specs

### 1. `config_store.py`
- `load_settings() -> dict` — `dotenv.load_dotenv(ENV_PATH, override=True)` then defaults for every key above.
- `save_settings(values) -> None` — **upsert**, not overwrite: read `.env` lines, replace `KEY=` in place, append new keys, preserve comments and order.
- `mask(value)` — display-only masking for secrets.
- `is_configured(settings)` — true when URL + email + token are all present.
- `ENV_PATH` resolved relative to this file, so the app runs from any cwd. Secret values are never logged.

### 2. `jira_client.py`
- `fetch_ticket(key, settings) -> dict` — `GET {JIRA_URL}/rest/api/3/issue/{key}?fields=...`, Basic auth with email + API token, 20s timeout. Returns `{key, summary, description, acceptance_criteria, status, issue_type, source}`.
- `adf_to_text(node)` — recursive walker over Atlassian Document Format (doc/paragraph/heading/lists/tables/code/media/mention) so the LLM gets readable text, not JSON.
- `_split_acceptance_criteria(text)` — pulls an "Acceptance Criteria" section out of the description.
- `ping(settings) -> (bool, str)` — `GET /rest/api/3/myself`; backs the Settings **Test Jira connection** button.
- `JiraError` distinguishes 401 / 403 / 404 / other, so the chat pane can say something actionable.
- **Demo fallback:** keys starting with `DEMO` load `templates/sample_ticket.json` with `source="demo"`. Missing credentials raise a `JiraError` that points at Settings and mentions `DEMO-1`.

### 3. `llm_client.py`
- `ollama_status(settings) -> (bool, str)` — probes `{OLLAMA_BASE_URL}/api/tags` (2s timeout) and checks the configured model is present locally. Never pulls or downloads.
- `_call_ollama(prompt, settings)` — `POST /api/chat`, `stream:false`, `temperature 0.2`.
- `_call_groq(prompt, settings)` — `POST https://api.groq.com/openai/v1/chat/completions` (OpenAI-compatible), Bearer key from Settings.
- `generate(prompt, settings) -> (text, provider_used, note)` — the fallback policy lives here and only here:
  1. `LLM_PROVIDER == "groq"` (explicit opt-out) → Groq. Blank key → clear error.
  2. Otherwise **Ollama first**; on success Groq is never contacted.
  3. Ollama unreachable / model missing / error → Groq if a key is saved (with a note), else a `LLMError` naming the Ollama reason plus a Settings hint.
- `build_test_case_prompt(template_text, ticket, count)` — fills `[NUMBER]`, `[FEATURE]`, `[PASTE REQUIREMENTS HERE]` and appends the ticket's summary/description/AC. Single place prompt text is assembled.

### 4. `app.py` (Screen 1 — Chat)
- ChatGPT-style history in `st.session_state.messages`, rendered with `st.chat_message`.
- Input via `st.chat_input("e.g. create test cases for QA-102")` — the idiomatic box with a built-in send affordance.
- Sidebar: provider status (Ollama ready / Groq fallback armed / not configured), Jira credential status, `st.page_link` to Settings, **Clear chat**.
- Per turn: parse the key with `\b[A-Z][A-Z0-9]+-\d+\b` (optional "N test cases", default 8) → fetch ticket → read `templates/TestCaseGen.md` → build prompt → generate → render markdown table + provider caption + ticket expander + `.md` download.
- `JiraError` / `LLMError` surface as `st.error` inside the assistant bubble — never a raw traceback.

### 5. `pages/settings.py` (Screen 2 — Settings)
- One `st.form`: Jira URL, Jira email, Jira API token (`password`), optional AC custom field, provider selectbox (`ollama` / `groq`), Ollama base URL, Ollama model, Groq API key (`password`), Groq model.
- Secrets render blank with a masked placeholder — leaving them blank keeps the stored value; a **Clear saved secrets** checkbox wipes them.
- **Save settings** → `save_settings()`. **Test Jira connection** → `jira_client.ping()` with the values currently typed in the form. A status block shows Ollama reachability and whether Jira credentials are saved.

### 6. `templates/sample_ticket.json`
A realistic demo ticket (`DEMO-1`) with summary, description and an explicit **Acceptance Criteria** block, so `create test cases for DEMO-1` exercises the whole pipeline offline.

### 7. `requirements.txt`
`streamlit`, `requests`, `python-dotenv`. Nothing else.

### 8. `.gitignore` + `.env.example`
`.gitignore` covers `.env`, `__pycache__/`, `*.pyc`, `.streamlit/secrets.toml`. `.env.example` ships the same keys with blank values.

---

## Implementation order

| # | Step |
|---|---|
| 0 | `plan.md` + `.gitignore` + `.env.example` + `.env` + `requirements.txt` |
| 1 | `config_store.py` |
| 2 | `templates/sample_ticket.json` + `jira_client.py` |
| 3 | `llm_client.py` |
| 4 | `app.py` |
| 5 | `pages/settings.py` |
| 6 | `README.md` + end-to-end verification |

---

## Verification

1. `pip install -r requirements.txt`
2. Import smoke test per module: `config_store.load_settings()`, `jira_client.fetch_ticket("DEMO-1", s)`, `llm_client.ollama_status(s)`.
3. `streamlit run app.py` → send `create test cases for DEMO-1` → expect the `TestCaseGen.md` column set (`Test ID | Description | Pre-conditions | Steps | Expected Result | Priority`), provider caption `Ollama / gemma3:1b`, `source: demo`.
4. Live path: real Jira Cloud credentials in Settings → **Test Jira connection** green → a real key returns real summary/description.
5. Fallback proof: point `OLLAMA_BASE_URL` at `http://localhost:9999` → reply must carry the "Ollama unavailable — answered with Groq" note. Reverse check: with Ollama healthy, the Groq key is never in the request path.
6. Secret-leak grep: no token literals in `*.py`; `git check-ignore chapter_03_Local_TC_Generator/.env` succeeds.
7. Missing-credential path: clear the Jira fields → warning + Settings link, no traceback.

## Known limitations
- Ollama (`gemma3:1b`) output quality on large tickets is limited; Groq produces noticeably better tables.
- Jira Cloud only in v1; Server/DC (REST v2 + PAT) is a one-function change if needed later.
- Acceptance criteria detection is heuristic unless `JIRA_AC_FIELD` is set.
- `.env` stores secrets in plain text on local disk — acceptable for an internal tool, not for shared machines.
