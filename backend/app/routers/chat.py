import uuid
from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.schemas.chat import ChatMessageCreate, ChatMessageResponse
from app.dependencies.auth import get_current_user
from app.services import chat_service

router = APIRouter()


@router.get("/{booking_id}/messages", response_model=List[ChatMessageResponse])
async def get_booking_chat_messages(
    booking_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await chat_service.get_messages(booking_id, db)


@router.post("/{booking_id}/messages", response_model=ChatMessageResponse)
async def post_chat_message(
    booking_id: uuid.UUID,
    body: ChatMessageCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await chat_service.send_message(
        booking_id=booking_id,
        sender_id=current_user.id,
        content=body.content,
        attachment_url=body.attachment_url,
        db=db,
    )
