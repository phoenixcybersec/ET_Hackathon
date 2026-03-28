from app.ticketing.odoo_client import OdooClient
from app.ticketing.normalizer import normalize_ticket
from app.ticketing.store import upsert_ticket
from app.utils.logger import get_logger

logger = get_logger()
client = OdooClient()

def sync_tickets():
    logger.info("Starting sync cycle")

    records = client.fetch_tickets()

    for r in records:
        try:
            t = normalize_ticket(r)
            upsert_ticket(t)
        except Exception as e:
            logger.error(f"Error processing ticket {r.get('id')}: {e}")

    logger.info("Sync cycle completed")