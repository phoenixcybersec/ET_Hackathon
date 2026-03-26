import xmlrpc.client
from app.utils.config import config


class OdooClient:
    def __init__(self):
        # Load config
        self.url = config.get("odoo", "url")
        self.db = config.get("odoo", "db")
        self.username = config.get("odoo", "username")
        self.password = config.get("odoo", "password")

        # Setup XML-RPC endpoints
        self.common = xmlrpc.client.ServerProxy(f"{self.url}/xmlrpc/2/common")
        self.models = xmlrpc.client.ServerProxy(f"{self.url}/xmlrpc/2/object")

        # Authenticate
        self.uid = self.common.authenticate(
            self.db,
            self.username,
            self.password,
            {}
        )

        if not self.uid:
            raise Exception("Authentication failed. Check credentials.")

    def get_new_tickets(self):
        """
        Fetch tickets from Odoo
        (Currently fetching all tickets — filtering will be added later)
        """
        try:
            tickets = self.models.execute_kw(
                self.db,
                self.uid,
                self.password,
                "helpdesk.ticket",
                "search_read",
                [[]],  # later: add stage filter
                {
                    "fields": [
                        "id",
                        "name",
                        "description",
                        "stage_id",
                        "user_id"
                    ]
                },
            )

            return tickets

        except Exception as e:
            raise Exception(f"Error fetching tickets: {e}")

    def get_stages(self):
        """
        Fetch all helpdesk stages (useful for debugging stage IDs)
        """
        try:
            stages = self.models.execute_kw(
                self.db,
                self.uid,
                self.password,
                "helpdesk.stage",
                "search_read",
                [[]],
                {"fields": ["id", "name"]},
            )

            return stages

        except Exception as e:
            raise Exception(f"Error fetching stages: {e}")

    def update_ticket(self, ticket_id, values):
        """
        Update a ticket (will be used later when agents act)
        """
        try:
            self.models.execute_kw(
                self.db,
                self.uid,
                self.password,
                "helpdesk.ticket",
                "write",
                [[ticket_id], values],
            )

        except Exception as e:
            raise Exception(f"Error updating ticket {ticket_id}: {e}")