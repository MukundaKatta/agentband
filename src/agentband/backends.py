"""Optional LLM backends for agents that want to phrase output as prose.

`StubBackend` is deterministic and keyless: it passes text through unchanged, so
the whole band runs offline with no API key. The LLM backends import their SDK
lazily, so installing agentband never pulls a vendor dependency.

A backend implements one method:

    rewrite(text, *, tone) -> str
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class Backend(Protocol):
    name: str

    def rewrite(self, text: str, *, tone: str) -> str: ...


class StubBackend:
    """Deterministic, keyless. Returns the draft unchanged."""

    name = "stub"

    def rewrite(self, text: str, *, tone: str) -> str:
        return text


def _prompt(text: str, tone: str) -> str:
    return (
        f"Rewrite the support reply below in a {tone} tone. Keep every fact, the "
        f"greeting, and the sign-off. Return only the rewritten reply.\n\n{text}"
    )


class GeminiBackend:
    """Google Gemini backend. Requires `google-genai` and GEMINI_API_KEY."""

    name = "gemini"

    def __init__(self, model: str = "gemini-2.5-flash", api_key: str | None = None):
        from google import genai  # lazy import

        import os

        self._client = genai.Client(api_key=api_key or os.environ["GEMINI_API_KEY"])
        self._model = model

    def rewrite(self, text: str, *, tone: str) -> str:
        resp = self._client.models.generate_content(model=self._model, contents=_prompt(text, tone))
        return (resp.text or "").strip()


class AnthropicBackend:
    """Anthropic Claude backend. Requires `anthropic` and ANTHROPIC_API_KEY."""

    name = "anthropic"

    def __init__(self, model: str = "claude-sonnet-4-6", api_key: str | None = None):
        import anthropic  # lazy import

        self._client = anthropic.Anthropic(api_key=api_key)
        self._model = model

    def rewrite(self, text: str, *, tone: str) -> str:
        msg = self._client.messages.create(
            model=self._model,
            max_tokens=512,
            messages=[{"role": "user", "content": _prompt(text, tone)}],
        )
        return "".join(b.text for b in msg.content if b.type == "text").strip()


class OllamaBackend:
    """Local Ollama backend. Requires a running ollama server. No key."""

    name = "ollama"

    def __init__(self, model: str = "llama3.2", host: str = "http://localhost:11434"):
        self._model = model
        self._host = host.rstrip("/")

    def rewrite(self, text: str, *, tone: str) -> str:
        import httpx  # lazy import

        resp = httpx.post(
            f"{self._host}/api/generate",
            json={"model": self._model, "prompt": _prompt(text, tone), "stream": False},
            timeout=120.0,
        )
        resp.raise_for_status()
        return resp.json().get("response", "").strip()
