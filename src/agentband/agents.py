"""The band: specialized agents that each own one step of an enterprise workflow.

The demo workflow is a support desk. Each agent reads the shared `Context`, does
its one piece, posts a `Message` announcing the hand-off, and writes its output
back to the `Context` for the next agent. The stubs are deterministic, so the
whole band runs with no API key.

    triage -> retriever -> drafter -> reviewer
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

from .backends import Backend, StubBackend
from .bus import Bus, Context, Message

# keyword buckets for the support-desk demo
_CATEGORIES: dict[str, tuple[str, ...]] = {
    "billing": ("invoice", "charge", "refund", "payment", "billed", "subscription"),
    "access": ("login", "password", "locked", "2fa", "sign in", "access"),
    "bug": ("error", "crash", "broken", "not working", "fails", "bug"),
    "feature": ("would like", "feature request", "feature", "suggestion"),
}
# tie-break order when more than one bucket matches; "general" is the fallback
_PRIORITY: tuple[str, ...] = ("billing", "access", "bug", "feature", "general")
_URGENT: tuple[str, ...] = ("urgent", "asap", "immediately", "outage", "down", "cannot work")

_KB: dict[str, str] = {
    "billing": "Refunds post in 5-7 business days. You can change your plan under Settings, then Billing.",
    "access": "Reset your password from the login page. Two-factor can be re-armed under Security.",
    "bug": "Please share the error id and the steps to reproduce. Engineering triages bugs within one business day.",
    "feature": "Your request is logged to the roadmap board and reviewed at the start of each sprint.",
    "general": "A support specialist will follow up with the next steps shortly.",
}

_EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")


@runtime_checkable
class Agent(Protocol):
    name: str
    role: str

    def handle(self, task: str, ctx: Context, bus: Bus) -> str: ...


class TriageAgent:
    """Classify the ticket into a category and set its urgency."""

    name = "triage"
    role = "Classify the ticket and set its urgency."

    def handle(self, task: str, ctx: Context, bus: Bus) -> str:
        text = task.lower()
        scores = {c: sum(1 for kw in kws if kw in text) for c, kws in _CATEGORIES.items()}
        best = max(_PRIORITY, key=lambda c: (scores.get(c, 0), -_PRIORITY.index(c)))
        if scores.get(best, 0) == 0:
            best = "general"
        urgency = "high" if any(w in text for w in _URGENT) else "normal"
        ctx.set("category", best)
        ctx.set("urgency", urgency)
        bus.post(Message(self.name, "retriever", "result", f"category={best} urgency={urgency}"))
        return f"category={best}, urgency={urgency}"


class RetrieverAgent:
    """Pull the relevant knowledge-base snippet for the triaged category."""

    name = "retriever"
    role = "Pull the relevant knowledge-base snippet."

    def handle(self, task: str, ctx: Context, bus: Bus) -> str:
        category = ctx.get("category", "general")
        snippet = _KB.get(category, _KB["general"])
        ctx.set("kb_snippet", snippet)
        bus.post(Message(self.name, "drafter", "result", snippet))
        return snippet


@dataclass
class DrafterAgent:
    """Draft a customer reply from the gathered context.

    Deterministic by default. Pass an LLM `backend` to rewrite the draft in a
    chosen tone; the keyless `StubBackend` leaves it unchanged.
    """

    name: str = field(default="drafter", init=False)
    role: str = field(default="Draft a customer reply from the gathered context.", init=False)
    backend: Backend = field(default_factory=StubBackend)
    tone: str = "warm and concise"

    def handle(self, task: str, ctx: Context, bus: Bus) -> str:
        snippet = ctx.get("kb_snippet", "")
        urgency = ctx.get("urgency", "normal")
        opener = (
            "Thanks for flagging this. We are treating it as urgent"
            if urgency == "high"
            else "Thanks for reaching out"
        )
        draft = f"Hi,\n\n{opener}. {snippet}\n\nBest,\nSupport"
        draft = self.backend.rewrite(draft, tone=self.tone)
        ctx.set("draft", draft)
        bus.post(Message(self.name, "reviewer", "result", "draft ready"))
        return draft


class ReviewerAgent:
    """Check the draft against reply policy and approve it or send it back."""

    name = "reviewer"
    role = "Check the draft against reply policy and approve or bounce it."

    def handle(self, task: str, ctx: Context, bus: Bus) -> str:
        draft = ctx.get("draft", "")
        problems: list[str] = []
        if "Hi" not in draft:
            problems.append("missing greeting")
        if "Support" not in draft:
            problems.append("missing sign-off")
        if _EMAIL.search(draft):
            problems.append("contains an email address")
        approved = not problems
        ctx.set("approved", approved)
        ctx.set("review_notes", problems)
        verdict = "approved" if approved else "changes requested: " + ", ".join(problems)
        bus.post(Message(self.name, "*", "result", verdict))
        return verdict
