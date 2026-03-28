from datetime import datetime
from bs4 import BeautifulSoup

from app.services.odoo_client import OdooClient
from app.db.connection import conn


# ✅ CLEAN HTML → TEXT
def clean_html(raw_html):
    if not raw_html:
        return None

    soup = BeautifulSoup(raw_html, "html.parser")

    # Remove script/style if present
    for tag in soup(["script", "style"]):
        tag.extract()

    return soup.get_text(separator="\n").strip()


def sync_odoo_tickets():
    client = OdooClient()
    tickets = client.fetch_tickets()

    for rec in tickets:
        ticket_id = str(rec["id"])

        helpdesk_team = rec["team_id"][1] if rec.get("team_id") else None
        assigned_to = rec["user_id"][1] if rec.get("user_id") else None
        customer = rec["partner_id"][1] if rec.get("partner_id") else None

        partner_id = rec["partner_id"][0] if rec.get("partner_id") else None
        phone = client.get_partner_phone(partner_id)

        tags = ",".join(map(str, rec.get("tag_ids", [])))

        # 🔥 FIXED DESCRIPTION
        description = clean_html(rec.get("description"))

        conn.execute("""
            INSERT OR REPLACE INTO tickets (
                ticket_id,
                subject,
                helpdesk_team,
                assigned_to,
                customer,
                phone,
                description,
                priority,
                tags,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            ticket_id,
            rec.get("name"),
            helpdesk_team,
            assigned_to,
            customer,
            phone,
            description,
            int(rec.get("priority", 0)),
            tags,
            rec.get("create_date"),
            rec.get("write_date"),
        ))

    conn.commit()
    print(f"✅ Synced {len(tickets)} tickets")