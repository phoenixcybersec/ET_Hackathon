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

# Gradient presets for grad_badge: index → CSS gradient
GRAD_PRESETS = [
    "linear-gradient(135deg,#f09433,#e6683c)",   # 0 – warm orange
    "linear-gradient(135deg,#dc2743,#cc2366)",   # 1 – crimson-pink
    "linear-gradient(135deg,#5851db,#833ab4)",   # 2 – indigo-purple
    "linear-gradient(135deg,#667eea,#764ba2)",   # 3 – blue-purple
    "linear-gradient(135deg,#00b09b,#96c93d)",   # 4 – teal-green
    "linear-gradient(135deg,#f77062,#fe5196)",   # 5 – coral-pink
]

CATEGORY_GRAD = {
    "Network":      0,
    "Hardware":     1,
    "Software":     2,
    "Security":     3,
    "Access":       4,
    "Performance":  5,
}

PRIORITY_GRAD = {
    "Critical": 1,
    "High":     0,
    "Medium":   2,
    "Low":      4,
}

def grad_badge(label: str, preset_index: int) -> str:
    grad = GRAD_PRESETS[preset_index % len(GRAD_PRESETS)]
    return (
        f'<span style="background:{grad};color:#fff;padding:5px 14px;'
        f'border-radius:20px;font-size:12px;font-weight:700;'
        f'letter-spacing:0.4px;display:inline-block;box-shadow:0 2px 6px rgba(0,0,0,.15)">'
        f'{label}</span>'
    )

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
# AI ANALYSIS SECTION  (gradient card style — RAG-powered)
# ================================================================
def render_ai_section(ticket):
    ai_issue    = ticket.get("ai_issue")
    ai_answer   = ticket.get("ai_answer")
    ai_sla      = ticket.get("ai_sla_rule")
    ai_penalty  = ticket.get("ai_breach_penalty")
    ai_suggest  = ticket.get("ai_suggestion")
    confidence  = ticket.get("ai_confidence")
    ai_category = ticket.get("ai_category", "")
    ai_priority = ticket.get("ai_priority", "")

    if not ai_issue:
        st.markdown(
            '<div style="background:#fafafa;border:1px dashed #dbdbdb;border-radius:12px;'
            'padding:20px;color:#8e8e8e;text-align:center">⏳ AI analysis pending...</div>',
            unsafe_allow_html=True
        )
        return

    # ── Badges ──────────────────────────────────────────────────
    badges = ""
    if ai_category:
        badges += grad_badge(ai_category, CATEGORY_GRAD.get(ai_category, 0)) + "&nbsp;"
    if ai_priority:
        badges += grad_badge(ai_priority, PRIORITY_GRAD.get(ai_priority, 1)) + "&nbsp;"
    if confidence is not None:
        try:
            pct = int(float(confidence) * 100)
            badges += grad_badge(f"🎯 {pct}% confidence", 2)
        except Exception:
            pass
    st.markdown(badges, unsafe_allow_html=True)
    st.markdown("")

    # ── Root Issue ───────────────────────────────────────────────
    st.markdown(
        f'<div style="background:linear-gradient(135deg,#ffecd2,#fcb69f);'
        f'border-radius:14px;padding:14px 18px;margin:6px 0">'
        f'<div style="font-size:11px;font-weight:700;color:#c0392b;margin-bottom:4px">🔍 ROOT ISSUE</div>'
        f'<div style="font-size:15px;font-weight:600;color:#262626">{ai_issue}</div>'
        f'</div>',
        unsafe_allow_html=True
    )

    # ── LLM Full Answer ─────────────────────────────────────────
    if ai_answer:
        st.markdown(
            f'<div style="background:linear-gradient(135deg,#e0f7fa,#e8f5e9);'
            f'border-radius:14px;padding:16px 20px;margin:8px 0">'
            f'<div style="font-size:11px;font-weight:700;color:#00796b;margin-bottom:8px">🤖 AI ANALYSIS & RECOMMENDATION</div>'
            f'<div style="font-size:14px;color:#262626;line-height:1.7">{ai_answer.replace(chr(10), "<br>")}</div>'
            f'</div>',
            unsafe_allow_html=True
        )

    # ── SOP Steps ───────────────────────────────────────────────
    if ai_suggest and ai_suggest != "—":
        st.markdown(
            '<div style="font-size:11px;font-weight:700;color:#5851db;margin:12px 0 6px 0">'
            '📋 SOP STEPS FROM KNOWLEDGE BASE</div>',
            unsafe_allow_html=True
        )
        lines = [l.strip() for l in ai_suggest.strip().split("\n") if l.strip()]
        for i, line in enumerate(lines, 1):
            clean = line.lstrip("0123456789.-) ").strip()
            if clean:
                colors = ["#f09433","#e6683c","#dc2743","#cc2366","#bc1888","#5851db"]
                c = colors[(i - 1) % len(colors)]
                st.markdown(
                    f'<div style="display:flex;align-items:flex-start;gap:10px;'
                    f'padding:8px 12px;margin:4px 0;border-radius:10px;background:#fafafa;'
                    f'border-left:3px solid {c}">'
                    f'<span style="color:{c};font-weight:800;min-width:20px">{i}.</span>'
                    f'<span style="color:#262626;font-size:13px">{clean}</span>'
                    f'</div>',
                    unsafe_allow_html=True
                )

    # ── SLA + Penalty ────────────────────────────────────────────
    if ai_sla or ai_penalty:
        s1, s2 = st.columns(2)
        if ai_sla:
            s1.markdown(
                f'<div style="background:linear-gradient(135deg,#667eea,#764ba2);'
                f'border-radius:14px;padding:14px 18px;color:#fff">'
                f'<div style="font-size:10px;opacity:0.8;margin-bottom:4px">⏱️ SLA RULE</div>'
                f'<div style="font-size:14px;font-weight:700">{ai_sla}</div>'
                f'</div>',
                unsafe_allow_html=True
            )
        if ai_penalty:
            s2.markdown(
                f'<div style="background:linear-gradient(135deg,#f77062,#fe5196);'
                f'border-radius:14px;padding:14px 18px;color:#fff">'
                f'<div style="font-size:10px;opacity:0.8;margin-bottom:4px">💰 BREACH PENALTY</div>'
                f'<div style="font-size:22px;font-weight:800">{ai_penalty}</div>'
                f'</div>',
                unsafe_allow_html=True
            )


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
            "verification_notes", "human_action",
            "ai_answer", "ai_sla_rule", "ai_breach_penalty"]:
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

        # ── AI Analysis (gradient card style) ───────────────────
        st.markdown("---")
        st.markdown("#### 🤖 AI Analysis")
        render_ai_section(ticket)

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