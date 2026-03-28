import xmlrpc.client
from app.config.loader import load_config
from app.utils.logger import get_logger

logger = get_logger()
config = load_config()

class OdooClient:
    def __init__(self):
        logger.info("Initializing Odoo client")

        url = config["odoo"]["url"]
        db = config["odoo"]["db"]
        username = config["odoo"]["username"]
        password = config["odoo"]["password"]

        common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
        self.uid = common.authenticate(db, username, password, {})

        self.models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object")
        self.db = db
        self.password = password
        self.model = config["odoo"]["model"]

        logger.info(f"Odoo client initialized (uid={self.uid})")

    def fetch_tickets(self):
        logger.info("Fetching tickets from Odoo")

        records = self.models.execute_kw(
            self.db, self.uid, self.password,
            self.model, "search_read",
            [[]],
            {"fields": ["id","name","partner_name","team_id","priority","create_date","write_date"]}
        )

        logger.info(f"Fetched {len(records)} tickets from Odoo")
        return records