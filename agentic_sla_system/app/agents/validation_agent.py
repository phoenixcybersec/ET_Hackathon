import json
import re

from openai import OpenAI
from app.db.database import get_connection
from app.config.loader import load_config
from app.utils.logger import get_logger

logger = get_logger()
cfg = load_config()

# ============================================================
# LOAD API KEY (CONFIG DRIVEN)
# ============================================================
_api_key = cfg.get("llm", {}).get("api_key")
if not _api_key:
    raise RuntimeError("Missing OpenAI API key in config under llm.api_key")

client = OpenAI(api_key=_api_key)

# ============================================================
# SYSTEM PROMPT
# ============================================================
SYSTEM_PROMPT = """You are an infrastructure validation agent.

Given an issue description and execution logs, determine if the issue is resolved.

Respond ONLY with valid JSON:
{
  "resolved": true | false,
  "confidence": "high" | "medium" | "low",
  "summary": "<one short explanation>"
}
"""

# ============================================================
# SAFE JSON PARSER
# ============================================================
def _parse_llm_response(raw: str) -> dict:
    clean = re.sub(r"```(?:json)?|```", "", raw).strip()

    try:
        data = json.loads(clean)
        return {
            "resolved": bool(data.get("resolved", False)),
            "summary": data.get("summary", raw[:300])
        }
    except Exception:
        logger.warning(f"LLM JSON parse failed. Raw: {raw[:200]}")
        return {
            "resolved": False,
            "summary": raw[:300]
        }

# ============================================================
# MAIN VALIDATION AGENT
# ============================================================
def run_validation_agent():
    conn = get_connection()

    # ✅ FIXED QUERY (THIS WAS YOUR MAIN BUG)
    rows = conn.execute("""
        SELECT * FROM tickets
        WHERE execution_status IS NOT NULL
        AND verified IS NULL
    """).fetchall()

    logger.info(f"Validation fetched {len(rows)} tickets")

    for t in rows:
        ticket_id = t["ticket_id"]
        status = t["execution_status"]

        try:
            # ====================================================
            # HANDLE NON-LLM CASES FIRST
            # ====================================================
            if status == "FAILED":
                conn.execute("""
                    UPDATE tickets SET
                        verification_result='FAILED',
                        verification_notes='Execution failed — issue not resolved',
                        verified=0
                    WHERE ticket_id=?
                """, (ticket_id,))
                conn.commit()
                logger.info(f"Ticket {ticket_id} → FAILED (no LLM)")
                continue

            if status == "ESCALATED":
                conn.execute("""
                    UPDATE tickets SET
                        verification_result='ESCALATED',
                        verification_notes='Requires human intervention',
                        verified=0
                    WHERE ticket_id=?
                """, (ticket_id,))
                conn.commit()
                logger.info(f"Ticket {ticket_id} → ESCALATED")
                continue

            # ====================================================
            # LLM VALIDATION (SUCCESS / PARTIAL_SUCCESS)
            # ====================================================
            response = client.chat.completions.create(
                model=cfg.get("llm", {}).get("model", "gpt-4o-mini"),
                temperature=0,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": (
                        f"Issue: {t['ai_issue']}\n"
                        f"Execution status: {status}\n"
                        f"Execution output:\n{t['execution_output']}"
                    )}
                ]
            )

            raw = response.choices[0].message.content
            parsed = _parse_llm_response(raw)

            resolved = parsed["resolved"]
            summary = parsed["summary"]

            conn.execute("""
                UPDATE tickets SET
                    verification_result=?,
                    verification_notes=?,
                    verified=?
                WHERE ticket_id=?
            """, (
                "RESOLVED" if resolved else "FAILED",
                summary,
                1 if resolved else 0,
                ticket_id
            ))
            conn.commit()

            logger.info(f"Ticket {ticket_id} validated → {'RESOLVED' if resolved else 'FAILED'}")

        except Exception as e:
            logger.error(f"Validation failed for ticket {ticket_id}: {e}")

            conn.execute("""
                UPDATE tickets SET
                    verification_result='ERROR',
                    verification_notes=?,
                    verified=0
                WHERE ticket_id=?
            """, (str(e)[:500], ticket_id))
            conn.commit()

    conn.close()