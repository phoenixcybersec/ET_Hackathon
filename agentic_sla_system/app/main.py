import subprocess
import threading
import time
import uvicorn

from fastapi import FastAPI
from contextlib import asynccontextmanager

from app.config.loader import load_config
from app.db.database import init_db, init_ai_columns, get_connection
from app.api.dashboard import router as dashboard_router
from app.api.odoo import router as odoo_router
from app.services.odoo_sync import sync_odoo_tickets
from app.agents.classifier_agent import classify_pending_tickets
from app.agents.decision_agent import run_decision_agent
from app.agents.execution_agent import run_execution_agent
from app.agents.validation_agent import run_validation_agent
from app.services.odoo_update import run_odoo_update
from app.utils.logger import get_logger

logger = get_logger()
config = load_config()


# ================================================================
# LIFESPAN
# ================================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("===== SYSTEM STARTING =====")

    logger.info("Initializing database schema")
    init_db()
    init_ai_columns()
    logger.info("Database initialized successfully")

    streamlit_process = start_streamlit()
    start_primary_loop()      # Cycle A: Odoo sync → Classify → Decide → Execute
    start_secondary_loop()    # Cycle B: Validate → Odoo update (runs after delay)

    yield

    logger.info("===== SYSTEM SHUTTING DOWN =====")
    if streamlit_process:
        streamlit_process.terminate()
        logger.info("Streamlit process terminated")


app = FastAPI(title="Agentic SLA System", version="1.0.0", lifespan=lifespan)
app.include_router(dashboard_router)
app.include_router(odoo_router)


# ================================================================
# HEALTH
# ================================================================
@app.get("/health")
def health():
    return {"status": "ok", "service": "agentic-sla-system"}


