import sqlite3
from app.config.loader import load_config
from app.utils.logger import get_logger

logger = get_logger()
config = load_config()

_conn = None

def get_connection():
    global _conn
    if _conn is None:
        logger.info("Connecting to SQLite DB")
        _conn = sqlite3.connect(config["db"]["path"], check_same_thread=False)
        _conn.row_factory = sqlite3.Row
    return _conn


def init_db():
    logger.info("🔥 INIT DB CALLED")
    conn = get_connection()

    conn.execute("DROP TABLE IF EXISTS tickets")

    conn.execute("""
    CREATE TABLE IF NOT EXISTS tickets (
        ticket_id TEXT PRIMARY KEY,
        subject TEXT,
        helpdesk_team TEXT,
        assigned_to TEXT,
        customer TEXT,
        phone TEXT,
        description TEXT,
        priority INTEGER,
        tags TEXT,
        status TEXT DEFAULT 'NEW',
        created_at TEXT,
        updated_at TEXT
    )
    """)

    conn.commit()
    logger.info("✅ Base table created")

def init_ai_columns():
    logger.info("🔥 INIT AI COLUMNS CALLED")
    conn = get_connection()

    for col, coltype in [
        ("ai_issue",           "TEXT"),
        ("ai_category",        "TEXT"),
        ("ai_priority",        "TEXT"),
        ("ai_confidence",      "REAL"),
        ("ai_suggestion",      "TEXT"),   # step by step SOP
        ("ai_sla_rule",        "TEXT"),   # e.g. Response: 30min, Resolution: 4hrs
        ("ai_breach_penalty",  "TEXT"),   # e.g. ₹10,000
        ("ai_answer",          "TEXT"),   # full paragraph answer from LLM
        ("ai_decision",        "TEXT"),
        ("final_decision",     "TEXT"),
        ("decision_reason",    "TEXT"),
        ("requires_human",     "INTEGER"),
        ("approved_by_human",  "INTEGER"),
        ("human_action",       "TEXT"),
        ("human_executed",     "INTEGER"),
        ("verification_result","TEXT"),
        ("verification_notes", "TEXT"),
        ("verified",           "INTEGER"),
    ]:
        try:
            conn.execute(f"ALTER TABLE tickets ADD COLUMN {col} {coltype}")
            logger.info(f"✅ Added column: {col}")
        except Exception as e:
            logger.warning(f"⚠️  Skipped {col}: {e}")

    conn.commit()
    logger.info("✅ AI columns ready")