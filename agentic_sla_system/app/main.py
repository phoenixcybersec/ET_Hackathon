import subprocess
import signal
import sys
import threading
import time
import uvicorn

from fastapi import FastAPI

from app.config.loader import load_config
from app.db.connection import init_db   # ✅ fixed import
from app.api.dashboard import router as dashboard_router
from app.api.odoo import router as odoo_router   # ✅ add this
from app.services.odoo_sync import sync_odoo_tickets  # ✅ add sync
from app.utils.logger import get_logger

logger = get_logger()
config = load_config()

app = FastAPI()

# ✅ Register routers
app.include_router(dashboard_router)
app.include_router(odoo_router)


# ---------------- STREAMLIT ---------------- #
def start_streamlit():
    logger.info("Starting Streamlit dashboard")

    return subprocess.Popen(
        ["streamlit", "run", "app/dashboard/streamlit_app.py"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )


# ---------------- AUTO SYNC (OPTIONAL BUT IMPORTANT) ---------------- #
def start_sync_loop():
    def loop():
        while True:
            try:
                logger.info("Running Odoo sync...")
                sync_odoo_tickets()
            except Exception as e:
                logger.error(f"Odoo sync failed: {e}")

            time.sleep(60)  # every 60 sec

    thread = threading.Thread(target=loop, daemon=True)
    thread.start()


# ---------------- MAIN ---------------- #
def main():
    logger.info("===== SYSTEM STARTING =====")

    # ✅ Init DB
    init_db()

    # ✅ Start Streamlit
    streamlit_process = start_streamlit()

    # ✅ Start auto sync (NEW)
    start_sync_loop()

    # ---------------- CLEAN SHUTDOWN ---------------- #
    def shutdown(sig, frame):
        logger.info("Shutting down system")

        if streamlit_process:
            streamlit_process.terminate()

        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    # ✅ Start FastAPI
    uvicorn.run(
        app,
        host=config["api"]["host"],
        port=config["api"]["port"],
        reload=False  # ⚠️ important when using threads
    )


if __name__ == "__main__":
    main()