import streamlit as st
import sqlite3
import pandas as pd
import os

# ================================================================
# CONFIG
# ================================================================
st.set_page_config(page_title="Ticket Viewer", layout="wide")

DB_PATH = os.path.abspath("tickets.db")

# ================================================================
# THEME
# ================================================================
theme = st.radio("Theme", ["Light", "Dark"], horizontal=True)

if theme == "Dark":
    bg      = "#0e1117"
    card    = "#161b22"
    border  = "#30363d"
    text    = "#e6edf3"
    muted   = "#8b949e"
    abg     = "#1c2128"
    aborder = "#6366f1"
else:
    bg      = "#f5f6fa"
    card    = "#ffffff"
    border  = "#e5e7eb"
    text    = "#111827"
    muted   = "#6b7280"
    abg     = "#f9fafb"
    aborder = "#6366f1"

st.markdown(f"""
<style>
.stApp, .block-container {{ background-color: {bg}; color: {text}; }}
.stApp p, .stApp div, .stApp span, .stApp label {{ color: {text}; }}

.tk-card {{
    background: {card};
    border: 1px solid {border};
    border-radius: 10px;
    padding: 18px 20px;
    margin-bottom: 14px;
}}
.tk-header {{
    display: flex;
    align-items: center;
    gap: 10px;
    flex-wrap: wrap;
    margin-bottom: 12px;
}}
.tk-id {{
    font-size: 12px;
    font-weight: 700;
    color: {muted};
    white-space: nowrap;
}}
.tk-subject {{
    font-size: 15px;
    font-weight: 700;
    color: {text};
    flex: 1;
}}
.tk-grid {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 10px 24px;
    margin-bottom: 12px;
}}
.tk-grid-3 {{
    display: grid;
    grid-template-columns: 1fr 1fr 1fr;
    gap: 10px 24px;
    margin-bottom: 12px;
}}
.tk-label {{
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: {muted};
    margin-bottom: 2px;
}}
.tk-value {{
    font-size: 13px;
    color: {text};
    line-height: 1.5;
}}
.tk-sep {{
    border: none;
    border-top: 1px solid {border};
    margin: 10px 0;
}}
.badge {{
    display: inline-block;
    font-size: 11px;
    font-weight: 600;
    padding: 3px 10px;
    border-radius: 999px;
    white-space: nowrap;
}}
.b-escalate  {{ background:#fee2e2; color:#991b1b; }}
.b-monitor   {{ background:#dbeafe; color:#1e40af; }}
.b-autofix   {{ background:#d1fae5; color:#065f46; }}
.b-human     {{ background:#fef3c7; color:#92400e; }}
.b-other     {{ background:#f3f4f6; color:#374151; }}
.b-critical  {{ background:#fee2e2; color:#991b1b; }}
.b-high      {{ background:#ffedd5; color:#9a3412; }}
.b-medium    {{ background:#dbeafe; color:#1e40af; }}
.b-low       {{ background:#d1fae5; color:#065f46; }}
.b-neutral   {{ background:#f3f4f6; color:#374151; border:1px solid #e5e7eb; }}
.conf-wrap   {{ display:flex; align-items:center; gap:6px; }}
.conf-track  {{ width:80px; height:6px; background:{border}; border-radius:3px; overflow:hidden; }}
.ai-block {{
    background: {abg};
    border-left: 3px solid {aborder};
    border-radius: 0 8px 8px 0;
    padding: 10px 14px;
    font-size: 13px;
    color: {text};
    line-height: 1.7;
    white-space: pre-wrap;
    margin-top: 4px;
}}
.step-row {{
    display: flex;
    gap: 10px;
    padding: 5px 0;
    border-bottom: 1px solid {border};
    font-size: 13px;
    color: {text};
}}
.step-num {{
    font-size: 11px;
    font-weight: 700;
    color: {muted};
    min-width: 18px;
    padding-top: 1px;
}}
.sla-box {{
    background: {abg};
    border: 1px solid {border};
    border-radius: 8px;
    padding: 8px 12px;
}}
.tk-footer {{
    font-size: 11px;
    color: {muted};
    margin-top: 8px;
}}
</style>
""", unsafe_allow_html=True)


