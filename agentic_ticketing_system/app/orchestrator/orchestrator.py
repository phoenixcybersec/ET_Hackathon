from app.db.repository import save_ticket
from app.utils.logger import logger

def run_orchestrator(ticket):
    logger.info(f"Processing ticket {ticket['id']}")
    save_ticket(ticket)
    logger.info(f"Stored ticket {ticket['id']} in DB")
    return {"status": "stored"}