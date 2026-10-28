import uuid
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.models.contract import Contract
from app.schemas.contract import (
    ContractResponse,
    ContractSignatureResponse,
    SignContractRequest,
    VerifyContractResponse,
)
from app.dependencies.auth import get_current_user
from app.services import contract_service

router = APIRouter()


@router.get("/{booking_id}", response_model=ContractResponse)
async def get_contract_by_booking(
    booking_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.dependencies.auth import get_booking_participant
    await get_booking_participant(booking_id, current_user, db)
    result = await db.execute(
        select(Contract)
        .options(selectinload(Contract.signatures))
        .where(Contract.booking_id == booking_id)
    )
    contract = result.scalars().first()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found for this booking")
    return contract


@router.post("/{id}/sign", response_model=ContractSignatureResponse)
async def sign_contract(
    id: uuid.UUID,
    body: SignContractRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    ip = request.client.host if request.client else None
    ua = request.headers.get("user-agent")
    return await contract_service.collect_signature(
        contract_id=id,
        user_id=current_user.id,
        signature_image_base64=body.signature_image_base64,
        ip=ip,
        ua=ua,
        db=db,
    )


@router.post("/{id}/verify", response_model=VerifyContractResponse)
async def verify_contract(
    id: uuid.UUID,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    pdf_bytes = await file.read()
    return await contract_service.verify_contract_integrity(id, pdf_bytes, db)