# ================================================================
# STREAMLIT
# ================================================================
def start_streamlit():
    logger.info("Starting Streamlit dashboard")
    try:
        process = subprocess.Popen(
            ["streamlit", "run", "app/dashboard/streamlit_app.py",
             "--server.headless", "true"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        logger.info(f"Streamlit started (PID: {process.pid})")
        return process
    except Exception as e:
        logger.error(f"Failed to start Streamlit: {e}")
        return None


# ================================================================
# HELPERS
# ================================================================
def _escalate_ticket(ticket_id: str, reason: str):
    """
    Mark a ticket as ESCALATED so human review picks it up.
    Opens its own fresh connection — never depends on caller's conn
    which may already be closed.
    """
    conn = get_connection()
    try:
        conn.execute("""
            UPDATE tickets SET
                final_decision   = 'ESCALATE',
                execution_status = 'EXECUTION_FAILED',
                execution_output = ?,
                execution_time   = datetime('now')
            WHERE ticket_id = ?
        """, (f"Auto-escalated: {reason}"[:4000], ticket_id))
        conn.commit()
    finally:
        conn.close()
    logger.warning(f"Ticket {ticket_id} escalated to human — {reason}")


def _get_tickets(query: str, params: tuple = ()):
    """Opens its own fresh connection, fetches, closes. Thread-safe."""
    conn = get_connection()
    try:
        rows = conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


# ================================================================
# CYCLE A — Primary pipeline
#   1. Odoo sync
#   2. Classifier
#   3. Decision agent
#   4. Execution agent
# ================================================================
def _run_primary_pipeline():
    logger.info("━━━ [CYCLE A] Primary pipeline starting ━━━")

    # ── Step 1: Odoo sync ──────────────────────────────────────
    synced_count = 0
    try:
        logger.info("[1/4] Running Odoo sync...")
        synced_count = sync_odoo_tickets()
        logger.info(f"[1/4] Odoo sync complete — {synced_count} ticket(s) synced")
    except Exception as e:
        logger.error(f"[1/4] Odoo sync failed: {e}")

    if synced_count == 0:
        logger.info("[CYCLE A] No new tickets — skipping remaining steps")
        return

    # ── Step 2: Classifier ─────────────────────────────────────
    classified_count = 0
    try:
        logger.info("[2/4] Running classifier agent...")
        classified_count = classify_pending_tickets()
        logger.info(f"[2/4] Classification complete — {classified_count} ticket(s) classified")
    except Exception as e:
        logger.error(f"[2/4] Classifier agent failed: {e}")

    if classified_count == 0:
        logger.info("[CYCLE A] No newly classified tickets — skipping decision + execution")
        return

    # ── Step 3: Decision agent ─────────────────────────────────
    try:
        logger.info("[3/4] Running decision agent...")
        run_decision_agent()
        logger.info("[3/4] Decision agent complete")
    except Exception as e:
        logger.error(f"[3/4] Decision agent failed: {e}")
        return  # can't execute without decisions

    # ── Step 4: Execution agent ────────────────────────────────
    try:
        logger.info("[4/4] Running execution agent...")
        # FIX: only pick up AUTO-FIX tickets that have never been attempted.
        # EXECUTION_FAILED tickets are escalated — never retried.
        tickets = _get_tickets("""
            SELECT * FROM tickets
            WHERE final_decision = 'AUTO-FIX'
            AND execution_status IS NULL
        """)

        logger.info(f"[4/4] {len(tickets)} ticket(s) queued for execution")

        for ticket in tickets:
            ticket_id = ticket.get("ticket_id", "unknown")
            try:
                result = run_execution_agent(ticket)

                if result.get("skipped"):
                    logger.info(f"  ↷ Ticket {ticket_id} skipped — decision not AUTO-FIX")

                elif result.get("success"):
                    logger.info(f"  ✓ Ticket {ticket_id} executed successfully — "
                                f"{result.get('message', '')}")

                else:
                    # FIX: execution failed → escalate to human, no retry
                    reason = result.get("message", "unknown execution error")
                    logger.warning(f"  ✗ Ticket {ticket_id} execution failed — escalating: {reason}")
                    _escalate_ticket(ticket_id, reason)

            except Exception as e:
                logger.error(f"  ✗ Execution agent crashed on ticket {ticket_id}: {e}")
                _escalate_ticket(ticket_id, str(e))

        logger.info("[4/4] Execution agent complete")

    except Exception as e:
        logger.error(f"[4/4] Execution agent failed: {e}")

    logger.info("━━━ [CYCLE A] Primary pipeline complete ━━━")


# ================================================================
# CYCLE B — Secondary pipeline (runs after a startup delay,
#            then on its own interval so execution has time to land)
#   5. Validation agent  — reads execution_output, calls OpenAI
#   6. Odoo update       — closes/escalates resolved tickets in Odoo
# ================================================================
def _run_secondary_pipeline():
    logger.info("━━━ [CYCLE B] Secondary pipeline starting ━━━")

    # ── Step 5: Validation agent ───────────────────────────────
    try:
        logger.info("[5/6] Running validation agent...")
        run_validation_agent()
        logger.info("[5/6] Validation agent complete")
    except Exception as e:
        logger.error(f"[5/6] Validation agent failed: {e}")

    # ── Step 6: Odoo update ────────────────────────────────────
    try:
        logger.info("[6/6] Running Odoo update...")
        run_odoo_update()
        logger.info("[6/6] Odoo update complete")
    except Exception as e:
        logger.error(f"[6/6] Odoo update failed: {e}")

    logger.info("━━━ [CYCLE B] Secondary pipeline complete ━━━")


# ================================================================
# LOOP THREADS
# ================================================================
def start_primary_loop():
    interval = config.get("sync", {}).get("interval_seconds", 60)

    def loop():
        _run_primary_pipeline()          # run immediately on startup
        while True:
            time.sleep(interval)
            _run_primary_pipeline()

    thread = threading.Thread(target=loop, daemon=True, name="pipeline-primary")
    thread.start()
    logger.info(f"[CYCLE A] Primary loop started (every {interval}s)")


def start_secondary_loop():
    interval      = config.get("sync", {}).get("interval_seconds", 60)
    startup_delay = config.get("sync", {}).get("validation_delay_seconds", 90)

    # FIX: secondary loop waits for startup_delay before its first run so
    # Cycle A always has time to write execution results before Cycle B reads them.
    def loop():
        logger.info(f"[CYCLE B] Secondary loop waiting {startup_delay}s before first run...")
        time.sleep(startup_delay)
        _run_secondary_pipeline()
        while True:
            time.sleep(interval)
            _run_secondary_pipeline()

    thread = threading.Thread(target=loop, daemon=True, name="pipeline-secondary")
    thread.start()
    logger.info(f"[CYCLE B] Secondary loop started (delay={startup_delay}s, every {interval}s)")


# ================================================================
# MAIN
# ================================================================
def main():
    uvicorn.run(
        app,
        host=config["api"]["host"],
        port=config["api"]["port"],
        reload=False
    )


if __name__ == "__main__":
    main()