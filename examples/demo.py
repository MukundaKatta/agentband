"""agentband demo — runs offline, no API key required.

    python examples/demo.py

Runs a band of agents (triage, retriever, drafter, reviewer) over a couple of
support tickets and prints the per-agent steps, the message trace, and the
final reply each band produced.
"""

from __future__ import annotations

from agentband import Conductor

TICKETS = [
    "My invoice looks wrong and I want a refund. This is urgent, we are blocked.",
    "I can't sign in, my password reset keeps failing.",
    "Would love a dark mode feature someday.",
]


def main() -> None:
    conductor = Conductor()
    for ticket in TICKETS:
        result = conductor.run(ticket)
        print("=" * 68)
        print("TICKET:", ticket)
        print("-" * 68)
        for step in result.steps:
            print(f"  [{step.agent:9}] {step.output}")
        print("-" * 68)
        print("MESSAGE TRACE:")
        for m in result.messages:
            print(f"  {m['sender']} -> {m['recipient']}: {m['content']}")
        print("-" * 68)
        print(f"APPROVED: {result.approved}")
        print(result.final_reply)
        print()


if __name__ == "__main__":
    main()
