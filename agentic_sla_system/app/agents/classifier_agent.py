import json
import os
import re
import requests

from app.config.loader import load_config
from app.db.database import get_connection
from app.utils.logger import get_logger

logger = get_logger()
config = load_config()

KB_PATH = config["knowledge_base"]["path"]


# ================================================================
# 1. LOAD KNOWLEDGE BASE
# ================================================================
def load_knowledge_base() -> str:
    context = ""
    try:
        for filename in sorted(os.listdir(KB_PATH)):
            if filename.endswith((".md", ".txt")):
                filepath = os.path.join(KB_PATH, filename)
                with open(filepath, "r", encoding="utf-8") as f:
                    context += f"\n\n### {filename}\n{f.read()}"
        logger.info(f"Knowledge base loaded: {len(context)} chars")
    except Exception as e:
        logger.error(f"Failed to load knowledge base: {e}")
    return context.strip()


# ================================================================
# 2. BUILD PROMPT
# ================================================================
def build_prompt(ticket: dict, sop_context: str) -> str:
    return f"""
You are an expert IT helpdesk classifier. Analyze the ticket and knowledge base below.
Respond ONLY in valid JSON. IMPORTANT: escape all newlines as \\n inside string values.
Never use real line breaks inside JSON string values.

--- TICKET ---
Subject: {ticket.get('subject', '')}
Description: {ticket.get('description', '')}
Helpdesk Team: {ticket.get('helpdesk_team', '')}
Priority: {ticket.get('priority', '')}

--- KNOWLEDGE BASE (SOPs & SLA Rules) ---
{sop_context}

--- TASK ---
Return ONLY this JSON object. Use \\n for line breaks inside strings. No extra text:
{{
  "ai_issue": "one line root cause of the problem",
  "ai_category": "one of: Hardware / Software / Network / Access / Other",
  "ai_priority": "one of: Critical / High / Medium / Low",
  "ai_confidence": 0.0,
  "ai_sla_rule": "exact SLA from knowledge base e.g. Response: 30 min, Resolution: 4 hrs",
  "ai_breach_penalty": "exact penalty from knowledge base e.g. Rs.10000 per breach",
  "ai_suggestion": "1. step one\\n2. step two\\n3. step three\\n4. step four",
  "ai_answer": "paragraph explaining root cause\\n\\nparagraph explaining SOP to follow\\n\\nparagraph explaining SLA and breach consequence",
  "ai_decision": "one of: AUTO-FIX / ESCALATE / MONITOR / HUMAN-REVIEW"
}}
""".strip()


# ================================================================
# 3. CALL LLM
# ================================================================
def call_llm(prompt: str) -> str:
    llm = config["llm"]

    provider = llm.get("provider", "")
    if provider != "openai":
        logger.error(f"Unsupported LLM provider '{provider}'.")
        return ""

    api_key         = llm.get("api_key", "")
    model           = llm.get("model", "gpt-4o-mini")
    temperature     = llm.get("temperature", 0.1)
    max_tokens      = llm.get("max_tokens", 1000)
    timeout         = llm.get("timeout", 60)
    response_format = llm.get("response_format", "json_object")
    system_prompt   = llm.get(
        "system_prompt",
        "You are an IT helpdesk classifier. Always respond with valid JSON only. "
        "Never include markdown fences or extra text."
    )

    if not api_key or api_key.startswith("sk-..."):
        logger.error("OpenAI API key missing in config.yaml")
        return ""

    try:
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type":  "application/json",
            },
            json={
                "model":           model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user",   "content": prompt},
                ],
                "temperature":     temperature,
                "max_tokens":      max_tokens,
                "response_format": {"type": response_format},
            },
            timeout=timeout
        )

        logger.info(f"OpenAI status: {response.status_code}")
        data = response.json()

        if "error" in data:
            logger.error(f"OpenAI API error: {data['error']}")
            return ""

        if "choices" not in data or not data["choices"]:
            logger.error(f"Unexpected OpenAI response: {data}")
            return ""

        content = data["choices"][0]["message"]["content"].strip()
        finish  = data["choices"][0].get("finish_reason", "unknown")

        if finish != "stop":
            logger.warning(f"OpenAI finish_reason='{finish}' — may be truncated")

        usage = data.get("usage", {})
        logger.info(
            f"OpenAI usage — model: {model} | "
            f"prompt_tokens: {usage.get('prompt_tokens', '?')} | "
            f"completion_tokens: {usage.get('completion_tokens', '?')} | "
            f"total_tokens: {usage.get('total_tokens', '?')}"
        )
        return content

    except requests.exceptions.Timeout:
        logger.error(f"OpenAI timed out after {timeout}s")
        return ""
    except requests.exceptions.ConnectionError as e:
        logger.error(f"OpenAI connection error: {e}")
        return ""
    except Exception as e:
        logger.error(f"OpenAI call failed: {e}")
        return ""


