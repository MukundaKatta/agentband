"""The conductor runs a band of agents over one task, in order, sharing context.

It is deliberately small: an ordered plan of agents, one shared `Context`, and a
`Bus` that records every hand-off. The `BandResult` bundles the final context,
the per-agent log, and the full message trace, so a run is fully inspectable.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .agents import Agent, DrafterAgent, RetrieverAgent, ReviewerAgent, TriageAgent
from .bus import Bus, Context


@dataclass
class Step:
    agent: str
    role: str
    output: str

    def to_dict(self) -> dict[str, str]:
        return {"agent": self.agent, "role": self.role, "output": self.output}


@dataclass
class BandResult:
    task: str
    steps: list[Step]
    context: dict[str, Any]
    messages: list[dict[str, str]]

    @property
    def final_reply(self) -> str:
        return self.context.get("draft", "")

    @property
    def approved(self) -> bool:
        return bool(self.context.get("approved", False))

    def to_dict(self) -> dict[str, Any]:
        return {
            "task": self.task,
            "approved": self.approved,
            "final_reply": self.final_reply,
            "steps": [s.to_dict() for s in self.steps],
            "context": self.context,
            "messages": self.messages,
        }


def default_band() -> list[Agent]:
    """The support-desk band: triage -> retriever -> drafter -> reviewer."""
    return [TriageAgent(), RetrieverAgent(), DrafterAgent(), ReviewerAgent()]


@dataclass
class Conductor:
    """Runs an ordered band over a task and returns an inspectable result."""

    band: list[Agent] = field(default_factory=default_band)

    def run(self, task: str) -> BandResult:
        ctx = Context()
        bus = Bus()
        ctx.set("task", task)
        steps: list[Step] = []
        for agent in self.band:
            output = agent.handle(task, ctx, bus)
            steps.append(Step(agent.name, agent.role, output))
        return BandResult(
            task=task,
            steps=steps,
            context=ctx.to_dict(),
            messages=bus.to_list(),
        )
