from app.db.database import get_connection
from app.utils.logger import get_logger

logger = get_logger()

# ── Thresholds ────────────────────────────────────────────────────
CONFIDENCE_THRESHOLD = 0.85

# These categories always need human sign-off
SLA_CRITICAL_CATEGORIES = ["Network", "Access"]

# These issue keywords are always routed to execution agent
# regardless of confidence score — infrastructure auto-remediation
INFRA_AUTOFIX_KEYWORDS = [
    "ram", "memory", "mem", "high memory", "oom",          # RAM
    "storage", "disk", "volume", "ebs", "space",           # Storage
    "pod", "resource", "request", "kubectl",               # Kubernetes
    "kubernetes", "minikube", "cpu throttl",
]


def _is_infra_ticket(ticket: dict) -> bool:
    """Returns True if ticket is one of the 3 infrastructure issue types."""
    issue = (ticket.get("ai_issue") or "").lower()
    subject = (ticket.get("subject") or "").lower()
    description = (ticket.get("description") or "").lower()
    combined = f"{issue} {subject} {description}"
    return any(k in combined for k in INFRA_AUTOFIX_KEYWORDS)


def decide(ticket: dict) -> dict:
    ticket_id     = ticket.get("ticket_id")
    ai_decision   = ticket.get("ai_decision", "HUMAN-REVIEW")
    ai_confidence = float(ticket.get("ai_confidence") or 0.0)
    ai_category   = ticket.get("ai_category", "Other")
    ai_priority   = ticket.get("ai_priority", "Medium")

    # ── Rule 1: Infrastructure tickets → always AUTO-FIX ─────────
    # RAM / Storage / Pod resource issues bypass confidence threshold
    # and go directly to execution agent
    if _is_infra_ticket(ticket):
        final_decision = "AUTO-FIX"
        reason = (
            f"Infrastructure issue detected — forced AUTO-FIX "
            f"(confidence: {ai_confidence}, bypassed threshold)"
        )

    # ── Rule 2: Critical priority → always escalate ───────────────
    elif ai_priority == "Critical":
        final_decision = "ESCALATE"
        reason = "Critical priority — always escalate"

    # ── Rule 3: High confidence + safe category → AUTO-FIX ───────
    elif (
        ai_confidence >= CONFIDENCE_THRESHOLD
        and ai_decision == "AUTO-FIX"
        and ai_category not in SLA_CRITICAL_CATEGORIES
    ):
        final_decision = "AUTO-FIX"
        reason = f"High confidence ({ai_confidence}) — safe to auto-fix"

    # ── Rule 4: High confidence but critical category → human ─────
    elif ai_confidence >= CONFIDENCE_THRESHOLD and ai_category in SLA_CRITICAL_CATEGORIES:
        final_decision = "HUMAN-REVIEW"
        reason = f"Category '{ai_category}' requires human sign-off despite high confidence"

    # ── Rule 5: Low confidence → human review ────────────────────
    elif ai_confidence < CONFIDENCE_THRESHOLD:
        final_decision = "HUMAN-REVIEW"
        reason = f"Low confidence ({ai_confidence}) — needs human review"

    # ── Rule 6: Fallback → pass through classifier decision ───────
    else:
        final_decision = ai_decision
        reason = "Passed through classifier decision"

    logger.info(
        f"Ticket {ticket_id} → final_decision: {final_decision} | reason: {reason}"
    )

    return {
        "ticket_id":      ticket_id,
        "final_decision": final_decision,
        "decision_reason": reason,
        "requires_human": final_decision in ("HUMAN-REVIEW", "ESCALATE"),
    }


# ── Save decision ─────────────────────────────────────────────────
def save_decision(ticket_id: str, result: dict):
    conn = get_connection()
    conn.execute("""
        UPDATE tickets SET
            final_decision  = ?,
            decision_reason = ?,
            requires_human  = ?
        WHERE ticket_id = ?
    """, (
        result["final_decision"],
        result["decision_reason"],
        1 if result["requires_human"] else 0,
        ticket_id,
    ))
    conn.commit()


# ── Batch run ─────────────────────────────────────────────────────
def run_decision_agent():
    conn = get_connection()
    rows = conn.execute("""
        SELECT * FROM tickets
        WHERE ai_decision IS NOT NULL
        AND (final_decision IS NULL OR final_decision = '')
    """).fetchall()

    logger.info(f"Decision agent processing {len(rows)} tickets")

    for row in rows:
        ticket = dict(row)
        result = decide(ticket)
        save_decision(ticket["ticket_id"], result)