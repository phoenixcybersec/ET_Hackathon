from app.db.database import conn

def company_summary():
    return conn.execute("""
        SELECT company,
               COUNT(*) as total,
               SUM(CASE WHEN status='open' THEN 1 ELSE 0 END) as open,
               SUM(CASE WHEN assigned=0 THEN 1 ELSE 0 END) as unassigned,
               SUM(CASE WHEN priority=3 THEN 1 ELSE 0 END) as urgent
        FROM tickets
        GROUP BY company
    """).fetchall()

def category_summary():
    return conn.execute("""
        SELECT category,
               COUNT(*) as total,
               SUM(CASE WHEN priority=3 THEN 1 ELSE 0 END) as urgent
        FROM tickets
        GROUP BY category
    """).fetchall()

def all_tickets():
    return conn.execute("SELECT * FROM tickets").fetchall()