import xmlrpc.client
from app.utils.config import config

ODOO_URL = config.get("odoo", "url")
ODOO_DB = config.get("odoo", "db")
ODOO_USERNAME = config.get("odoo", "username")
ODOO_PASSWORD = config.get("odoo", "password")


class OdooClient:
    def __init__(self):
        self.common = xmlrpc.client.ServerProxy(f"{ODOO_URL}/xmlrpc/2/common")
        self.uid = self.common.authenticate(
            ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD, {}
        )

        self.models = xmlrpc.client.ServerProxy(f"{ODOO_URL}/xmlrpc/2/object")

    def get_new_tickets(self):
        stage_id = config.get("odoo", "new_ticket_stage_id")

        return self.models.execute_kw(
            ODOO_DB,
            self.uid,
            ODOO_PASSWORD,
            "helpdesk.ticket",
            "search_read",
            [[("stage_id", "=", stage_id)]],
            {"fields": ["id", "name", "description"]},
        )

    def update_ticket(self, ticket_id, message):
        stage_id = config.get("odoo", "resolved_stage_id")

        self.models.execute_kw(
            ODOO_DB,
            self.uid,
            ODOO_PASSWORD,
            "helpdesk.ticket",
            "write",
            [[ticket_id], {"description": message, "stage_id": stage_id}],
        )