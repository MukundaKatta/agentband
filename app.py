"""agentband dashboard — watch a band of agents handle a support ticket.

    pip install -e ".[dashboard]"
    streamlit run app.py

Runs offline against the keyless stub band by default.
"""

from __future__ import annotations

import streamlit as st

from agentband import Conductor

SAMPLE = "My invoice looks wrong and I want a refund. This is urgent, we are blocked."

st.set_page_config(page_title="agentband", page_icon="🎸", layout="wide")

st.title("🎸 agentband")
st.caption(
    "A band of specialized agents share context over a bus and finish an "
    "enterprise workflow together. Triage, retrieve, draft, review. No key, runs offline."
)

col_in, col_out = st.columns(2)

with col_in:
    ticket = st.text_area("Incoming support ticket", value=SAMPLE, height=200)
    go = st.button("Run the band", type="primary")

with col_out:
    if go:
        if not ticket.strip():
            st.warning("Paste a ticket first.")
            st.stop()

        result = Conductor().run(ticket)

        c1, c2, c3 = st.columns(3)
        c1.metric("Category", result.context.get("category", "—"))
        c2.metric("Urgency", result.context.get("urgency", "—"))
        c3.metric("Approved", "yes" if result.approved else "no")

        st.subheader("Steps")
        for step in result.steps:
            st.markdown(f"**{step.agent}** — {step.role}")
            st.code(step.output, language="text")

        st.subheader("Message trace")
        st.table(result.messages)

        st.subheader("Final reply")
        st.code(result.final_reply, language="text")
