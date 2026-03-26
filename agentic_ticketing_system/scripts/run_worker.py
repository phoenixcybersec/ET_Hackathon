# Optional: only for manual testing if needed

from app.integrations.odoo.client import OdooClient
from app.orchestrator.orchestrator import run_orchestrator


def run_once():
    odoo = OdooClient()
    tickets = odoo.get_new_tickets()

    for ticket in tickets:
        run_orchestrator(ticket)


if __name__ == "__main__":
    run_once()