# ================================================================
# 4. PARSE RESPONSE
# ================================================================
def parse_response(raw: str) -> dict:
    fallback = {
        "ai_issue":          "parse_error",
        "ai_category":       "Other",
        "ai_priority":       "Medium",
        "ai_confidence":     0.0,
        "ai_suggestion":     "Manual review required",
        "ai_sla_rule":       "Response: 2 hrs, Resolution: 8 hrs",
        "ai_breach_penalty": "Rs.5,000",
        "ai_answer":         "Could not generate analysis. Please review manually.",
        "ai_decision":       "HUMAN-REVIEW"
    }

    if not raw:
        return fallback

    try:
        clean = raw.strip()
        clean = re.sub(r"^```json\s*", "", clean)
        clean = re.sub(r"^```\s*",     "", clean)
        clean = re.sub(r"\s*```$",     "", clean)
        clean = clean.strip()

        start = clean.find("{")
        end   = clean.rfind("}")
        if start == -1 or end == -1:
            raise ValueError("No JSON object found")
        clean = clean[start:end + 1]

        def fix_string_values(m):
            s = m.group(0)
            s = s.replace("\n", "\\n")
            s = s.replace("\r", "\\r")
            s = s.replace("\t", "\\t")
            return s

        clean = re.sub(r'"(?:[^"\\]|\\.)*"', fix_string_values, clean, flags=re.DOTALL)
        clean = re.sub(r'(["\d\]}\s])\s*\n(\s*")', r'\1,\n\2', clean)

        return json.loads(clean)

    except Exception as e:
        logger.warning(f"Failed to parse LLM response: {e}\nRaw: {raw[:400]}")
        return fallback


# ================================================================
# 5. CALCULATE CONFIDENCE
# ================================================================
def calculate_confidence(result: dict, ticket: dict) -> float:
    score = 0.0
    breakdown = []

    if result.get("ai_category") in {"Hardware", "Software", "Network", "Access", "Other"}:
        score += 0.25; breakdown.append("category:+0.25")
    else:
        breakdown.append("category:0")

    if result.get("ai_priority") in {"Critical", "High", "Medium", "Low"}:
        score += 0.20; breakdown.append("priority:+0.20")
    else:
        breakdown.append("priority:0")

    issue = result.get("ai_issue", "") or ""
    if len(issue.strip()) > 10 and issue != "parse_error":
        score += 0.20; breakdown.append("issue:+0.20")
    else:
        breakdown.append("issue:0")

    suggestion = result.get("ai_suggestion", "") or ""
    steps = [s.strip() for s in suggestion.replace("\\n", "\n").split("\n") if s.strip()]
    if len(steps) >= 2:
        score += 0.20; breakdown.append("steps:+0.20")
    else:
        breakdown.append("steps:0")

    description = ticket.get("description", "") or ""
    if len(description.strip()) > 10:
        score += 0.15; breakdown.append("desc:+0.15")
    else:
        breakdown.append("desc:0")

    final = round(min(score, 1.0), 2)
    logger.info(f"Confidence: {final} | {' | '.join(breakdown)}")
    return final


# ================================================================
# 6. SAVE TO DB  — sets is_classified = 1 so sync loop never re-runs this ticket
# ================================================================
def save_ai_results(ticket_id: str, result: dict):
    conn = get_connection()
    cursor = conn.execute("""
        UPDATE tickets SET
            ai_issue          = ?,
            ai_category       = ?,
            ai_priority       = ?,
            ai_confidence     = ?,
            ai_suggestion     = ?,
            ai_sla_rule       = ?,
            ai_breach_penalty = ?,
            ai_answer         = ?,
            ai_decision       = ?,
            is_classified     = 1
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

    if cursor.rowcount == 0:
        logger.error(f"Save failed — ticket {ticket_id} not found in DB")
    else:
        logger.info(f"AI results saved for ticket {ticket_id}")


# ================================================================
# 7. CLASSIFY ONE TICKET
# ================================================================
def classify_ticket(ticket: dict) -> dict:
    ticket_id = ticket.get("ticket_id", "unknown")
    logger.info(f"Classifying ticket {ticket_id}")

    sop_context = load_knowledge_base()
    prompt      = build_prompt(ticket, sop_context)
    raw         = call_llm(prompt)
    result      = parse_response(raw)

    result["ai_confidence"] = calculate_confidence(result, ticket)

    save_ai_results(ticket_id, result)
    logger.info(
        f"Ticket {ticket_id} → "
        f"decision: {result.get('ai_decision')} | "
        f"confidence: {result.get('ai_confidence')}"
    )
    return result


# ================================================================
# 8. BATCH — skips any ticket that has already passed the classifier
# ================================================================
def classify_pending_tickets() -> int:
    from app.db.database import get_connection
    from app.utils.logger import get_logger
    logger = get_logger()
 
    conn = get_connection()
    rows = conn.execute("""
        SELECT * FROM tickets
        WHERE is_classified = 0 OR is_classified IS NULL
    """).fetchall()
 
    if not rows:
        logger.info("No unclassified tickets — skipping")
        return 0                      # ← tells main.py to skip decision agent
 
    logger.info(f"Found {len(rows)} unclassified tickets")
    for row in rows:
        classify_ticket(dict(row))
 
    return len(rows) 