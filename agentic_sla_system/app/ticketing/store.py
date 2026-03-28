from app.db.database import conn
from app.utils.logger import get_logger

logger = get_logger()

def upsert_ticket(t):
    logger.info(f"Upserting ticket {t['ticket_id']}")

    conn.execute("""
    INSERT INTO tickets (
        ticket_id, subject, company, category, team,
        helpdesk_team, assigned_to, customer, phone, description,
        priority, status, assigned,
        created_at, updated_at
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)

    ON CONFLICT(ticket_id) DO UPDATE SET
        subject=excluded.subject,
        helpdesk_team=excluded.helpdesk_team,
        assigned_to=excluded.assigned_to,
        customer=excluded.customer,
        phone=excluded.phone,
        description=excluded.description,
        priority=excluded.priority,
        updated_at=excluded.updated_at
    """, (
        t["ticket_id"], t["subject"], t["company"], t["category"], t["team"],
        t["helpdesk_team"], t["assigned_to"], t["customer"], t["phone"], t["description"],
        t["priority"], t["status"], t["assigned"],
        t["created_at"], t["updated_at"]
    ))

    conn.commit()
    logger.info(f"Ticket {t['ticket_id']} stored successfully")