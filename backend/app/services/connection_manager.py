import uuid
import logging
from typing import Dict
from fastapi import WebSocket
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.booking import Booking
from app.models.resource import Resource

logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self):
        # Maps user_id_str -> WebSocket
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, user_id: str, ws: WebSocket):
        await ws.accept()
        self.active_connections[user_id] = ws
        logger.info("WebSocket connected for user %s", user_id)

    def disconnect(self, user_id: str):
        if user_id in self.active_connections:
            del self.active_connections[user_id]
            logger.info("WebSocket disconnected for user %s", user_id)

    async def send_to_user(self, user_id: str, message: dict):
        ws = self.active_connections.get(user_id)
        if ws:
            try:
                await ws.send_json(message)
            except Exception as e:
                logger.error("Failed to send WS message to %s: %s", user_id, e)
                self.disconnect(user_id)

    async def broadcast_to_booking(self, booking_id: uuid.UUID, message: dict, db: AsyncSession):
        result = await db.execute(
            select(Booking, Resource)
            .join(Resource, Booking.resource_id == Resource.id)
            .where(Booking.id == booking_id)
        )
        row = result.first()
        if row:
            booking, resource = row
            await self.send_to_user(str(booking.user_id), message)
            await self.send_to_user(str(resource.owner_id), message)


connection_manager = ConnectionManager()
