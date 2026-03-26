import re


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


def transform_ticket(raw):
    return {
        "id": raw.get("id"),
        "title": raw.get("name"),
        "description": clean_html(raw.get("description")),
        "stage": format_stage(raw.get("stage_id")),
        "assigned_to": format_assigned(raw.get("user_id"))
    }