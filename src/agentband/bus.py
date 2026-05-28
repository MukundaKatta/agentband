"""In-process message bus and shared context for a band of agents.

Agents never call each other directly. They post messages to the `Bus` and
read or write a shared `Context` (a blackboard). That keeps coordination
observable: every hand-off is a recorded `Message` you can replay later, which
is what makes a multi-agent run auditable instead of a black box.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Message:
    """One hand-off between agents. `recipient` is an agent name or "*" (broadcast)."""

    sender: str
    recipient: str
    kind: str
    content: str

    def to_dict(self) -> dict[str, str]:
        return {
            "sender": self.sender,
            "recipient": self.recipient,
            "kind": self.kind,
            "content": self.content,
        }


@dataclass
class Context:
    """The shared blackboard the band reads and writes as work flows through it."""

    facts: dict[str, Any] = field(default_factory=dict)

    def set(self, key: str, value: Any) -> None:
        self.facts[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        return self.facts.get(key, default)

    def to_dict(self) -> dict[str, Any]:
        return dict(self.facts)


@dataclass
class Bus:
    """Records every message. The ordered trace is the audit log of coordination."""

    messages: list[Message] = field(default_factory=list)

    def post(self, message: Message) -> None:
        self.messages.append(message)

    def for_recipient(self, name: str) -> list[Message]:
        return [m for m in self.messages if m.recipient in (name, "*")]

    def to_list(self) -> list[dict[str, str]]:
        return [m.to_dict() for m in self.messages]