# ================================================================
# HELPERS
# ================================================================
def safe(val) -> str:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return "—"
    s = str(val).strip()
    if not s or s.lower() in ("none", "nan"):
        return "—"
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def decision_badge(d: str) -> str:
    cls = {"ESCALATE": "b-escalate", "MONITOR": "b-monitor",
           "AUTO-FIX": "b-autofix", "HUMAN-REVIEW": "b-human"}.get(d, "b-other")
    return f'<span class="badge {cls}">{d}</span>'


def priority_badge(p: str) -> str:
    cls = {"Critical": "b-critical", "High": "b-high",
           "Medium": "b-medium", "Low": "b-low"}.get(p, "b-neutral")
    return f'<span class="badge {cls}">{p}</span>'


def conf_html(conf: float) -> str:
    pct = int(conf * 100)
    color = "#10b981" if conf >= 0.85 else "#f59e0b" if conf >= 0.60 else "#ef4444"
    return (
        f'<div class="conf-wrap">'
        f'<div class="conf-track"><div style="width:{pct}%;height:100%;'
        f'background:{color};border-radius:3px;"></div></div>'
        f'<span style="font-size:12px;color:{muted};">{pct}%</span>'
        f'</div>'
    )


def steps_html(suggestion: str) -> str:
    if suggestion == "—":
        return f'<p style="font-size:13px;color:{muted};">No steps available.</p>'
    lines = [s.strip() for s in suggestion.replace("\\n", "\n").split("\n") if s.strip()]
    if not lines:
        return f'<p style="font-size:13px;color:{muted};">No steps available.</p>'
    out = ""
    for i, line in enumerate(lines, 1):
        text = line.lstrip("0123456789. ").strip()
        out += f'<div class="step-row"><span class="step-num">{i}</span><span>{text}</span></div>'
    return out


# ================================================================
# DB
# ================================================================
def load_data() -> pd.DataFrame:
    if not os.path.exists(DB_PATH):
        st.error(f"Database not found: `{DB_PATH}`")
        st.stop()
    try:
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql_query("SELECT * FROM tickets ORDER BY updated_at DESC", conn)
        conn.close()
    except Exception as e:
        st.error(f"DB error: {e}")
        st.stop()

    for col in ["ticket_id", "subject", "description", "helpdesk_team", "priority",
                "ai_issue", "ai_category", "ai_priority", "ai_confidence",
                "ai_suggestion", "ai_sla_rule", "ai_breach_penalty",
                "ai_answer", "ai_decision", "updated_at"]:
        if col not in df.columns:
            df[col] = None
    return df


# ================================================================
# MAIN
# ================================================================
st.title("🎫 Ticket Viewer")

df = load_data()
if df.empty:
    st.warning("No tickets found.")
    st.stop()

# ── Metrics ──────────────────────────────────────────────────────
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("🎫 Total",       len(df))
c2.metric("✅ Classified",  int(df["ai_decision"].notna().sum()))
c3.metric("🚨 Escalate",    int((df["ai_decision"] == "ESCALATE").sum()))
c4.metric("👁 Monitor",     int((df["ai_decision"] == "MONITOR").sum()))
c5.metric("🧑 Human",       int((df["ai_decision"] == "HUMAN-REVIEW").sum()))

st.markdown("---")

# ── Filters ──────────────────────────────────────────────────────
f1, f2, f3 = st.columns(3)
with f1:
    dec_opts = ["All"] + sorted([d for d in df["ai_decision"].dropna().unique() if d])
    f_dec = st.selectbox("Decision", dec_opts)
with f2:
    cat_opts = ["All"] + sorted([c for c in df["ai_category"].dropna().unique() if c])
    f_cat = st.selectbox("Category", cat_opts)
