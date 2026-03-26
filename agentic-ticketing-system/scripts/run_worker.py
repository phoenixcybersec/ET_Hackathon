import time
from app.utils.config import config
from app.integrations.odoo.client import OdooClient
from app.orchestrator.orchestrator import run_orchestrator

odoo = OdooClient()


def process_tickets():
    print("🚀 Worker started...\n")

    poll_interval = config.get("worker", "poll_interval")

    while True:
        tickets = odoo.get_new_tickets()

        for ticket in tickets:
            print(f"\n📩 Ticket: {ticket['name']}")

            result = run_orchestrator(ticket["description"])

            message = format_response(result)

            odoo.update_ticket(ticket["id"], message)

            print("✅ Updated in Odoo")

        time.sleep(poll_interval)


def format_response(result):
    if result.get("status") == "resolved":
        return f"""
🤖 AI Resolution:

{result['resolution']}

✅ Status: Resolved
"""
    return "⚠️ Escalated"


if __name__ == "__main__":
    process_tickets()