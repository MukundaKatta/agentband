"""agentband — a small, keyless multi-agent coordinator.

Specialized agents share a `Context` and pass messages over a `Bus` to finish an
enterprise workflow together. Runs offline with a deterministic stub; plug in an
LLM backend only when you want prose phrasing.
"""

from __future__ import annotations

from .agents import (
    Agent,
    DrafterAgent,
    RetrieverAgent,
    ReviewerAgent,
    TriageAgent,
)
from .backends import (
    AnthropicBackend,
    Backend,
    GeminiBackend,
    OllamaBackend,
    StubBackend,
)
from .bus import Bus, Context, Message
from .conductor import BandResult, Conductor, Step, default_band

__all__ = [
    "Agent",
    "TriageAgent",
    "RetrieverAgent",
    "DrafterAgent",
    "ReviewerAgent",
    "Backend",
    "StubBackend",
    "GeminiBackend",
    "AnthropicBackend",
    "OllamaBackend",
    "Bus",
    "Context",
    "Message",
    "Conductor",
    "BandResult",
    "Step",
    "default_band",
]

__version__ = "0.1.0"
