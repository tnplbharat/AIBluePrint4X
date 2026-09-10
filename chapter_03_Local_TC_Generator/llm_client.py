"""LLM backends for the test case generator.

Ollama is the default and is always tried first. Groq is only contacted when the
user explicitly selected it in Settings, or when Ollama is unavailable and a
Groq API key has been saved. That policy lives in `generate()` and nowhere else.

The model is never pulled or downloaded — the app assumes the configured Ollama
model is already present locally.
"""

from __future__ import annotations

import requests

OLLAMA_PROBE_TIMEOUT = 2
OLLAMA_REQUEST_TIMEOUT = 300
GROQ_REQUEST_TIMEOUT = 120
GROQ_ENDPOINT = "https://api.groq.com/openai/v1/chat/completions"

TEMPERATURE = 0.2

SYSTEM_PROMPT = (
    "You are a Senior QA Engineer. Follow the user's instructions exactly. "
    "Respond with the requested test case table and nothing else."
)


class LLMError(Exception):
    """Raised when no configured backend could answer, with a UI-safe message."""


def _normalise(model: str) -> str:
    return (model or "").strip().lower().replace(":latest", "")


def _base_url(settings: dict) -> str:
    return (settings.get("OLLAMA_BASE_URL") or "http://localhost:11434").strip().rstrip("/")


def ollama_status(settings: dict) -> tuple[bool, str]:
    """Probe the local Ollama server and confirm the configured model is present."""
    model = (settings.get("OLLAMA_MODEL") or "").strip()
    if not model:
        return False, "No Ollama model configured."

    try:
        response = requests.get(
            f"{_base_url(settings)}/api/tags", timeout=OLLAMA_PROBE_TIMEOUT
        )
    except requests.RequestException as exc:
        return False, f"Ollama is not reachable at {_base_url(settings)} ({exc.__class__.__name__})."

    if response.status_code != 200:
        return False, f"Ollama responded with HTTP {response.status_code}."

    try:
        available = [item.get("name", "") for item in response.json().get("models", [])]
    except ValueError:
        return False, "Ollama returned a response that was not valid JSON."

    if not available:
        return False, "Ollama is running but has no models installed."

    target = _normalise(model)
    for name in available:
        if _normalise(name) == target:
            return True, f"Ollama ready ({model})."

    return False, f"Model '{model}' is not installed in Ollama. Available: {', '.join(available)}"


def _call_ollama(prompt: str, settings: dict) -> str:
    model = (settings.get("OLLAMA_MODEL") or "").strip()
    url = f"{_base_url(settings)}/api/chat"

    body = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        "stream": False,
        "options": {"temperature": TEMPERATURE},
    }

    try:
        response = requests.post(url, json=body, timeout=OLLAMA_REQUEST_TIMEOUT)
    except requests.RequestException as exc:
        raise LLMError(f"Ollama request failed: {exc}") from exc

    if response.status_code == 404:
        raise LLMError(f"Ollama does not have the model '{model}'. Pull it first, or change it in Settings.")

    if response.status_code != 200:
        raise LLMError(f"Ollama returned HTTP {response.status_code}: {response.text.strip()[:200]}")

    try:
        content = (response.json().get("message") or {}).get("content", "")
    except ValueError as exc:
        raise LLMError("Ollama returned a response that was not valid JSON.") from exc

    if not content.strip():
        raise LLMError("Ollama returned an empty response.")

    return content.strip()


def _call_groq(prompt: str, settings: dict) -> str:
    api_key = (settings.get("GROQ_API_KEY") or "").strip()
    if not api_key:
        raise LLMError("No Groq API key is saved. Add one in Settings, or use Ollama.")

    model = (settings.get("GROQ_MODEL") or "openai/gpt-oss-120b").strip()

    body = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        "temperature": TEMPERATURE,
    }

    try:
        response = requests.post(
            GROQ_ENDPOINT,
            json=body,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            timeout=GROQ_REQUEST_TIMEOUT,
        )
    except requests.RequestException as exc:
        raise LLMError(f"Groq request failed: {exc}") from exc

    if response.status_code == 401:
        raise LLMError("Groq rejected the API key (401). Check it in Settings.")

    if response.status_code != 200:
        raise LLMError(f"Groq returned HTTP {response.status_code}: {response.text.strip()[:200]}")

    try:
        choices = response.json().get("choices") or []
    except ValueError as exc:
        raise LLMError("Groq returned a response that was not valid JSON.") from exc

    if not choices:
        raise LLMError("Groq returned no choices.")

    content = (choices[0].get("message") or {}).get("content", "")
    if not content.strip():
        raise LLMError("Groq returned an empty response.")

    return content.strip()


def generate(prompt: str, settings: dict) -> tuple[str, str, str]:
    """Generate an answer, returning (text, provider_used, note).

    Ollama is tried first unless the user explicitly chose Groq. Groq is used as
    a fallback only when Ollama is unavailable and a key is saved.
    """
    provider = (settings.get("LLM_PROVIDER") or "ollama").lower()

    if provider == "groq":
        text = _call_groq(prompt, settings)
        return text, f"Groq ({settings.get('GROQ_MODEL', '')})", "Groq selected in Settings."

    ready, reason = ollama_status(settings)
    if ready:
        return _call_ollama(prompt, settings), f"Ollama ({settings.get('OLLAMA_MODEL', '')})", ""

    if (settings.get("GROQ_API_KEY") or "").strip():
        text = _call_groq(prompt, settings)
        return text, f"Groq ({settings.get('GROQ_MODEL', '')})", f"Ollama unavailable — {reason}"

    raise LLMError(
        f"Ollama is not usable ({reason}) and no Groq API key is saved as a fallback. "
        "Start Ollama, or add a Groq key in Settings."
    )


def build_test_case_prompt(template_text: str, ticket: dict, count: int) -> str:
    """Merge a fetched ticket into the local template to form the final prompt."""
    feature = ticket.get("summary") or ticket.get("key", "the feature")
    description = ticket.get("description") or "Not specified"
    criteria = ticket.get("acceptance_criteria") or ""

    requirements = [
        f"Ticket: {ticket.get('key', '')}",
        f"Summary: {feature}",
        f"Status: {ticket.get('status', '')}",
        f"Issue type: {ticket.get('issue_type', '')}",
        "",
        "Description:",
        description,
    ]

    if criteria:
        requirements += ["", "Acceptance Criteria:", criteria]

    filled = template_text
    replacements = {
        "[NUMBER]": str(count),
        "[FEATURE]": feature,
        "[PASTE REQUIREMENTS HERE]": "\n".join(requirements),
    }
    for placeholder, value in replacements.items():
        filled = filled.replace(placeholder, value)

    if "[PASTE REQUIREMENTS HERE]" not in template_text and requirements:
        filled = f"{filled}\n\nREQUIREMENTS:\n" + "\n".join(requirements)

    return filled.strip()
