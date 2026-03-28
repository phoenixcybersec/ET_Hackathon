import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import streamlit as st
import sqlite3
import pandas as pd

st.set_page_config(page_title="Agentic SLA Dashboard", layout="wide")

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../tickets.db"))
conn = sqlite3.connect(DB_PATH, check_same_thread=False)


# ================================================================
# DATA
# ================================================================
def load_data():
    return pd.read_sql_query("SELECT * FROM tickets ORDER BY updated_at DESC", conn)

def save_approval(ticket_id, action: str):
    final = {"APPROVED": "AUTO-FIX", "REJECTED": "REJECTED", "ESCALATED": "ESCALATE"}.get(action, action)
    conn.execute("""
        UPDATE tickets SET approved_by_human=?, final_decision=?, human_action=?
        WHERE ticket_id=?
    """, (1 if action == "APPROVED" else 0, final, action, ticket_id))
    conn.commit()

def mark_executed(ticket_id):
    conn.execute("UPDATE tickets SET human_executed=1 WHERE ticket_id=?", (ticket_id,))
    conn.commit()


# ================================================================
# STYLING HELPERS
# ================================================================
def badge(label, color):
    return (
        f'<span style="background:{color};color:#fff;padding:4px 14px;'
        f'border-radius:20px;font-size:12px;font-weight:700;'
        f'letter-spacing:0.5px;display:inline-block">{label}</span>'
    )

DECISION_COLOR = {
    "AUTO-FIX":     "#22c55e",
    "ESCALATE":     "#ef4444",
    "HUMAN-REVIEW": "#f59e0b",
    "MONITOR":      "#3b82f6",
    "REJECTED":     "#6b7280",
    "PENDING":      "#9ca3af",
}
PRIORITY_COLOR = {
    "Critical": "#ef4444",
    "High":     "#f97316",
    "Medium":   "#f59e0b",
    "Low":      "#22c55e",
}

def stars(p):
    try:    p = int(p)
    except: p = 0
    return "★" * p + "☆" * (3 - p)


# ================================================================
# AGENT PIPELINE CHAIN
# ================================================================
def render_pipeline(ticket):
    ai_done        = bool(ticket.get("ai_decision"))
    decision_done  = bool(ticket.get("final_decision"))
    human_exec     = int(ticket.get("human_executed") or 0)
    verified       = ticket.get("verified")
    ver_result     = ticket.get("verification_result", "")
    final          = ticket.get("final_decision", "")
    requires_human = int(ticket.get("requires_human") or 0)
    approved       = ticket.get("approved_by_human")

    # Execution node
    if final == "REJECTED":
        exec_label, exec_color = "Rejected", "#ef4444"
    elif final == "ESCALATE":
        exec_label, exec_color = "Escalated", "#ef4444"
    elif human_exec:
        exec_label, exec_color = "Done ✓", "#22c55e"
    elif approved == 1 or (final == "AUTO-FIX" and not requires_human):
        exec_label, exec_color = "Queued ▶", "#22c55e"
    elif requires_human and not approved:
        exec_label, exec_color = "Awaiting Human", "#f59e0b"
    else:
        exec_label, exec_color = "Pending", "#6b7280"

    # Verification node
    if verified == 1:
        ver_label = "SUCCESS ✓" if ver_result == "SUCCESS" else "Attention ⚠"
        ver_color = "#22c55e"  if ver_result == "SUCCESS" else "#f59e0b"
    elif human_exec:
        ver_label, ver_color = "Running…", "#3b82f6"
    else:
        ver_label, ver_color = "Waiting",  "#6b7280"

    steps = [
        ("🧠 Classifier",    "#22c55e" if ai_done       else "#6b7280", "Done ✓"  if ai_done       else "Pending"),
        ("⚖️ Decision",      "#22c55e" if decision_done  else "#6b7280", "Done ✓"  if decision_done  else "Pending"),
        ("⚡ Execution",     exec_color, exec_label),
        ("🛡️ Verification",  ver_color,  ver_label),
    ]

    html = '<div style="display:flex;align-items:center;margin:14px 0 6px 0;flex-wrap:wrap;gap:0">'
    for i, (name, color, status) in enumerate(steps):
        next_color = steps[i + 1][1] if i < len(steps) - 1 else color
        connector  = (
            f'<div style="height:2px;width:32px;'
            f'background:linear-gradient(to right,{color},{next_color})"></div>'
            if i < len(steps) - 1 else ""
        )
        html += f"""
        <div style="display:flex;align-items:center">
            <div style="background:{color}20;border:1.5px solid {color};border-radius:10px;
                        padding:7px 16px;text-align:center;min-width:120px">
                <div style="font-size:11px;color:{color};font-weight:700;white-space:nowrap">{name}</div>
                <div style="font-size:10px;color:#9ca3af;margin-top:3px;white-space:nowrap">{status}</div>
            </div>
            {connector}
        </div>"""
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)


