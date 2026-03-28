import xmlrpc.client
from app.config.loader import load_config
from app.utils.logger import get_logger

logger = get_logger()
config = load_config()


class OdooClient:
    def __init__(self):
        self.url = config["odoo"]["url"]
        self.db = config["odoo"]["db"]
        self.username = config["odoo"]["username"]
        self.password = config["odoo"]["password"]

        self.common = xmlrpc.client.ServerProxy(f"{self.url}/xmlrpc/2/common")
        self.uid = self.common.authenticate(self.db, self.username, self.password, {})

        self.models = xmlrpc.client.ServerProxy(f"{self.url}/xmlrpc/2/object")

        logger.info(f"Connected to Odoo UID={self.uid}")

    def fetch_tickets(self):
        tickets = self.models.execute_kw(
            self.db,
            self.uid,
            self.password,
            "helpdesk.ticket",
            "search_read",
            [[("id", "!=", 0)]],
            {
                "fields": [
                    "id",
                    "name",
                    "team_id",
                    "user_id",
                    "priority",
                    "tag_ids",
                    "partner_id",
                    "description",
                    "create_date",
                    "write_date",
                ],
                "limit": 100
            }
        )

        logger.info(f"Fetched {len(tickets)} tickets")
        return tickets

    def get_partner_phone(self, partner_id):
        if not partner_id:
            return None

        partner = self.models.execute_kw(
            self.db,
            self.uid,
            self.password,
            "res.partner",
            "read",
            [partner_id],
            {"fields": ["phone"]}
        )

        return partner[0].get("phone") if partner else None