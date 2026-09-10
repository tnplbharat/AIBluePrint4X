"""Persisted settings for the Jira Test Case Generator.

All credentials live in a single `.env` file next to this module. That file is
the source of truth for both the chat screen and the settings screen, and it is
excluded from version control.

No secret value is ever logged or written anywhere else.
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

ENV_PATH = Path(__file__).resolve().parent / ".env"

DEFAULTS = {
    "JIRA_URL": "",
    "JIRA_EMAIL": "",
    "JIRA_API_TOKEN": "",
    "JIRA_AC_FIELD": "",
    "LLM_PROVIDER": "ollama",
    "OLLAMA_BASE_URL": "http://localhost:11434",
    "OLLAMA_MODEL": "gemma3:1b",
    "GROQ_API_KEY": "",
    "GROQ_MODEL": "openai/gpt-oss-120b",
}

SECRET_KEYS = ("JIRA_API_TOKEN", "GROQ_API_KEY")

_SETTINGS_KEYS = tuple(DEFAULTS.keys())


def load_settings() -> dict:
    """Read settings from `.env`, falling back to defaults for anything missing.

    `override=True` makes the file authoritative over stale environment
    variables left behind by an earlier shell session.
    """
    load_dotenv(ENV_PATH, override=True)

    settings = {key: os.getenv(key, default).strip() for key, default in DEFAULTS.items()}
    settings["LLM_PROVIDER"] = settings["LLM_PROVIDER"].lower() or "ollama"
    return settings


def save_settings(values: dict) -> None:
    """Upsert keys into `.env`, preserving comments and line order.

    Keys already present are rewritten in place; unknown keys are appended.
    """
    updates = {
        key: str(values[key]).strip()
        for key in values
        if key in _SETTINGS_KEYS and values[key] is not None
    }

    lines = ENV_PATH.read_text(encoding="utf-8").splitlines() if ENV_PATH.exists() else []
    written: set[str] = set()
    output: list[str] = []

    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            output.append(line)
            continue

        key = stripped.split("=", 1)[0].strip()
        if key in updates:
            output.append(f"{key}={updates[key]}")
            written.add(key)
        else:
            output.append(line)

    missing = [key for key in updates if key not in written]
    if missing:
        if output and output[-1].strip():
            output.append("")
        output.extend(f"{key}={updates[key]}" for key in missing)

    ENV_PATH.write_text("\n".join(output).rstrip("\n") + "\n", encoding="utf-8")


def mask(value: str) -> str:
    """Display-only masking for a secret. Empty in, empty out."""
    if not value:
        return ""
    if len(value) <= 4:
        return "*" * len(value)
    return f"{value[:4]}{'*' * 8}"


def is_configured(settings: dict) -> bool:
    """True when enough Jira credentials are saved to attempt a live call."""
    return bool(
        settings.get("JIRA_URL")
        and settings.get("JIRA_EMAIL")
        and settings.get("JIRA_API_TOKEN")
    )


def provider_label(settings: dict) -> str:
    """Human-readable provider description for the sidebar."""
    provider = (settings.get("LLM_PROVIDER") or "ollama").lower()
    if provider == "groq":
        return "Groq (selected)"
    return f"Ollama ({settings.get('OLLAMA_MODEL', 'gemma3:1b')})"
