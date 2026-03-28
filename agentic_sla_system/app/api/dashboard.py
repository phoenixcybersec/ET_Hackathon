from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.api.ws_manager import manager
from app.ticketing.normalizer import normalize_ticket
from app.ticketing.store import upsert_ticket
from app.utils.logger import get_logger

router = APIRouter()
logger = get_logger()

# ---------------- WebSocket ----------------
@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# ---------------- Webhook ----------------
@router.post("/odoo/webhook")
async def odoo_webhook(data: dict):
    logger.info(f"Webhook received: {data}")

    ticket = normalize_ticket(data)
    upsert_ticket(ticket)

    await manager.broadcast({
        "event": "ticket_updated",
        "ticket_id": ticket["ticket_id"]
    })

    return {"status": "processed"}