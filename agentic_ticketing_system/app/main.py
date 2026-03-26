import sys
import time
from app.utils.config import config
from app.utils.logger import logger
from app.db.models import create_table
from app.integrations.odoo.client import OdooClient
from app.orchestrator.orchestrator import run_orchestrator


def check_config():
    logger.info("Checking configuration")

    required_fields = [
        ("odoo", "url"),
        ("odoo", "db"),
        ("odoo", "username"),
        ("odoo", "password"),
    ]

    for section, key in required_fields:
        value = config.get(section, key)
        if not value:
            logger.error(f"Missing config: {section}.{key}")
            sys.exit(1)

    logger.info("Configuration valid")


def check_db():
    logger.info("Checking database")

    try:
        create_table()
        logger.info("Database ready")
    except Exception as e:
        logger.error(f"Database error: {e}")
        sys.exit(1)


def check_odoo(odoo):
    logger.info("Checking Odoo connection")

    try:
        tickets = odoo.get_new_tickets()
        logger.info(f"Odoo connected. Tickets available: {len(tickets)}")
    except Exception as e:
        logger.error(f"Odoo connection failed: {e}")
        sys.exit(1)


def process_loop():
    odoo = OdooClient()
    poll_interval = config.get("worker", "poll_interval", default=5)

    logger.info("Starting main processing loop")

    try:
        while True:
            tickets = odoo.get_new_tickets()

            if tickets:
                logger.info(f"Fetched {len(tickets)} ticket(s)")

            for ticket in tickets:
                try:
                    logger.info(f"Processing ticket ID: {ticket['id']}")

                    run_orchestrator(ticket)

                    logger.info(f"Stored ticket ID: {ticket['id']}")

                except Exception as e:
                    logger.error(f"Error processing ticket {ticket['id']}: {e}")

            time.sleep(poll_interval)

    except KeyboardInterrupt:
        logger.info("Shutdown requested by user (Ctrl + C)")
        sys.exit(0)


def start():
    logger.info("Starting AI Ticketing System")

    check_config()
    check_db()

    odoo = OdooClient()
    check_odoo(odoo)

    process_loop()


if __name__ == "__main__":
    start()