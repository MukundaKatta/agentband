"""Test suite for agentband.

Written with the standard-library ``unittest`` framework so it runs with no
third-party dependencies:

    python -m unittest discover -s tests

(``pytest`` discovers and runs ``unittest.TestCase`` classes too, so
``pytest`` still works if you prefer it.)
"""

import json
import unittest

from agentband import (
    BandResult,
    Bus,
    Conductor,
    Context,
    DrafterAgent,
    Message,
    RetrieverAgent,
    ReviewerAgent,
    StubBackend,
    Step,
    TriageAgent,
    default_band,
)


class TriageAgentTests(unittest.TestCase):
    def test_classifies_into_expected_category(self) -> None:
        cases = [
            ("I want a refund on my last invoice", "billing"),
            ("I am locked out and my password reset fails", "access"),
            ("the app keeps throwing an error and crashes", "bug"),
            ("I would like a dark mode feature", "feature"),
            ("hello, just saying hi", "general"),
        ]
        for ticket, expected in cases:
            with self.subTest(ticket=ticket):
                ctx, bus = Context(), Bus()
                TriageAgent().handle(ticket, ctx, bus)
                self.assertEqual(ctx.get("category"), expected)

    def test_detects_high_urgency(self) -> None:
        ctx, bus = Context(), Bus()
        TriageAgent().handle("the whole system is down, this is urgent", ctx, bus)
        self.assertEqual(ctx.get("urgency"), "high")

    def test_normal_urgency_is_the_default(self) -> None:
        ctx, bus = Context(), Bus()
        TriageAgent().handle("I would like a new feature", ctx, bus)
        self.assertEqual(ctx.get("urgency"), "normal")

    def test_posts_handoff_message_to_retriever(self) -> None:
        ctx, bus = Context(), Bus()
        TriageAgent().handle("refund please", ctx, bus)
        self.assertEqual(len(bus.messages), 1)
        msg = bus.messages[0]
        self.assertEqual(msg.sender, "triage")
        self.assertEqual(msg.recipient, "retriever")

    def test_tie_break_prefers_higher_priority_category(self) -> None:
        # mentions both a billing keyword (refund) and an access keyword (login);
        # billing wins per the documented _PRIORITY order.
        ctx, bus = Context(), Bus()
        TriageAgent().handle("I cannot login and I want a refund", ctx, bus)
        self.assertEqual(ctx.get("category"), "billing")

    def test_empty_ticket_falls_back_to_general(self) -> None:
        ctx, bus = Context(), Bus()
        TriageAgent().handle("", ctx, bus)
        self.assertEqual(ctx.get("category"), "general")
        self.assertEqual(ctx.get("urgency"), "normal")


class RetrieverAgentTests(unittest.TestCase):
    def test_sets_snippet_for_category(self) -> None:
        ctx, bus = Context(), Bus()
        ctx.set("category", "billing")
        snippet = RetrieverAgent().handle("", ctx, bus)
        self.assertIn("Refund", snippet)
        self.assertEqual(ctx.get("kb_snippet"), snippet)

    def test_unknown_category_falls_back_to_general_snippet(self) -> None:
        ctx, bus = Context(), Bus()
        ctx.set("category", "does-not-exist")
        snippet = RetrieverAgent().handle("", ctx, bus)
        self.assertEqual(snippet, "A support specialist will follow up with the next steps shortly.")

    def test_missing_category_defaults_to_general(self) -> None:
        ctx, bus = Context(), Bus()  # no category set at all
        snippet = RetrieverAgent().handle("", ctx, bus)
        self.assertIn("support specialist", snippet)


class DrafterAgentTests(unittest.TestCase):
    def test_draft_has_greeting_and_signoff(self) -> None:
        ctx, bus = Context(), Bus()
        ctx.set("kb_snippet", "Some help text.")
        ctx.set("urgency", "normal")
        draft = DrafterAgent().handle("", ctx, bus)
        self.assertTrue(draft.startswith("Hi,"))
        self.assertTrue(draft.rstrip().endswith("Support"))

    def test_urgent_ticket_uses_urgent_opener(self) -> None:
        ctx, bus = Context(), Bus()
        ctx.set("kb_snippet", "Some help text.")
        ctx.set("urgency", "high")
        draft = DrafterAgent().handle("", ctx, bus)
        self.assertIn("urgent", draft.lower())

    def test_normal_ticket_does_not_use_urgent_opener(self) -> None:
        ctx, bus = Context(), Bus()
        ctx.set("kb_snippet", "Some help text.")
        ctx.set("urgency", "normal")
        draft = DrafterAgent().handle("", ctx, bus)
        self.assertNotIn("urgent", draft.lower())

    def test_backend_rewrite_is_applied(self) -> None:
        class ShoutBackend:
            name = "shout"

            def rewrite(self, text: str, *, tone: str) -> str:
                return text.upper()

        ctx, bus = Context(), Bus()
        ctx.set("kb_snippet", "help text")
        ctx.set("urgency", "normal")
        draft = DrafterAgent(backend=ShoutBackend()).handle("", ctx, bus)
        self.assertEqual(draft, draft.upper())


class StubBackendTests(unittest.TestCase):
    def test_is_passthrough(self) -> None:
        self.assertEqual(StubBackend().rewrite("unchanged", tone="warm"), "unchanged")

    def test_default_drafter_backend_is_the_stub(self) -> None:
        self.assertIsInstance(DrafterAgent().backend, StubBackend)


