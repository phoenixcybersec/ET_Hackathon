import sqlite3
import os
from app.config.loader import load_config
from app.utils.logger import get_logger

logger = get_logger()
config = load_config()

_conn = None


def get_connection():
    global _conn
    if _conn is None:
        raw_path = config["db"]["path"]

        if not os.path.isabs(raw_path):
            repo_root = os.path.normpath(
                os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
            )
            db_path = os.path.join(repo_root, raw_path)
        else:
            db_path = raw_path

        db_path = os.path.normpath(db_path)
        logger.info("Connecting to SQLite DB")
        logger.info(f"DB path resolved: {db_path}")
        _conn = sqlite3.connect(db_path, check_same_thread=False)
        _conn.row_factory = sqlite3.Row
        _conn.execute("PRAGMA journal_mode=WAL")
        _conn.execute("PRAGMA foreign_keys=ON")
    return _conn


def init_db():
    logger.info("🔥 INIT DB CALLED")
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
        # ── gate flag: set to 1 after classifier completes, never reset by sync ──
        ("is_classified",       "INTEGER DEFAULT 0"),
    ]:
        try:
            conn.execute(f"ALTER TABLE tickets ADD COLUMN {col} {coltype}")
            logger.info(f"✅ Added column: {col}")
        except Exception:
            pass  # already exists after first run

    conn.commit()
    logger.info("✅ AI columns ready")