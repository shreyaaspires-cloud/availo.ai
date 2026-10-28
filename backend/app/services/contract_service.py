import io
import hashlib
import base64
import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.models.booking import Booking, BookingStatus
from app.models.contract import Contract, ContractSignature, ContractStatus, ContractSignerRole
from app.models.resource import Resource
from app.models.user import User
from app.services.gemini_service import generate_contract_html
from app.services.audit_service import log_transition
from app.services.notification_service import notify_contract_ready
from app.storage.supabase_storage import upload_file

# Attempt import WeasyPrint; fallback to mock/html wrapper if native GTK/pango libraries not present on host OS
try:
    from weasyprint import HTML
    WEASYPRINT_AVAILABLE = True
except Exception:
    WEASYPRINT_AVAILABLE = False


async def generate_contract(booking_id: uuid.UUID, db: AsyncSession) -> Contract:
    # 1. Load booking + resource + user + owner
    result = await db.execute(
        select(Booking)
        .options(selectinload(Booking.resource), selectinload(Booking.user))
        .where(Booking.id == booking_id)
    )
    booking = result.scalars().first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    owner_res = await db.execute(select(User).where(User.id == booking.resource.owner_id))
    owner = owner_res.scalars().first()

    # 2. Build structured data for contract
    days = max(1, (booking.end_dt - booking.start_dt).days)
    booking_data = {
        "booking_id": str(booking.id),
        "resource_title": booking.resource.title,
        "location": booking.resource.location,
        "owner_name": owner.full_name if owner else "Owner",
        "owner_email": owner.email if owner else "",
        "user_name": booking.user.full_name,
        "user_email": booking.user.email,
        "start_dt": booking.start_dt.strftime("%Y-%m-%d %H:%M"),
        "end_dt": booking.end_dt.strftime("%Y-%m-%d %H:%M"),
        "purpose": booking.purpose,
        "days": days,
        "daily_rate": str(booking.resource.daily_rate),
        "total_amount": str(booking.total_amount),
        "deposit_amount": str(booking.deposit_amount),
    }

    # 3. Generate HTML via Gemini
    html_content = await generate_contract_html(booking_data)

    # 4. Render HTML to PDF and compute SHA256
    pdf_bytes: bytes
    if WEASYPRINT_AVAILABLE:
        try:
            pdf_bytes = HTML(string=html_content).write_pdf()
        except Exception:
            pdf_bytes = html_content.encode("utf-8")
    else:
        pdf_bytes = html_content.encode("utf-8")

    sha256_hash = hashlib.sha256(pdf_bytes).hexdigest()

    # 5. Upload to Supabase Storage
    path = f"contracts/{booking.id}/contract_{sha256_hash[:8]}.pdf"
    pdf_url = await upload_file(pdf_bytes, "contracts", path, content_type="application/pdf")

    # 6. Check existing contract or create new
    existing_res = await db.execute(select(Contract).where(Contract.booking_id == booking_id))
    contract = existing_res.scalars().first()
    if not contract:
        contract = Contract(
            booking_id=booking_id,
            content_html=html_content,
            pdf_url=pdf_url,
            sha256_hash=sha256_hash,
            status=ContractStatus.PENDING_SIGNATURES,
        )
        db.add(contract)
    else:
        contract.content_html = html_content
        contract.pdf_url = pdf_url
        contract.sha256_hash = sha256_hash
        contract.status = ContractStatus.PENDING_SIGNATURES

    await db.commit()
    await db.refresh(contract)

    # 7. Notify both parties
    if owner:
        await notify_contract_ready(booking.user_id, owner.id, contract.id, booking.id, db)

    await log_transition(
        action="CONTRACT_GENERATED",
        booking_id=booking.id,
        user_id=None,
        previous_status=None,
        new_status=ContractStatus.PENDING_SIGNATURES.value,
        db=db,
        metadata={"sha256_hash": sha256_hash},
    )

    return contract


async def collect_signature(
    contract_id: uuid.UUID,
    user_id: uuid.UUID,
    signature_image_base64: str,
    ip: Optional[str],
    ua: Optional[str],
    db: AsyncSession,
) -> ContractSignature:
    result = await db.execute(
        select(Contract)
        .options(selectinload(Contract.booking), selectinload(Contract.signatures))
        .where(Contract.id == contract_id)
    )
    contract = result.scalars().first()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    booking = contract.booking
    resource_res = await db.execute(select(Resource).where(Resource.id == booking.resource_id))
    resource = resource_res.scalars().first()

    # Determine signer role
    if user_id == booking.user_id:
        role = ContractSignerRole.USER
    elif resource and user_id == resource.owner_id:
        role = ContractSignerRole.OWNER
    else:
        raise HTTPException(status_code=403, detail="User is not authorized to sign this contract")

    # Clean base64 image and upload
    raw_b64 = signature_image_base64
    if "," in raw_b64:
        raw_b64 = raw_b64.split(",", 1)[1]
    sig_bytes = base64.b64decode(raw_b64)
    sig_path = f"contracts/{contract_id}/{user_id}_{role.value}_sig.png"
    sig_url = await upload_file(sig_bytes, "contracts", sig_path, content_type="image/png")

    # Save ContractSignature record
    signature = ContractSignature(
        contract_id=contract_id,
        user_id=user_id,
        role_in_contract=role,
        signature_image_url=sig_url,
        ip_address=ip,
        user_agent=ua,
    )
    db.add(signature)
    await db.commit()

    # Re-evaluate signatures
    sig_res = await db.execute(
        select(ContractSignature).where(ContractSignature.contract_id == contract_id)
    )
    all_sigs = list(sig_res.scalars().all())
    roles_signed = {s.role_in_contract for s in all_sigs}

    if ContractSignerRole.USER in roles_signed and ContractSignerRole.OWNER in roles_signed:
        contract.status = ContractStatus.SIGNED
        prev_booking_status = booking.status.value
        booking.status = BookingStatus.AWAITING_PAYMENT
        await db.commit()
        await log_transition(
            action="CONTRACT_FULLY_SIGNED",
            booking_id=booking.id,
            user_id=user_id,
            previous_status=prev_booking_status,
            new_status=BookingStatus.AWAITING_PAYMENT.value,
            db=db,
        )

    return signature


async def verify_contract_integrity(contract_id: uuid.UUID, pdf_bytes: bytes, db: AsyncSession) -> Dict[str, Any]:
    contract = await db.get(Contract, contract_id)
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    provided_hash = hashlib.sha256(pdf_bytes).hexdigest()
    is_valid = (provided_hash == contract.sha256_hash)
    return {
        "status": "VALID" if is_valid else "TAMPERED",
        "stored_hash": contract.sha256_hash,
        "provided_hash": provided_hash,
    }
