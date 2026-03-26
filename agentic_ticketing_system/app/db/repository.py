from app.db.connection import get_connection


def save_ticket(ticket):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    INSERT OR IGNORE INTO tickets (id, title, description, stage, assigned_to)
    VALUES (?, ?, ?, ?, ?)
    """, (
        ticket["id"],
        ticket["title"],
        ticket["description"],
        ticket["stage"],
        ticket["assigned_to"]
    ))

    conn.commit()
    conn.close()