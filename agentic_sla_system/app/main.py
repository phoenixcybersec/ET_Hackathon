import subprocess
import threading
import time
import uvicorn

from fastapi import FastAPI
from contextlib import asynccontextmanager

from app.agents.verification_agent import run_verification_agent
from app.config.loader import load_config
from app.db.database import init_db, init_ai_columns
from app.api.dashboard import router as dashboard_router
from app.api.odoo import router as odoo_router
from app.services.odoo_sync import sync_odoo_tickets
from app.agents.classifier_agent import classify_pending_tickets
from app.utils.logger import get_logger
from app.agents.decision_agent import run_decision_agent

logger = get_logger()
config = load_config()

# ---------------- LIFESPAN ---------------- #
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("===== SYSTEM STARTING =====")

    # Init DB
    logger.info("Initializing database schema")
    init_db()
    init_ai_columns()
    logger.info("Database initialized successfully")

    # Start Streamlit
    streamlit_process = start_streamlit()

    # Start sync loop
    start_sync_loop()

    yield  # app is running

    # Shutdown
    logger.info("===== SYSTEM SHUTTING DOWN =====")
    if streamlit_process:
        streamlit_process.terminate()
        logger.info("Streamlit process terminated")


app = FastAPI(
    title="Agentic SLA System",
    version="1.0.0",
    lifespan=lifespan
)

# Register routers
app.include_router(dashboard_router)
app.include_router(odoo_router)


# ---------------- HEALTH CHECK ---------------- #
@app.get("/health")
def health():
    return {"status": "ok", "service": "agentic-sla-system"}


# ---------------- STREAMLIT ---------------- #
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


# ---------------- SYNC + CLASSIFY LOOP ---------------- #
def start_sync_loop():
    interval = config.get("sync", {}).get("interval_seconds", 60)


    def _run_sync():
        # Step 1: Odoo sync
        try:
            logger.info("Running Odoo sync...")
            sync_odoo_tickets()
            logger.info("Odoo sync complete")
        except Exception as e:
            logger.error(f"Odoo sync failed: {e}")

        # Step 2: Classify
        try:
            logger.info("Running classifier agent...")
            classify_pending_tickets()
            logger.info("Classification complete")
        except Exception as e:
            logger.error(f"Classifier agent failed: {e}")

        # Step 3: Decision
        try:
            logger.info("Running decision agent...")
            run_decision_agent()
            logger.info("Decision agent complete")
        except Exception as e:
            logger.error(f"Decision agent failed: {e}")

         # Step 4: Verification (runs on humanly executed tickets)
        try:
            logger.info("Running verification agent...")
            run_verification_agent()
            logger.info("Verification agent complete")
        except Exception as e:
            logger.error(f"Verification agent failed: {e}")

    def loop():
        _run_sync()  # run immediately on startup
        while True:
            time.sleep(interval)
            _run_sync()

    thread = threading.Thread(target=loop, daemon=True, name="odoo-sync")
    thread.start()
    logger.info(f"Sync loop started (every {interval}s)")


# ---------------- MAIN ---------------- #
def main():
    uvicorn.run(
        app,
        host=config["api"]["host"],
        port=config["api"]["port"],
        reload=False
    )


if __name__ == "__main__":
    main()