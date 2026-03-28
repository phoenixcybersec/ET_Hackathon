import yaml
from pathlib import Path
from app.utils.logger import get_logger

logger = get_logger()

def load_config():
    path = Path(__file__).parent / "config.yaml"
    logger.info(f"Loading config from {path}")

    with open(path, "r") as f:
        config = yaml.safe_load(f)

    logger.info("Config loaded successfully")
    return config