with f3:
    f_pri = st.selectbox("AI Priority", ["All", "Critical", "High", "Medium", "Low"])

filtered = df.copy()
if f_dec != "All": filtered = filtered[filtered["ai_decision"] == f_dec]
if f_cat != "All": filtered = filtered[filtered["ai_category"] == f_cat]
if f_pri != "All": filtered = filtered[filtered["ai_priority"] == f_pri]

st.markdown(
    f'<p style="font-size:13px;color:{muted};">Showing <strong>{len(filtered)}</strong>'
    f' of <strong>{len(df)}</strong> tickets</p>',
    unsafe_allow_html=True
)
st.markdown("---")

if filtered.empty:
    st.info("No tickets match the selected filters.")
    st.stop()

# ── Ticket Cards ─────────────────────────────────────────────────
for _, row in filtered.iterrows():
    tid    = safe(row.get("ticket_id"))
    subj   = safe(row.get("subject"))
    desc   = safe(row.get("description"))
    team   = safe(row.get("helpdesk_team"))
    pri    = safe(row.get("priority"))
    ai_cat = safe(row.get("ai_category"))
    ai_pri = safe(row.get("ai_priority"))
    ai_iss = safe(row.get("ai_issue"))
    ai_dec = safe(row.get("ai_decision"))
    ai_sla = safe(row.get("ai_sla_rule"))
    ai_pen = safe(row.get("ai_breach_penalty"))
    ai_ans = safe(row.get("ai_answer")).replace("\\n", "\n")
    ai_sug = safe(row.get("ai_suggestion"))
    upd    = safe(row.get("updated_at"))

    try:
        conf = float(row.get("ai_confidence") or 0.0)
    except Exception:
        conf = 0.0

    st.markdown(f"""
<div class="tk-card">

  <!-- ── HEADER ── -->
  <div class="tk-header">
    <span class="tk-id">#{tid}</span>
    <span class="tk-subject">{subj}</span>
    {decision_badge(ai_dec)}&nbsp;{priority_badge(ai_pri)}&nbsp;
    <span class="badge b-neutral">{ai_cat}</span>&nbsp;
    {conf_html(conf)}
  </div>

  <hr class="tk-sep">

  <!-- ── ROW 1: Ticket basics ── -->
  <div class="tk-grid">
    <div>
      <div class="tk-label">Description</div>
      <div class="tk-value">{desc}</div>
    </div>
    <div>
      <div class="tk-label">Helpdesk Team</div>
      <div class="tk-value">{team}</div>
    </div>
  </div>

  <hr class="tk-sep">

  <!-- ── ROW 2: AI classification ── -->
  <div class="tk-grid-3">
    <div>
      <div class="tk-label">AI Root Issue</div>
      <div class="tk-value">{ai_iss}</div>
    </div>
    <div>
      <div class="tk-label">AI Category</div>
      <div class="tk-value">{ai_cat}</div>
    </div>
    <div>
      <div class="tk-label">Ticket Priority</div>
      <div class="tk-value">{pri}</div>
    </div>
  </div>

  <hr class="tk-sep">

  <!-- ── ROW 3: SLA ── -->
  <div class="tk-grid">
    <div class="sla-box">
      <div class="tk-label">SLA Rule</div>
      <div class="tk-value">{ai_sla}</div>
    </div>
    <div class="sla-box">
      <div class="tk-label">Breach Penalty</div>
      <div class="tk-value">{ai_pen}</div>
    </div>
  </div>

  <hr class="tk-sep">

  <!-- ── AI Suggestion Steps ── -->
  <div class="tk-label" style="margin-bottom:6px;">AI Suggestion Steps</div>
  {steps_html(ai_sug)}

  <hr class="tk-sep">

  <!-- ── AI Analysis ── -->
  <div class="tk-label" style="margin-bottom:6px;">AI Analysis</div>
  <div class="ai-block">{ai_ans}</div>

  <div class="tk-footer">Last updated: {upd}</div>

</div>
""", unsafe_allow_html=True)