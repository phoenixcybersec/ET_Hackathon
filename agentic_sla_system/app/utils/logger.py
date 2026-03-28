from loguru import logger
import sys

logger.remove()

logger.add(
    sys.stdout,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
    level="INFO"
)

logger.add(
    "system.log",
    rotation="5 MB",
    retention="3 days",
    level="INFO"
)

def get_logger():
    return logger