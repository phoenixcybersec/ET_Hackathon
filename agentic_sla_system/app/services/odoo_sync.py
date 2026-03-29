from bs4 import BeautifulSoup

from app.services.odoo_client import OdooClient
from app.db.database import get_connection
from app.utils.logger import get_logger

logger = get_logger()


# ================================================================
# HELPERS
# ================================================================
def clean_html(raw_html: str) -> str | None:
    if not raw_html:
        return None
    soup = BeautifulSoup(raw_html, "html.parser")
    for tag in soup(["script", "style"]):
        tag.extract()
    return soup.get_text(separator="\n").strip()


# ================================================================
# SYNC
# ================================================================
def sync_odoo_tickets() -> int:
    """
    Fetch tickets from Odoo and upsert only new/changed ones.
    Skips tickets whose write_date hasn't changed since last sync —
    so agents downstream are only triggered when there's real work.
    Returns count of new/updated tickets (0 = nothing changed → agents skipped).
    """
    client  = OdooClient()
    tickets = client.fetch_tickets()
    conn    = get_connection()

    new_or_updated = 0

    for rec in tickets:
        ticket_id  = str(rec["id"])
        write_date = rec.get("write_date")

        # ── Skip if ticket exists and hasn't changed ──────────
        existing = conn.execute(
            "SELECT updated_at FROM tickets WHERE ticket_id = ?", (ticket_id,)
        ).fetchone()

        if existing and existing["updated_at"] == write_date:
            continue

        # ── New or changed — upsert source fields only ────────
        new_or_updated += 1

        helpdesk_team = rec["team_id"][1]    if rec.get("team_id")    else None
        assigned_to   = rec["user_id"][1]    if rec.get("user_id")    else None
        customer      = rec["partner_id"][1] if rec.get("partner_id") else None
        partner_id    = rec["partner_id"][0] if rec.get("partner_id") else None
        phone         = client.get_partner_phone(partner_id)
        tags          = ",".join(map(str, rec.get("tag_ids", [])))
        description   = clean_html(rec.get("description"))

        conn.execute("""
            INSERT INTO tickets (
                ticket_id, subject,
                helpdesk_team, assigned_to, customer, phone,
                description, priority, tags,
                created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)

            ON CONFLICT(ticket_id) DO UPDATE SET
                subject       = excluded.subject,
                helpdesk_team = excluded.helpdesk_team,
                assigned_to   = excluded.assigned_to,
                customer      = excluded.customer,
                phone         = excluded.phone,
                description   = excluded.description,
                priority      = excluded.priority,
                tags          = excluded.tags,
                updated_at    = excluded.updated_at
                -- ai_*, is_classified, final_decision intentionally omitted
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
            write_date,
        ))

    conn.commit()
    logger.info(f"Synced {new_or_updated} new/updated of {len(tickets)} fetched")
    return new_or_updated