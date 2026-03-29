from app.db.database import get_connection


def company_summary():
    conn = get_connection()
    return conn.execute("""
        SELECT company,
               COUNT(*)                                        AS total,
               SUM(CASE WHEN status = 'open'   THEN 1 ELSE 0 END) AS open,
               SUM(CASE WHEN assigned = 0      THEN 1 ELSE 0 END) AS unassigned,
               SUM(CASE WHEN priority = 3      THEN 1 ELSE 0 END) AS urgent
        FROM tickets
        GROUP BY company
    """).fetchall()


def category_summary():
    conn = get_connection()
    return conn.execute("""
        SELECT category,
               COUNT(*)                                        AS total,
               SUM(CASE WHEN priority = 3      THEN 1 ELSE 0 END) AS urgent
        FROM tickets
        GROUP BY category
    """).fetchall()


def all_tickets():
    conn = get_connection()
    return conn.execute("SELECT * FROM tickets").fetchall()


def pending_tickets():
    """Returns tickets not yet classified — used by classifier batch loop."""
    conn = get_connection()
    return conn.execute("""
        SELECT * FROM tickets
        WHERE is_classified = 0 OR is_classified IS NULL
    """).fetchall()


def executed_tickets():
    """Returns tickets where execution agent has run."""
    conn = get_connection()
    return conn.execute("""
        SELECT * FROM tickets
        WHERE execution_status IS NOT NULL
    """).fetchall()


def failed_executions():
    """Returns tickets where execution agent failed — for alerting/review."""
    conn = get_connection()
    return conn.execute("""
        SELECT * FROM tickets
        WHERE execution_status = 'EXECUTION_FAILED'
    """).fetchall()


def get_ticket_by_id(ticket_id: str):
    conn = get_connection()
    return conn.execute(
        "SELECT * FROM tickets WHERE ticket_id = ?", (ticket_id,)
    ).fetchone()