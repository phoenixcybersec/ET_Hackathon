from app.db.database import get_connection
from app.utils.logger import get_logger

logger = get_logger()

def verify_ticket(ticket: dict) -> dict:
    ticket_id = ticket.get("ticket_id")
    final     = ticket.get("final_decision", "")
    category  = ticket.get("ai_category", "")
    priority  = ticket.get("ai_priority", "Medium")

    # Simple rule-based verification for now
    # Execution Agent will plug real checks here later
    issues = []

    if not ticket.get("ai_suggestion"):
        issues.append("No SOP was followed — suggestion missing")
    if not ticket.get("assigned_to"):
        issues.append("Ticket not assigned to any agent")
    if priority == "Critical" and final != "ESCALATE":
        issues.append("Critical ticket was not escalated")

    verified  = len(issues) == 0
    result    = "SUCCESS" if verified else "NEEDS_ATTENTION"
    notes     = " | ".join(issues) if issues else f"All checks passed for {category} ticket"

    logger.info(f"Verification ticket {ticket_id} → {result}: {notes}")

    return {
        "ticket_id":           ticket_id,
        "verification_result": result,
        "verification_notes":  notes,
        "verified":            1 if verified else 0,
    }


def save_verification(ticket_id: str, result: dict):
    conn = get_connection()
    conn.execute("""
        UPDATE tickets SET
            verification_result = ?,
            verification_notes  = ?,
            verified            = ?
        WHERE ticket_id = ?
    """, (
        result["verification_result"],
        result["verification_notes"],
        result["verified"],
        ticket_id,
    ))
    conn.commit()


def run_verification_agent():
    conn = get_connection()
    # Run on tickets marked as humanly executed but not yet verified
    rows = conn.execute("""
        SELECT * FROM tickets
        WHERE human_executed = 1
        AND (verified IS NULL OR verified = '')
    """).fetchall()

    logger.info(f"Verification agent processing {len(rows)} tickets")
    for row in rows:
        ticket = dict(row)
        result = verify_ticket(ticket)
        save_verification(ticket["ticket_id"], result)