class ReviewerAgentTests(unittest.TestCase):
    def test_approves_clean_draft(self) -> None:
        ctx, bus = Context(), Bus()
        ctx.set("draft", "Hi,\n\nThanks. Help text.\n\nBest,\nSupport")
        verdict = ReviewerAgent().handle("", ctx, bus)
        self.assertEqual(verdict, "approved")
        self.assertIs(ctx.get("approved"), True)
        self.assertEqual(ctx.get("review_notes"), [])

    def test_bounces_email_leak(self) -> None:
        ctx, bus = Context(), Bus()
        ctx.set("draft", "Hi,\n\nEmail us at help@acme.com.\n\nBest,\nSupport")
        verdict = ReviewerAgent().handle("", ctx, bus)
        self.assertIs(ctx.get("approved"), False)
        self.assertIn("email address", verdict)

    def test_bounces_missing_greeting_and_signoff(self) -> None:
        ctx, bus = Context(), Bus()
        ctx.set("draft", "no greeting and no signoff here")
        ReviewerAgent().handle("", ctx, bus)
        notes = ctx.get("review_notes")
        self.assertIn("missing greeting", notes)
        self.assertIn("missing sign-off", notes)

    def test_broadcasts_verdict_to_everyone(self) -> None:
        ctx, bus = Context(), Bus()
        ctx.set("draft", "Hi,\n\nok.\n\nBest,\nSupport")
        ReviewerAgent().handle("", ctx, bus)
        self.assertEqual(bus.messages[-1].recipient, "*")


class BusAndContextTests(unittest.TestCase):
    def test_broadcast_reaches_everyone(self) -> None:
        bus = Bus()
        bus.post(Message("a", "*", "note", "hello all"))
        bus.post(Message("a", "b", "note", "for b only"))
        self.assertEqual(len(bus.for_recipient("z")), 1)  # only the broadcast
        self.assertEqual(len(bus.for_recipient("b")), 2)  # broadcast + direct

    def test_message_to_dict_round_trips_fields(self) -> None:
        msg = Message("triage", "retriever", "result", "category=billing")
        self.assertEqual(
            msg.to_dict(),
            {
                "sender": "triage",
                "recipient": "retriever",
                "kind": "result",
                "content": "category=billing",
            },
        )

    def test_context_get_returns_default_for_missing_key(self) -> None:
        ctx = Context()
        self.assertIsNone(ctx.get("missing"))
        self.assertEqual(ctx.get("missing", "fallback"), "fallback")

    def test_context_to_dict_is_a_copy(self) -> None:
        ctx = Context()
        ctx.set("a", 1)
        snapshot = ctx.to_dict()
        snapshot["a"] = 999
        self.assertEqual(ctx.get("a"), 1)  # mutating the copy must not leak back


class ConductorTests(unittest.TestCase):
    def test_end_to_end_approves_billing_ticket(self) -> None:
        result = Conductor().run("I need a refund, my invoice was wrong and this is urgent")
        self.assertIs(result.approved, True)
        self.assertTrue(result.final_reply.startswith("Hi,"))
        self.assertEqual(
            [s.agent for s in result.steps],
            ["triage", "retriever", "drafter", "reviewer"],
        )
        self.assertEqual(result.context["category"], "billing")
        self.assertEqual(result.context["urgency"], "high")

    def test_records_full_message_trace(self) -> None:
        result = Conductor().run("the app crashes with an error")
        self.assertEqual(len(result.messages), 4)
        senders = [m["sender"] for m in result.messages]
        self.assertEqual(senders, ["triage", "retriever", "drafter", "reviewer"])

    def test_result_is_json_serializable(self) -> None:
        result = Conductor().run("please reset my password, I am locked out")
        back = json.loads(json.dumps(result.to_dict()))
        self.assertIs(back["approved"], True)
        self.assertEqual(back["context"]["category"], "access")

    def test_custom_band_is_honoured(self) -> None:
        # A conductor with only triage records exactly one step.
        result = Conductor(band=[TriageAgent()]).run("refund please")
        self.assertEqual([s.agent for s in result.steps], ["triage"])
        # No drafter ran, so there is no draft / approval.
        self.assertEqual(result.final_reply, "")
        self.assertIs(result.approved, False)

    def test_run_is_deterministic(self) -> None:
        ticket = "the whole system is down, this is urgent"
        first = Conductor().run(ticket).to_dict()
        second = Conductor().run(ticket).to_dict()
        self.assertEqual(first, second)

    def test_each_run_is_isolated(self) -> None:
        conductor = Conductor()
        billing = conductor.run("refund my invoice")
        access = conductor.run("I am locked out, password reset fails")
        # The second run must not inherit the first run's category.
        self.assertEqual(billing.context["category"], "billing")
        self.assertEqual(access.context["category"], "access")


class DataclassHelperTests(unittest.TestCase):
    def test_default_band_shape(self) -> None:
        band = default_band()
        self.assertEqual(
            [a.name for a in band],
            ["triage", "retriever", "drafter", "reviewer"],
        )

    def test_step_to_dict(self) -> None:
        step = Step(agent="triage", role="classify", output="category=billing")
        self.assertEqual(
            step.to_dict(),
            {"agent": "triage", "role": "classify", "output": "category=billing"},
        )

    def test_band_result_properties_default_safely(self) -> None:
        # A result with an empty context exposes sane defaults rather than raising.
        result = BandResult(task="t", steps=[], context={}, messages=[])
        self.assertEqual(result.final_reply, "")
        self.assertIs(result.approved, False)


if __name__ == "__main__":
    unittest.main()
