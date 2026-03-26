import logging
import os
from app.utils.config import config

log_path = config.get("paths", "logs", default="logs/")
os.makedirs(log_path, exist_ok=True)

logging.basicConfig(
    filename=os.path.join(log_path, "app.log"),
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger("ai-ticketing")