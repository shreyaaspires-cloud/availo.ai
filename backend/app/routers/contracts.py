import uuid
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Request, Response
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.models.booking import Booking
from app.models.contract import Contract
from app.schemas.contract import (
    ContractResponse,
    ContractSignatureResponse,
    SignContractRequest,
    VerifyContractResponse,
)
from app.dependencies.auth import get_current_user, get_booking_participant
from app.services import contract_service
from app.services import receipt_service
from app.models.incident import IncidentReport, DamageClaim

router = APIRouter()


@router.get("/{booking_id}", response_model=ContractResponse)
async def get_contract_by_booking(
    booking_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await get_booking_participant(booking_id, current_user, db)
    result = await db.execute(
        select(Contract)
        .options(selectinload(Contract.signatures))
        .where(Contract.booking_id == booking_id)
    )
    contract = result.scalars().first()
    if not contract:
        # If booking is approved, auto-generate contract on demand if not yet generated
        booking = await db.get(Booking, booking_id)
        if booking and booking.status.value in ["APPROVED", "AWAITING_SIGNATURES", "AWAITING_PAYMENT", "CONFIRMED", "CHECKED_IN", "RETURN_SUBMITTED", "COMPLETED"]:
            contract = await contract_service.generate_contract(booking_id, db)
        else:
            raise HTTPException(status_code=404, detail="Contract not found for this booking")
    return contract


@router.get("/{booking_id}/pdf")
async def download_contract_pdf(
    booking_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generates and downloads the official Availo Rental Agreement PDF for authorized booking participants."""
    await get_booking_participant(booking_id, current_user, db)

    booking_res = await db.execute(
        select(Booking)
        .options(selectinload(Booking.resource), selectinload(Booking.user))
        .where(Booking.id == booking_id)
    )
    booking = booking_res.scalars().first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    owner_res = await db.execute(select(User).where(User.id == booking.resource.owner_id))
    owner = owner_res.scalars().first()

    contract_res = await db.execute(
        select(Contract)
        .options(selectinload(Contract.signatures))
        .where(Contract.booking_id == booking_id)
    )
    contract = contract_res.scalars().first()
    if not contract:
        contract = await contract_service.generate_contract(booking_id, db)

    # Render PDF bytes
    pdf_bytes = contract_service.generate_agreement_pdf_bytes(
        booking=booking,
        resource=booking.resource,
        borrower=booking.user,
        owner=owner,
        signatures=contract.signatures,
        document_hash=contract.sha256_hash,
    )

    clean_filename = f"Availo_Agreement_{str(booking.id)[:8]}_v1.pdf"

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename={clean_filename}",
            "Cache-Control": "private, max-age=3600",
        },
    )


@router.get("/{booking_id}/receipt/pdf")
async def download_closure_receipt_pdf(
    booking_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generates and downloads the official Availo Agreement Closure & Escrow Settlement PDF Receipt."""
    await get_booking_participant(booking_id, current_user, db)

    booking_res = await db.execute(
        select(Booking)
        .options(selectinload(Booking.resource), selectinload(Booking.user))
        .where(Booking.id == booking_id)
    )
    booking = booking_res.scalars().first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    # Receipt is only available once closure is confirmed / completed
    valid_closure_statuses = ["COMPLETED", "RESOLVED_USER", "RESOLVED_OWNER", "RESOLVED_SPLIT"]
    if booking.status.value not in valid_closure_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Settlement receipt is not available yet. Current booking status is {booking.status.value}. Receipt is issued upon agreement closure.",
        )

    owner_res = await db.execute(select(User).where(User.id == booking.resource.owner_id))
    owner = owner_res.scalars().first()

    contract_res = await db.execute(
        select(Contract)
        .options(selectinload(Contract.signatures))
        .where(Contract.booking_id == booking_id)
    )
    contract = contract_res.scalars().first()

    inc_res = await db.execute(
        select(IncidentReport)
        .options(selectinload(IncidentReport.claims))
        .where(IncidentReport.booking_id == booking_id)
    )
    incident = inc_res.scalars().first()
    claim = incident.claims[0] if incident and incident.claims else None

    # Render PDF Receipt
    pdf_bytes = receipt_service.generate_closure_receipt_pdf_bytes(
        booking=booking,
        resource=booking.resource,
        borrower=booking.user,
        owner=owner,
        contract=contract,
        incident=incident,
        claim=claim,
    )

    clean_filename = f"Availo_Receipt_{str(booking.id)[:8]}.pdf"

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename={clean_filename}",
            "Cache-Control": "private, max-age=3600",
        },
    )


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
