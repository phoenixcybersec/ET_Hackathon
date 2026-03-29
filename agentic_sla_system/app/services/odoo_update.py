import xmlrpc.client
from app.db.database import get_connection
from app.config.loader import load_config
from app.utils.logger import get_logger

logger = get_logger()

# BUG FIX 1: credentials were hardcoded as module-level literals — any import
# of this file exposed them. Moved into the function and loaded from config,
# matching the pattern used in the other two agents.
def _load_odoo_cfg():
    cfg = load_config()
    odoo = cfg.get("odoo", {})
    return {
        "url":      odoo.get("url",      "http://your-odoo-url"),
        "db":       odoo.get("db",       "your_db"),
        "username": odoo.get("username", "your_email"),
        "password": odoo.get("password", "your_api_key"),
        "closed_stage_id": int(odoo.get("closed_stage_id", 4)),
    }

def run_odoo_update():
    odoo = _load_odoo_cfg()
    conn = get_connection()

    common = xmlrpc.client.ServerProxy(f"{odoo['url']}/xmlrpc/2/common")
    uid = common.authenticate(odoo["db"], odoo["username"], odoo["password"], {})

    if not uid:
        logger.error("Odoo auth failed")
        return

    models = xmlrpc.client.ServerProxy(f"{odoo['url']}/xmlrpc/2/object")

    rows = conn.execute("""
        SELECT * FROM tickets
        WHERE verified = 1
        AND verification_result = 'RESOLVED'
        AND status != 'CLOSED'
    """).fetchall()

    logger.info(f"Odoo update fetched {len(rows)} tickets")

    for t in rows:
        ticket_id = t["ticket_id"]

        try:
            odoo_id = int(ticket_id)

            models.execute_kw(
                odoo["db"], uid, odoo["password"],
                "helpdesk.ticket", "write",
                [[odoo_id], {
                    "stage_id": odoo["closed_stage_id"],
                    "description": t["verification_notes"],
                }]
            )

            # 🔥 THIS IS WHAT UI READS
            conn.execute("""
                UPDATE tickets SET
                    status='CLOSED'
                WHERE ticket_id=?
            """, (ticket_id,))
            conn.commit()

            logger.info(f"Ticket {ticket_id} closed in Odoo + DB")

        except Exception as e:
            logger.error(f"Odoo update failed for {ticket_id}: {e}")

    conn.close()