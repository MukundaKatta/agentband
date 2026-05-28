# agentband 🎸

A small **multi-agent coordinator**. Specialized agents share one context and
pass messages over a bus to finish an **enterprise workflow together** — no
single model doing everything, and no API key required to run it.

[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-pytest-blueviolet.svg)](tests/)

---

## Why

Most "agent" demos are one model in a loop. Real enterprise work is a handoff:
something gets triaged, someone looks up policy, someone drafts, someone
reviews. agentband models that as a **band of small agents** that coordinate
through two shared primitives:

- A **Context** (a blackboard) every agent reads and writes.
- A **Bus** that records every message, so the coordination is an audit log you
  can replay — not a black box.

The bundled workflow is a support desk: `triage → retriever → drafter →
reviewer`. Swap the band for your own steps and the machinery is unchanged.

## Quickstart (no API key)

```bash
pip install -e .
python examples/demo.py
```

```python
from agentband import Conductor

result = Conductor().run(
    "My invoice looks wrong and I want a refund. This is urgent, we are blocked."
)

print(result.context["category"])  # billing
print(result.context["urgency"])   # high
print(result.approved)             # True
print(result.final_reply)
```

Every run returns a `BandResult` you can index into or serialize:

```python
result.steps        # per-agent log: who did what
result.messages     # full ordered message trace between agents
result.to_dict()    # JSON-ready, for logging or replay
```

## The band

| Agent | Role | Reads | Writes |
| --------- | ------------------------------------ | ----------------- | ----------------------- |
| `triage` | Classify the ticket, set urgency | the raw ticket | `category`, `urgency` |
| `retriever` | Pull the matching KB snippet | `category` | `kb_snippet` |
| `drafter` | Compose the reply | `kb_snippet`, `urgency` | `draft` |
| `reviewer` | Check policy, approve or bounce | `draft` | `approved`, `review_notes` |

Agents never call each other. They post to the bus and write to the context,
so adding, reordering, or replacing an agent is a one-line change.

## Coordination is observable

```python
for m in result.messages:
    print(m["sender"], "->", m["recipient"], ":", m["content"])
# triage -> retriever : category=billing urgency=high
# retriever -> drafter : Refunds post in 5-7 business days. ...
# drafter -> reviewer : draft ready
# reviewer -> * : approved
```

The reviewer is a real gate: it bounces a draft that leaks an email address or
drops the greeting or sign-off, and records why.

## LLM phrasing (optional)

The band is deterministic. If you want an agent to phrase its output as prose,
hand it a backend. All are lazily imported, so the core install pulls **zero**
vendor deps.

| Backend | Install | Needs |
| ------------------ | -------------- | --------------------- |
| `StubBackend` | (built in) | nothing — passthrough |
| `GeminiBackend` | `.[gemini]` | `GEMINI_API_KEY` |
| `AnthropicBackend` | `.[anthropic]` | `ANTHROPIC_API_KEY` |
| `OllamaBackend` | `.[ollama]` | a local Ollama server |

```python
from agentband import Conductor, DrafterAgent, TriageAgent, RetrieverAgent, ReviewerAgent, GeminiBackend

band = [TriageAgent(), RetrieverAgent(), DrafterAgent(backend=GeminiBackend()), ReviewerAgent()]
result = Conductor(band=band).run("I can't sign in, my password reset keeps failing.")
```

Triage, retrieval, and review stay deterministic; only the drafted prose
changes.

## Dashboard

```bash
pip install -e ".[dashboard]"
streamlit run app.py
```

Paste a ticket, watch each agent fire, and read the message trace and final
reply.

## Tests

```bash
pip install -e ".[dev]"
pytest
```

Runs fully offline against the stub band.

## License

MIT — see [LICENSE](LICENSE).
