# agentband — submission copy

**Repo:** https://github.com/MukundaKatta/agentband

**Target event:** Band of Agents (lablab, online, Jun 12-19 2026) — enterprise multi-agent coordination

**Tagline:** A band of small agents share context over a bus to finish an enterprise workflow together.

## Short description

agentband is a keyless multi-agent coordinator. Specialized agents (triage,
retriever, drafter, reviewer) read and write one shared context and pass
messages over a bus to complete an enterprise support workflow together. Every
hand-off is recorded, so the coordination is an audit log you can replay.

## Inspiration

Most agent demos are one model in a loop. Real enterprise work is a chain of
hand-offs: a request gets triaged, someone looks up policy, someone drafts a
reply, someone reviews it before it goes out. We wanted to model that hand-off
directly, and make the coordination something you can inspect instead of trust
on faith.

## What it does

It runs a band of specialized agents over one task. The bundled workflow is a
support desk: triage classifies the ticket and sets urgency, the retriever pulls
the matching knowledge-base snippet, the drafter writes the reply, and the
reviewer checks it against policy and approves or bounces it. Agents never call
each other. They write to a shared context and post to a message bus, so the
whole run is observable and every hand-off is recorded.

## How we built it

Two small primitives do the coordination: a Context blackboard every agent reads
and writes, and a Bus that records every message in order. Agents are
deterministic stubs so the band runs with no API key. Any agent can take an
optional, lazily-imported LLM backend (Gemini, Anthropic, or Ollama) to phrase
its output as prose. Zero core dependencies, a Streamlit dashboard, and a test
suite that runs fully offline.

## Challenges we ran into

Keeping coordination observable without letting agents reach into each other.
Routing everything through a shared context and a recorded bus meant adding,
reordering, or replacing an agent is a one-line change, and the message trace is
a real audit log. The reviewer also had to be a genuine gate, not decoration, so
it bounces a draft that leaks an email address or drops the greeting or sign-off.

## Accomplishments we're proud of

The band finishes a real workflow end to end, the full message trace is
serializable for replay, and it all runs with no key and zero dependencies. The
reviewer actually stops bad replies.

## What we learned

Multi-agent value comes from clean hand-offs and observability, not from more
models. A shared blackboard plus a recorded bus gets you both.

## What's next

A planner agent that picks the band per task, parallel agents where steps do not
depend on each other, and a retry loop where a bounced draft goes back to the
drafter with the reviewer's notes.

## Tech tags

python, multi-agent, agent-orchestration, agent-coordination, message-bus,
blackboard, enterprise-workflow, llm, streamlit, mit
