from fastapi import WebSocket
from app.utils.logger import get_logger

logger = get_logger()

class ConnectionManager:
    def __init__(self):
        self.active_connections = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info("WebSocket connected")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        logger.info("WebSocket disconnected")

    async def broadcast(self, message: dict):
        logger.info(f"Broadcasting message: {message}")

        for connection in self.active_connections:
            await connection.send_json(message)

manager = ConnectionManager()