from app.db.database import get_connection
from app.utils.logger import get_logger

logger = get_logger()

# ---------------- DECISION RULES ---------------- #
CONFIDENCE_THRESHOLD = 0.85  # above this → AUTO-FIX, below → HUMAN-REVIEW

SLA_CRITICAL_CATEGORIES = ["Network", "Access"]  # always escalate these unless very high confidence

def decide(ticket: dict) -> dict:
    ticket_id = ticket.get("ticket_id")
    ai_decision = ticket.get("ai_decision", "HUMAN-REVIEW")
    ai_confidence = float(ticket.get("ai_confidence") or 0.0)
    ai_category = ticket.get("ai_category", "Other")
    ai_priority = ticket.get("ai_priority", "Medium")

    # ---------------- DECISION LOGIC ---------------- #
    if ai_priority == "Critical":
        final_decision = "ESCALATE"
        reason = "Critical priority — always escalate"

    elif ai_confidence >= CONFIDENCE_THRESHOLD and ai_decision == "AUTO-FIX" and ai_category not in SLA_CRITICAL_CATEGORIES:
        final_decision = "AUTO-FIX"
        reason = f"High confidence ({ai_confidence}) — safe to auto-fix"

    elif ai_confidence >= CONFIDENCE_THRESHOLD and ai_category in SLA_CRITICAL_CATEGORIES:
        final_decision = "HUMAN-REVIEW"
        reason = f"Category '{ai_category}' requires human sign-off despite high confidence"

    elif ai_confidence < CONFIDENCE_THRESHOLD:
        final_decision = "HUMAN-REVIEW"
        reason = f"Low confidence ({ai_confidence}) — needs human review"

    else:
        final_decision = ai_decision
        reason = "Passed through classifier decision"

    logger.info(f"Ticket {ticket_id} → final_decision: {final_decision} | reason: {reason}")

    return {
        "ticket_id": ticket_id,
        "final_decision": final_decision,
        "decision_reason": reason,
        "requires_human": final_decision in ("HUMAN-REVIEW", "ESCALATE")
    }


# ---------------- SAVE DECISION ---------------- #
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
        ticket_id
    ))
    conn.commit()


# ---------------- BATCH DECIDE ---------------- #
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