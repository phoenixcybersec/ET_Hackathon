import sqlite3
from app.config.loader import load_config
from app.utils.logger import get_logger

logger = get_logger()
config = load_config()

def get_connection():
    logger.info("Connecting to SQLite DB")
    return sqlite3.connect(config["db"]["path"], check_same_thread=False)

conn = get_connection()

def init_db():
    logger.info("Initializing database schema")

    conn.execute("""
    CREATE TABLE IF NOT EXISTS tickets (
        ticket_id TEXT PRIMARY KEY,
        subject TEXT,

        company TEXT,
        category TEXT,
        team TEXT,

        helpdesk_team TEXT,
        assigned_to TEXT,
        customer TEXT,
        phone TEXT,
        description TEXT,

        priority INTEGER,
        status TEXT,
        assigned INTEGER,

        created_at TEXT,
        updated_at TEXT
    )
    """)

    conn.commit()
    logger.info("Database initialized successfully")