# ================================================================
# SOP STEPS RENDERER  (Steps + SLA + Cost Impact)
# ================================================================
def render_sop(suggestion: str):
    if not suggestion:
        st.info("No SOP suggestion available")
        return

    lines      = [l.strip() for l in suggestion.strip().split("\n") if l.strip()]
    steps      = []
    sla_line   = ""
    cost_line  = ""

    for line in lines:
        ll = line.lower()
        if any(k in ll for k in ["sla", "resolution time", "response time"]):
            sla_line = line
        elif any(k in ll for k in ["cost", "penalty", "₹", "$", "breach"]):
            cost_line = line
        else:
            steps.append(line)

    # Steps
    st.markdown("**📋 Recommended SOP Steps:**")
    for i, step in enumerate(steps, 1):
        clean = step.lstrip("0123456789.-) ").strip()
        if clean:
            st.markdown(
                f'<div style="padding:4px 0 4px 12px;border-left:3px solid #3b82f6;margin:4px 0">'
                f'<b>{i}.</b> {clean}</div>',
                unsafe_allow_html=True
            )

    # SLA + Cost row
    if sla_line or cost_line:
        st.markdown("")
        c1, c2 = st.columns(2)
        if sla_line:
            c1.success(f"⏱️ **SLA Rule:** {sla_line.lstrip('SLAsla: -').strip()}")
        if cost_line:
            c2.error(f"💰 **Cost / Penalty:** {cost_line.lstrip('Costcost: -').strip()}")


# ================================================================
# SIDEBAR
# ================================================================
st.sidebar.title("⚙️ Controls")

auto_mode = st.sidebar.toggle(
    "🤖 AI Auto-Execute Mode",
    value=False,
    help="ON = AUTO-FIX tickets are queued automatically. OFF = every ticket needs human approval."
)

st.sidebar.markdown("---")
st.sidebar.markdown("""
**Pipeline Legend**

🟢 **AUTO-FIX** — AI confident, safe to execute  
🟡 **HUMAN-REVIEW** — Needs your sign-off  
🔴 **ESCALATE** — Route to team lead  
🔵 **MONITOR** — Watch, no action yet  
⚫ **REJECTED** — Closed by human  
""")

if auto_mode:
    st.sidebar.success("🤖 Auto-Execute is ON")
else:
    st.sidebar.warning("🧑 Manual approval required for all tickets")

st.sidebar.markdown("---")
if st.sidebar.button("🔄 Refresh Data"):
    st.rerun()


# ================================================================
# HEADER + METRICS
# ================================================================
st.title("🎯 Agentic SLA Dashboard")

df = load_data()
if df.empty:
    st.warning("No tickets found in the database.")
    st.stop()

# Ensure columns exist even if DB not fully migrated
for col in ["final_decision", "requires_human", "approved_by_human",
            "human_executed", "verified", "verification_result",
            "ai_category", "ai_issue", "ai_priority",
            "ai_confidence", "ai_suggestion", "decision_reason",
            "verification_notes", "human_action"]:
    if col not in df.columns:
        df[col] = None

total        = len(df)
auto_fix     = len(df[df["final_decision"] == "AUTO-FIX"])
needs_human  = len(df[(df["requires_human"] == 1) & (df["approved_by_human"].isna())])
escalated    = len(df[df["final_decision"] == "ESCALATE"])
executed     = len(df[df["human_executed"] == 1])
verified_ok  = len(df[df["verification_result"] == "SUCCESS"])

m1, m2, m3, m4, m5, m6 = st.columns(6)
m1.metric("🎫 Total Tickets",  total)
m2.metric("🟢 Auto-Fix",       auto_fix)
m3.metric("🟡 Needs Review",   needs_human)
m4.metric("🔴 Escalated",      escalated)
m5.metric("⚡ Executed",       executed)
m6.metric("🛡️ Verified OK",    verified_ok)

st.markdown("---")


