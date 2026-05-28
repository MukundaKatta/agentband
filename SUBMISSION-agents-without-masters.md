# DoraHacks Agents Without Masters — submission copy (agentband)

Event: DoraHacks "Agents Without Masters" — autonomous multi-agent, $25K.
Deadline 2026-06-16. Same agentband build as the Band of Agents submission;
this copy is reframed for the "no central master" theme.

Repo: https://github.com/MukundaKatta/agentband

## Why agentband fits "Agents Without Masters"

The theme is autonomy without a commanding orchestrator. agentband's core
design rule is exactly that: agents never call each other and nothing
"drives" them. Each agent reads and writes one shared Context (a blackboard)
and posts to a recorded Bus. Coordination is emergent from shared state, not
dictated by a master process. Swap, reorder, or add an agent and the
machinery is unchanged because no agent holds a reference to another.

## Short description

    agentband is a keyless band of specialized agents that finish an
    enterprise workflow together with no master agent in charge. They
    coordinate only through a shared Context blackboard and a recorded message
    Bus, so the whole run is an auditable trace instead of a black box.

## What it does

    The bundled workflow is a support desk: triage classifies the ticket and
    sets urgency, the retriever pulls the matching knowledge-base snippet, the
    drafter writes the reply, and the reviewer checks it against policy and
    approves or bounces it. No agent calls another. Each reads shared context
    and posts to the bus, so hand-offs are observable and recorded. The
    reviewer is a real gate: it bounces a draft that leaks an email address or
    drops the greeting or sign-off, and records why.

## How we built it

    Two primitives do all the coordination: a Context blackboard every agent
    reads and writes, and a Bus that records every message in order. Agents are
    deterministic stubs, so the band runs with no API key. Any agent can take an
    optional, lazily-imported LLM backend (Gemini, Anthropic, or Ollama) to
    phrase its output as prose. Zero core dependencies, a Streamlit dashboard,
    and a test suite that runs fully offline.

## Autonomy / no-master design notes

    - No agent imports or calls another agent.
    - There is no central controller issuing commands; the Conductor only
      threads the shared Context and Bus through whatever band is configured.
    - Every hand-off is a recorded Bus message, so the coordination is a
      replayable audit log.
    - Adding, removing, or reordering an agent is a one-line change because
      agents are decoupled through shared state.

## What's next

    A planner agent that picks the band per task, parallel agents where steps
    do not depend on each other, and a retry loop where a bounced draft goes
    back to the drafter with the reviewer's notes.

## Tech tags

    python, multi-agent, autonomous-agents, agent-orchestration,
    agent-coordination, message-bus, blackboard, enterprise-workflow, llm,
    streamlit, mit

## Links

  - Repo: https://github.com/MukundaKatta/agentband
  - Demo: `python examples/demo.py` (offline, no key)
  - Dashboard: `streamlit run app.py`
