import json
import os
import requests

from app.config.loader import load_config
from app.db.database import get_connection
from app.utils.logger import get_logger

logger = get_logger()
config = load_config()

OLLAMA_URL = config["ollama"]["url"]
OLLAMA_MODEL = config["ollama"]["model"]
OLLAMA_TIMEOUT = config["ollama"]["timeout"]
KB_PATH = config["knowledge_base"]["path"]


# ---------------- LOAD KNOWLEDGE BASE ---------------- #
def load_knowledge_base() -> str:
    context = ""
    try:
        for filename in sorted(os.listdir(KB_PATH)):
            if filename.endswith((".md", ".txt", ".pdf")):
                filepath = os.path.join(KB_PATH, filename)
                with open(filepath, "r", encoding="utf-8") as f:
                    context += f"\n\n### {filename}\n{f.read()}"
        logger.info(f"Knowledge base loaded: {len(context)} chars")
    except Exception as e:
        logger.error(f"Failed to load knowledge base: {e}")
    return context.strip()


# ---------------- BUILD PROMPT ---------------- #
def build_prompt(ticket: dict, sop_context: str) -> str:
    return f"""
You are an expert IT helpdesk classifier. Analyze the ticket and knowledge base below.
Respond ONLY in valid JSON with no extra text.

--- TICKET ---
Subject: {ticket.get('subject', '')}
Description: {ticket.get('description', '')}
Helpdesk Team: {ticket.get('helpdesk_team', '')}
Priority: {ticket.get('priority', '')}

--- KNOWLEDGE BASE (SOPs & SLA Rules) ---
{sop_context}

--- TASK ---
Based on the knowledge base above, return ONLY this JSON:
{{
  "ai_issue": "one line root cause of the problem",
  "ai_category": "one of: Hardware / Software / Network / Access / Other",
  "ai_priority": "one of: Critical / High / Medium / Low",
  "ai_confidence": 0.0 to 1.0,
  "ai_sla_rule": "exact SLA rule from knowledge base for this priority e.g. Response: 30 min, Resolution: 4 hrs",
  "ai_breach_penalty": "exact penalty from knowledge base e.g. ₹10,000 per breach",
  "ai_suggestion": "step by step SOP recommendation from knowledge base, each step on a new line starting with 1. 2. 3.",
  "ai_answer": "2-3 paragraph human readable answer explaining the issue, what SOP to follow, what SLA applies, and what happens if breached",
  "ai_decision": "one of: AUTO-FIX / ESCALATE / MONITOR / HUMAN-REVIEW"
}}
""".strip()


# ---------------- CALL OLLAMA ---------------- #
def call_ollama(prompt: str) -> str:
    try:
        response = requests.post(OLLAMA_URL, json={
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False
        }, timeout=OLLAMA_TIMEOUT)
        return response.json().get("response", "").strip()
    except Exception as e:
        logger.error(f"Ollama call failed: {e}")
        return ""


# ---------------- PARSE RESPONSE ---------------- #
def parse_response(raw: str) -> dict:
    try:
        clean = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        return json.loads(clean)
    except Exception as e:
        logger.warning(f"Failed to parse LLM response: {e}\nRaw: {raw}")
        return {
            "ai_issue":          "parse_error",
            "ai_category":       "Other",
            "ai_priority":       "Medium",
            "ai_confidence":     0.0,
            "ai_suggestion":     "Manual review required",
            "ai_sla_rule":       "Response: 2 hrs, Resolution: 8 hrs",
            "ai_breach_penalty": "₹5,000",
            "ai_answer":         "Could not generate analysis. Please review manually.",
            "ai_decision":       "HUMAN-REVIEW"
        }

# ---------------- SAVE TO DB ---------------- #
def save_ai_results(ticket_id: str, result: dict):
    conn = get_connection()
    conn.execute("""
        UPDATE tickets SET
            ai_issue          = ?,
            ai_category       = ?,
            ai_priority       = ?,
            ai_confidence     = ?,
            ai_suggestion     = ?,
            ai_sla_rule       = ?,
            ai_breach_penalty = ?,
            ai_answer         = ?,
            ai_decision       = ?
        WHERE ticket_id = ?
    """, (
        result.get("ai_issue"),
        result.get("ai_category"),
        result.get("ai_priority"),
        result.get("ai_confidence"),
        result.get("ai_suggestion"),
        result.get("ai_sla_rule"),
        result.get("ai_breach_penalty"),
        result.get("ai_answer"),
        result.get("ai_decision"),
        ticket_id
    ))
    conn.commit()
    logger.info(f"AI results saved for ticket {ticket_id}")


# ---------------- MAIN CLASSIFY ---------------- #
def classify_ticket(ticket: dict) -> dict:
    ticket_id = ticket.get("ticket_id", "unknown")
    logger.info(f"Classifying ticket {ticket_id}")

    sop_context = load_knowledge_base()
    prompt = build_prompt(ticket, sop_context)
    raw = call_ollama(prompt)

    if not raw:
        logger.warning(f"Empty response from Ollama for ticket {ticket_id}")
        result = {
            "ai_issue": "no_response",
            "ai_category": "Other",
            "ai_priority": "Medium",
            "ai_confidence": 0.0,
            "ai_suggestion": "Ollama unreachable — manual review",
            "ai_decision": "HUMAN-REVIEW"
        }
    else:
        result = parse_response(raw)

    save_ai_results(ticket_id, result)
    logger.info(f"Ticket {ticket_id} → decision: {result.get('ai_decision')} | confidence: {result.get('ai_confidence')}")
    return result


# ---------------- BATCH CLASSIFY ---------------- #
def classify_pending_tickets():
    conn = get_connection()
    rows = conn.execute("""
        SELECT * FROM tickets
        WHERE ai_decision IS NULL OR ai_decision = ''
    """).fetchall()

    logger.info(f"Found {len(rows)} unclassified tickets")

    for row in rows:
        ticket = dict(row)
        classify_ticket(ticket)