from app.db.connection import get_connection

def save_ticket(ticket):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    INSERT OR IGNORE INTO tickets (id, title, description, stage)
    VALUES (?, ?, ?, ?)
    """, (
        ticket["id"],
        ticket["name"],
        ticket.get("description", ""),
        str(ticket.get("stage_id"))
    ))

    conn.commit()
    conn.close()