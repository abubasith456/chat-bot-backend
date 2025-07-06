from fastapi import WebSocket
from typing import List, Literal
import logging
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class StateData(BaseModel):
    model_name: str


class ResponseData(BaseModel):
    type: Literal["response", "error"]
    message: str


class ConnectionManager:
    def __init__(self):
        self.active: List[WebSocket] = []
        self.state: StateData = StateData(model_name="microsoft/phi-4-mini-instruct")

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active.append(ws)

    def disconnect(self, ws: WebSocket):
        self.active.remove(ws)

    async def send_personal(self, ws: WebSocket, message: str):
        await ws.send_text(message)

    async def send_message(self, ws: WebSocket, responseData: ResponseData):
        """Send a message to all connected clients"""
        if not self.active:
            logger.warning("No active WebSocket connections to send message.")
            return
        message = (
            responseData.model_dump_json()
            if isinstance(responseData, BaseModel)
            else responseData
        )
        await ws.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active:
            await connection.send_text(message)


manager = ConnectionManager()
