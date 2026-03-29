import sqlite3
import os
from app.config.loader import load_config
from app.utils.logger import get_logger

logger = get_logger()
config = load_config()


def get_db_path() -> str:
    """Single source of truth for the DB file path."""
    raw_path = config["db"]["path"]
    if not os.path.isabs(raw_path):
        repo_root = os.path.normpath(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
        )
        db_path = os.path.join(repo_root, raw_path)
    else:
        db_path = raw_path
    return os.path.normpath(db_path)


def get_connection() -> sqlite3.Connection:
    """
    FIX: was a global singleton — once closed anywhere in the process,
    every subsequent caller got 'Cannot operate on a closed database'.

    Now returns a fresh connection on every call.
    Callers are responsible for calling conn.close() when done.
    WAL mode is set so multiple threads can read while one writes.
    """
    db_path = get_db_path()
    logger.info(f"DB path resolved: {db_path}")
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    logger.info("🔥 INIT DB CALLED")
    logger.info("Connecting to SQLite DB")
    conn = get_connection()

    conn.execute("""
    CREATE TABLE IF NOT EXISTS tickets (
        ticket_id     TEXT PRIMARY KEY,
        subject       TEXT,
        helpdesk_team TEXT,
        assigned_to   TEXT,
        customer      TEXT,
        phone         TEXT,
        description   TEXT,
        priority      INTEGER,
        tags          TEXT,
        status        TEXT DEFAULT 'NEW',
        created_at    TEXT,
        updated_at    TEXT
    )
    """)

    conn.commit()
    conn.close()
    logger.info("✅ Base table created")


def init_ai_columns():
    logger.info("🔥 INIT AI COLUMNS CALLED")
    conn = get_connection()

    for col, coltype in [
        ("ai_issue",            "TEXT"),
        ("ai_category",         "TEXT"),
        ("ai_priority",         "TEXT"),
        ("ai_confidence",       "REAL"),
        ("ai_suggestion",       "TEXT"),
        ("ai_sla_rule",         "TEXT"),
        ("ai_breach_penalty",   "TEXT"),
        ("ai_answer",           "TEXT"),
        ("ai_decision",         "TEXT"),
        ("final_decision",      "TEXT"),
        ("decision_reason",     "TEXT"),
        ("requires_human",      "INTEGER"),
        ("approved_by_human",   "INTEGER"),
        ("human_action",        "TEXT"),
        ("human_executed",      "INTEGER"),
        ("verification_result", "TEXT"),
        ("verification_notes",  "TEXT"),
        ("verified",            "INTEGER"),
        ("execution_route",     "TEXT"),
        ("is_classified",       "INTEGER DEFAULT 0"),
        ("execution_action",    "TEXT"),
        ("execution_status",    "TEXT"),
        ("execution_output",    "TEXT"),
        ("execution_time",      "TEXT"),
    ]:
        try:
            conn.execute(f"ALTER TABLE tickets ADD COLUMN {col} {coltype}")
            logger.info(f"✅ Added column: {col}")
        except Exception:
            pass  # already exists — safe to ignore

    conn.commit()
    conn.close()
    logger.info("✅ AI columns ready")