import sys
import os
import re

# Add project path
sys.path.append(os.path.abspath("agentic-ticketing-system"))

from app.integrations.odoo.client import OdooClient


def clean_html(raw_html):
    if not raw_html:
        return ""
    return re.sub('<.*?>', '', raw_html)


def format_stage(stage):
    if stage and isinstance(stage, list):
        return stage[1]
    return "Unknown"


def format_assigned(user):
    if user and isinstance(user, list):
        return user[1]
    return "Unassigned"


def test_connection():
    print("Testing Odoo connection...\n")

    try:
        odoo = OdooClient()
        print("Authentication successful\n")

        tickets = odoo.get_new_tickets()
        print(f"Tickets fetched: {len(tickets)}\n")

        if not tickets:
            print("No tickets found.")
            return

        for t in tickets:
            ticket_id = t.get("id")
            title = t.get("name")
            description = clean_html(t.get("description"))
            stage = format_stage(t.get("stage_id"))
            assigned_to = format_assigned(t.get("user_id"))

            print(f"ID: {ticket_id}")
            print(f"Title: {title}")
            print(f"Description: {description}")
            print(f"Stage: {stage}")
            print(f"Assigned To: {assigned_to}")
            print("-" * 50)

    except Exception as e:
        print("Connection failed")
        print(f"Error: {e}")


if __name__ == "__main__":
    test_connection()