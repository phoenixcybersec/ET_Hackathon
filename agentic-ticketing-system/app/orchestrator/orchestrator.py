from app.utils.logger import logger

def run_orchestrator(ticket_text):
    logger.info("Orchestrator started")

    state = {"ticket": ticket_text}

    logger.info(f"Input: {ticket_text}")

    # TEMP (no agents yet)
    result = {
        "status": "resolved",
        "resolution": "Test auto-resolution (pipeline working)"
    }

    logger.info(f"Output: {result}")

    return result