# ================================================================
# FILTERS
# ================================================================
f1, f2, f3 = st.columns(3)
with f1:
    filter_decision = st.selectbox("Filter by Decision", [
        "All", "AUTO-FIX", "HUMAN-REVIEW", "ESCALATE", "MONITOR", "REJECTED", "PENDING"
    ])
with f2:
    filter_stage = st.selectbox("Filter by Stage", [
        "All", "Awaiting Decision", "Needs Human Approval",
        "Awaiting Execution", "Executed", "Verified"
    ])
with f3:
    raw_cats   = sorted([c for c in df["ai_category"].dropna().unique() if c])
    filter_cat = st.selectbox("Filter by AI Category", ["All"] + raw_cats)

filtered = df.copy()

# Decision filter
if filter_decision == "PENDING":
    filtered = filtered[filtered["final_decision"].isna() | (filtered["final_decision"] == "")]
elif filter_decision != "All":
    filtered = filtered[filtered["final_decision"] == filter_decision]

# Stage filter
if filter_stage == "Awaiting Decision":
    filtered = filtered[filtered["final_decision"].isna() | (filtered["final_decision"] == "")]
elif filter_stage == "Needs Human Approval":
    filtered = filtered[(filtered["requires_human"] == 1) & (filtered["approved_by_human"].isna())]
elif filter_stage == "Awaiting Execution":
    filtered = filtered[(filtered["approved_by_human"] == 1) & (filtered["human_executed"].isna())]
elif filter_stage == "Executed":
    filtered = filtered[filtered["human_executed"] == 1]
elif filter_stage == "Verified":
    filtered = filtered[filtered["verified"] == 1]

# Category filter
if filter_cat != "All":
    filtered = filtered[filtered["ai_category"] == filter_cat]

st.markdown(f"**Showing {len(filtered)} of {total} tickets**")
st.markdown("---")


