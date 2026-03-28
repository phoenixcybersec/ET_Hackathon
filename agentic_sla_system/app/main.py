import subprocess
import signal
import sys
import uvicorn

from fastapi import FastAPI

from app.config.loader import load_config
from app.db.database import init_db
from app.api.dashboard import router
from app.utils.logger import get_logger

logger = get_logger()
config = load_config()

app = FastAPI()
app.include_router(router)

def start_streamlit():
    logger.info("Starting Streamlit dashboard")

    return subprocess.Popen(
        ["streamlit", "run", "app/dashboard/streamlit_app.py"]
    )

def main():
    logger.info("===== SYSTEM STARTING =====")

    init_db()

    streamlit_process = start_streamlit()

    def shutdown(sig, frame):
        logger.info("Shutting down system")

        if streamlit_process:
            streamlit_process.terminate()

        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    uvicorn.run(
        app,
        host=config["api"]["host"],
        port=config["api"]["port"]
    )

if __name__ == "__main__":
    main()