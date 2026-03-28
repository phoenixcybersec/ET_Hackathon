from app.utils.logger import get_logger

logger = get_logger()

def map_priority(p):
    try:
        val = max(1, min(int(p), 3))
        return val
    except:
        logger.warning(f"Invalid priority {p}, defaulting to 1")
        return 1

def normalize_ticket(rec):
    logger.info(f"Normalizing ticket {rec.get('id')}")

    team = rec.get("team_id")[1] if rec.get("team_id") else "General"

    ticket = {
        "ticket_id": str(rec["id"]),
        "subject": rec.get("name", ""),

        # Core mapping
        "company": rec.get("partner_name", "Unknown"),
        "category": team,
        "team": team,

        # Helpdesk fields
        "helpdesk_team": team,
        "assigned_to": "GRAVITY_AI",
        "customer": rec.get("partner_name", "Unknown Customer"),
        "phone": rec.get("phone", "99009900"),
        "description": rec.get("description", "No description provided"),

        "priority": map_priority(rec.get("priority", 1)),
        "status": "open",
        "assigned": 1,

        "created_at": rec.get("create_date"),
        "updated_at": rec.get("write_date")
    }

    logger.info(f"Normalized ticket: {ticket}")
    return ticket