import subprocess
import threading
import time
import uvicorn

from fastapi import FastAPI
from contextlib import asynccontextmanager

from app.config.loader import load_config
from app.db.database import init_db, init_ai_columns
from app.api.dashboard import router as dashboard_router
from app.api.odoo import router as odoo_router
from app.services.odoo_sync import sync_odoo_tickets
from app.agents.classifier_agent import classify_pending_tickets
from app.agents.decision_agent import run_decision_agent
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
    start_sync_loop()

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
# SYNC + AGENT LOOP
# ================================================================
def _run_pipeline():
    """
    One pipeline cycle:
      1. Sync Odoo → returns count of new/updated tickets
      2. Only classify if sync brought something in
      3. Only run decision agent if classifier produced new results
    """

    # ── Step 1: Odoo sync ──────────────────────────────────────
    synced_count = 0
    try:
        logger.info("Running Odoo sync...")
        synced_count = sync_odoo_tickets()   # must return int
        logger.info(f"Odoo sync complete — {synced_count} ticket(s) synced")
    except Exception as e:
        logger.error(f"Odoo sync failed: {e}")

    if synced_count == 0:
        logger.info("No new tickets — skipping classifier and decision agent")
        return

    # ── Step 2: Classify new/unclassified tickets ───────────────
    classified_count = 0
    try:
        logger.info("Running classifier agent...")
        classified_count = classify_pending_tickets()   # must return int
        logger.info(f"Classification complete — {classified_count} ticket(s) classified")
    except Exception as e:
        logger.error(f"Classifier agent failed: {e}")

    if classified_count == 0:
        logger.info("No newly classified tickets — skipping decision agent")
        return

    # ── Step 3: Decision agent (only if classifier did work) ────
    try:
        logger.info("Running decision agent...")
        run_decision_agent()
        logger.info("Decision agent complete")
    except Exception as e:
        logger.error(f"Decision agent failed: {e}")

    # ── Step 4: Verification (uncomment when ready) ─────────────
    # try:
    #     logger.info("Running verification agent...")
    #     run_verification_agent()
    #     logger.info("Verification agent complete")
    # except Exception as e:
    #     logger.error(f"Verification agent failed: {e}")


def start_sync_loop():
    interval = config.get("sync", {}).get("interval_seconds", 60)

    def loop():
        _run_pipeline()          # run immediately on startup
        while True:
            time.sleep(interval)
            _run_pipeline()

    thread = threading.Thread(target=loop, daemon=True, name="odoo-sync")
    thread.start()
    logger.info(f"Sync loop started (every {interval}s)")


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