# ================================================================
# TICKET CARDS
# ================================================================
for _, row in filtered.iterrows():
    ticket         = row.to_dict()
    ticket_id      = ticket.get("ticket_id")
    final          = ticket.get("final_decision") or "PENDING"
    requires_human = int(ticket.get("requires_human") or 0)
    approved       = ticket.get("approved_by_human")
    human_exec     = int(ticket.get("human_executed") or 0)
    verified       = ticket.get("verified")
    ver_result     = ticket.get("verification_result") or ""
    ver_notes      = ticket.get("verification_notes") or ""
    confidence     = ticket.get("ai_confidence")
    ai_pri         = ticket.get("ai_priority") or ""

    STATUS_ICON = {
        "AUTO-FIX":     "🟢",
        "ESCALATE":     "🔴",
        "HUMAN-REVIEW": "🟡",
        "REJECTED":     "⚫",
        "MONITOR":      "🔵",
        "PENDING":      "⏳",
    }
    icon = STATUS_ICON.get(final, "⏳")

    # Auto-expand if action is needed
    expand = (
        (requires_human == 1 and approved is None) or
        (approved == 1 and not human_exec) or
        (human_exec == 1 and not verified)
    )

    with st.expander(
        f"{icon}  #{ticket_id} — {ticket.get('subject', 'No Subject')}",
        expanded=expand
    ):

        # ── Pipeline Chain ──────────────────────────────────────
        render_pipeline(ticket)
        st.markdown("---")

        # ── Decision Badge + Confidence ─────────────────────────
        top1, top2 = st.columns([4, 1])
        with top1:
            st.markdown(
                badge(final, DECISION_COLOR.get(final, "#9ca3af")) +
                "&nbsp;&nbsp;" +
                (badge(ai_pri, PRIORITY_COLOR.get(ai_pri, "#9ca3af")) if ai_pri else ""),
                unsafe_allow_html=True
            )
            st.markdown("")
            if ticket.get("decision_reason"):
                st.caption(f"📋 Decision Reason: {ticket.get('decision_reason')}")
        with top2:
            if confidence is not None:
                try:
                    st.metric("AI Confidence", f"{float(confidence):.0%}")
                except Exception:
                    pass

        st.markdown("---")

        # ── Ticket Info ─────────────────────────────────────────
        i1, i2, i3, i4 = st.columns(4)
        i1.markdown(f"**🏢 Team**  \n{ticket.get('helpdesk_team', '—')}")
        i2.markdown(f"**👤 Assigned**  \n{ticket.get('assigned_to', '—')}")
        i3.markdown(f"**🧑 Customer**  \n{ticket.get('customer', '—')}")
        i4.markdown(f"**📞 Phone**  \n{ticket.get('phone', '—')}")

        st.markdown(f"**📝 Description:** {ticket.get('description', '—')}")
        st.markdown(
            f"**Priority:** {stars(ticket.get('priority'))} &nbsp;&nbsp;"
            f"**Created:** {ticket.get('created_at', '—')}"
        )

        # ── AI Analysis ─────────────────────────────────────────
        if ticket.get("ai_issue"):
            st.markdown("---")
            st.markdown("#### 🤖 AI Analysis")

            a1, a2, a3 = st.columns(3)
            a1.markdown(f"**🔍 Root Issue**  \n{ticket.get('ai_issue', '—')}")
            a2.markdown(f"**📂 Category**  \n{ticket.get('ai_category', '—')}")
            a3.markdown(f"**⚡ AI Priority**  \n{ai_pri or '—'}")

            st.markdown("---")
            render_sop(ticket.get("ai_suggestion", ""))

        # ── Verification Result ─────────────────────────────────
        if verified is not None:
            st.markdown("---")
            st.markdown("#### 🛡️ Verification Result")
            if ver_result == "SUCCESS":
                st.success(f"✅ **SUCCESS** — {ver_notes}")
            else:
                st.warning(f"⚠️ **Needs Attention** — {ver_notes}")

        # ── Action Section ──────────────────────────────────────
        st.markdown("---")

        if final == "REJECTED":
            st.error("❌ Ticket rejected and closed by human")

        elif final == "ESCALATE":
            st.error("🚨 Escalated to Team Lead — awaiting senior action")
            if st.button("✅ Override & Approve Manually", key=f"override_{ticket_id}"):
                save_approval(ticket_id, "APPROVED")
                st.rerun()

        elif human_exec and verified == 1:
            if ver_result == "SUCCESS":
                st.success("🎉 Ticket fully resolved and verified — pipeline complete")
            else:
                st.warning("⚠️ Verification flagged issues — please review the notes above")

        elif human_exec and not verified:
            st.info("🛡️ Verification Agent is running checks on this ticket…")
            st.caption("This will update automatically on next sync cycle")

        elif approved == 1 and not human_exec:
            st.warning(
                "🧑 **Your turn to execute** — follow the SOP steps listed above, "
                "then click the button below when done"
            )
            col_exec, _ = st.columns([2, 3])
            with col_exec:
                if st.button(
                    "✅ Mark as Executed (I've completed the steps)",
                    key=f"exec_{ticket_id}",
                    type="primary"
                ):
                    mark_executed(ticket_id)
                    st.success("✅ Marked as executed — Verification Agent will now validate")
                    st.rerun()

        elif requires_human == 1 and approved is None:
            st.warning("⚠️ **Human approval required** before this ticket proceeds to Execution")
            b1, b2, b3 = st.columns(3)
            with b1:
                if st.button(
                    "✅ Approve & Assign to Me",
                    key=f"approve_{ticket_id}",
                    type="primary"
                ):
                    save_approval(ticket_id, "APPROVED")
                    st.rerun()
            with b2:
                if st.button("❌ Reject & Close", key=f"reject_{ticket_id}"):
                    save_approval(ticket_id, "REJECTED")
                    st.rerun()
            with b3:
                if st.button("🚨 Escalate to Team Lead", key=f"escalate_{ticket_id}"):
                    save_approval(ticket_id, "ESCALATED")
                    st.rerun()

        elif auto_mode and final == "AUTO-FIX" and not requires_human:
            st.success(
                "🤖 **Auto-Execute Mode is ON** — this ticket has been queued "
                "for the Execution Agent automatically"
            )

        elif final == "AUTO-FIX" and not auto_mode:
            st.info(
                "🤖 AI recommends **AUTO-FIX** — "
                "enable Auto-Execute in the sidebar to run automatically, or approve manually below"
            )
            col_m, _ = st.columns([2, 3])
            with col_m:
                if st.button(
                    "✅ Approve & Execute Manually",
                    key=f"manual_{ticket_id}",
                    type="primary"
                ):
                    save_approval(ticket_id, "APPROVED")
                    st.rerun()

        elif final == "MONITOR":
            st.info("🔵 **Monitoring** — no action required at this time")

        elif final == "PENDING":
            st.info("⏳ Waiting for Classifier and Decision agents to process this ticket…")

        st.caption(f"Ticket ID: {ticket_id} &nbsp;|&nbsp; Updated: {ticket.get('updated_at', '—')}")