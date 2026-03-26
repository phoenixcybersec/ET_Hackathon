import time
import sys

from app.utils.config import config
from app.utils.logger import logger
from app.db.models import create_table
from app.integrations.odoo.client import OdooClient
from app.orchestrator.orchestrator import run_orchestrator


def start():
    logger.info("Starting system")
    print("Starting system...")  # for visibility when running in terminal

    # Init DB
    create_table()

    # Init Odoo
    odoo = OdooClient()

    poll_interval = config.get("worker", "poll_interval", default=10)

    logger.info(f"Polling every {poll_interval} seconds")

    try:
        while True:
            tickets = odoo.get_new_tickets()
            print(f"Fetched {len(tickets)} ticket(s)")  # for visibility when running in terminal
            if tickets:
                logger.info(f"Fetched {len(tickets)} ticket(s)")

            for ticket in tickets:
                try:
                    run_orchestrator(ticket)
                except Exception as e:
                    logger.error(f"Error processing ticket {ticket.get('id')}: {e}")

            time.sleep(poll_interval)

    except KeyboardInterrupt:
        logger.info("Shutting down")
        sys.exit(0)


if __name__ == "__main__":
    start()