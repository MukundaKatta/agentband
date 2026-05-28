import json

import pytest

from agentband import (
    Bus,
    Conductor,
    Context,
    DrafterAgent,
    Message,
    ReviewerAgent,
    RetrieverAgent,
    StubBackend,
    TriageAgent,
    default_band,
)


@pytest.mark.parametrize(
    "ticket,expected",
    [
        ("I want a refund on my last invoice", "billing"),
        ("I am locked out and my password reset fails", "access"),
        ("the app keeps throwing an error and crashes", "bug"),
        ("I would like a dark mode feature", "feature"),
        ("hello, just saying hi", "general"),
    ],
)
def test_triage_classifies(ticket, expected):
    ctx, bus = Context(), Bus()
    TriageAgent().handle(ticket, ctx, bus)
    assert ctx.get("category") == expected


def test_triage_detects_urgency():
    ctx, bus = Context(), Bus()
    TriageAgent().handle("the whole system is down, this is urgent", ctx, bus)
    assert ctx.get("urgency") == "high"


def test_triage_normal_urgency_default():
    ctx, bus = Context(), Bus()
    TriageAgent().handle("I would like a new feature", ctx, bus)
    assert ctx.get("urgency") == "normal"


def test_retriever_sets_snippet_for_category():
    ctx, bus = Context(), Bus()
    ctx.set("category", "billing")
    snippet = RetrieverAgent().handle("", ctx, bus)
    assert "Refund" in snippet
    assert ctx.get("kb_snippet") == snippet


def test_drafter_has_greeting_and_signoff():
    ctx, bus = Context(), Bus()
    ctx.set("kb_snippet", "Some help text.")
    ctx.set("urgency", "normal")
    draft = DrafterAgent().handle("", ctx, bus)
    assert draft.startswith("Hi,")
    assert draft.rstrip().endswith("Support")


def test_drafter_urgent_opener():
    ctx, bus = Context(), Bus()
    ctx.set("kb_snippet", "Some help text.")
    ctx.set("urgency", "high")
    draft = DrafterAgent().handle("", ctx, bus)
    assert "urgent" in draft.lower()


def test_stub_backend_is_passthrough():
    assert StubBackend().rewrite("unchanged", tone="warm") == "unchanged"


def test_reviewer_approves_clean_draft():
    ctx, bus = Context(), Bus()
    ctx.set("draft", "Hi,\n\nThanks. Help text.\n\nBest,\nSupport")
    verdict = ReviewerAgent().handle("", ctx, bus)
    assert verdict == "approved"
    assert ctx.get("approved") is True


def test_reviewer_bounces_email_leak():
    ctx, bus = Context(), Bus()
    ctx.set("draft", "Hi,\n\nEmail us at help@acme.com.\n\nBest,\nSupport")
    verdict = ReviewerAgent().handle("", ctx, bus)
    assert ctx.get("approved") is False
    assert "email address" in verdict


def test_reviewer_bounces_missing_parts():
    ctx, bus = Context(), Bus()
    ctx.set("draft", "no greeting and no signoff here")
    ReviewerAgent().handle("", ctx, bus)
    notes = ctx.get("review_notes")
    assert "missing greeting" in notes
    assert "missing sign-off" in notes


def test_bus_broadcast_reaches_everyone():
    bus = Bus()
    bus.post(Message("a", "*", "note", "hello all"))
    bus.post(Message("a", "b", "note", "for b only"))
    assert len(bus.for_recipient("z")) == 1  # only the broadcast
    assert len(bus.for_recipient("b")) == 2  # broadcast + direct


def test_conductor_end_to_end_approves():
    result = Conductor().run("I need a refund, my invoice was wrong and this is urgent")
    assert result.approved is True
    assert result.final_reply.startswith("Hi,")
    assert [s.agent for s in result.steps] == ["triage", "retriever", "drafter", "reviewer"]
    assert result.context["category"] == "billing"
    assert result.context["urgency"] == "high"


def test_conductor_records_full_message_trace():
    result = Conductor().run("the app crashes with an error")
    # one hand-off message per agent
    assert len(result.messages) == 4
    senders = [m["sender"] for m in result.messages]
    assert senders == ["triage", "retriever", "drafter", "reviewer"]


def test_band_result_is_json_serializable():
    result = Conductor().run("please reset my password, I am locked out")
    blob = json.dumps(result.to_dict())
    back = json.loads(blob)
    assert back["approved"] is True
    assert back["context"]["category"] == "access"


def test_default_band_shape():
    band = default_band()
    assert [a.name for a in band] == ["triage", "retriever", "drafter", "reviewer"]
