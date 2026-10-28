import uuid
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from app.models.chat import ChatRoom, ChatMessage
from app.models.booking import Booking
from app.services.connection_manager import connection_manager


async def get_or_create_room(booking_id: uuid.UUID, db: AsyncSession) -> ChatRoom:
    result = await db.execute(select(ChatRoom).where(ChatRoom.booking_id == booking_id))
    room = result.scalars().first()
    if not room:
        room = ChatRoom(booking_id=booking_id)
        db.add(room)
        await db.commit()
        await db.refresh(room)
    return room


async def send_message(
    booking_id: uuid.UUID,
    sender_id: uuid.UUID,
    content: str,
    attachment_url: Optional[str],
    db: AsyncSession,
) -> ChatMessage:
    room = await get_or_create_room(booking_id, db)
    msg = ChatMessage(
        room_id=room.id,
        sender_id=sender_id,
        content=content,
        attachment_url=attachment_url,
    )
    db.add(msg)
    await db.commit()
    await db.refresh(msg)

    # Broadcast to booking participants via WebSocket
    payload = {
        "type": "CHAT_MESSAGE",
        "room_id": str(room.id),
        "booking_id": str(booking_id),
        "sender_id": str(sender_id),
        "content": content,
        "attachment_url": attachment_url,
        "created_at": msg.created_at.isoformat(),
    }
    await connection_manager.broadcast_to_booking(booking_id, payload, db)
    return msg


async def get_messages(booking_id: uuid.UUID, db: AsyncSession) -> List[ChatMessage]:
    room = await get_or_create_room(booking_id, db)
    result = await db.execute(
        select(ChatMessage).where(ChatMessage.room_id == room.id).order_by(ChatMessage.created_at.asc())
    )
    return list(result.scalars().all())
