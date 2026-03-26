import time
from app.utils.config import config
from app.integrations.odoo.client import OdooClient
from app.orchestrator.orchestrator import run_orchestrator
from app.utils.logger import logger

odoo = OdooClient()


def process_tickets():
    logger.info("Worker started...")
    poll_interval = config.get("worker", "poll_interval")

    logger.info("🚀 Worker started")

    while True:
        tickets = odoo.get_new_tickets()

        if tickets:
            logger.info(f"{len(tickets)} new ticket(s) received")
        for ticket in tickets:
            logger.info(f"Ticket ID: {ticket['id']}")
            logger.info(f"Title: {ticket['name']}")
            logger.info(f"Description: {ticket['description']}")
            result = run_orchestrator(ticket["description"])
            logger.info(f"Result: {result}")
            message = format_response(result)
            odoo.update_ticket(ticket["id"], message)
            logger.info("Ticket updated in Odoo")


def format_response(result):
    if result.get("status") == "resolved":
        return f""" AI Resolution:{result['resolution']} Status: Resolved """
    logger.warning("⚠️ Could not resolve ticket, escalating")
    return "Escalated"


if __name__ == "__main__":
    process_tickets()