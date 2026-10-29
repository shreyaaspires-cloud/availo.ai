import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.models.booking import Booking, BookingStatus
from app.models.incident import IncidentReport, IncidentStatus, DamageClaim, ClaimStatus, ClaimResolutionType
from app.schemas.incident import (
    IncidentReportResponse,
    DamageAssessmentResponse,
    DamageClaimCreate,
    DamageClaimResponse,
    DamageClaimResponseRequest,
    RepairSubmitRequest,
    DisputeResolveRequest,
    CloseupSubmitRequest,
)
from app.dependencies.auth import get_current_user, get_booking_participant, require_admin
from app.services import damage_service
from app.services.audit_service import log_transition
from app.services.notification_service import notify
from app.services.contract_closure_service import verify_and_close_contract

router = APIRouter()


@router.get("/{booking_id}/damage-assessment", response_model=IncidentReportResponse)
async def get_incident_damage_assessment(
    booking_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await get_booking_participant(booking_id, current_user, db)
    result = await db.execute(
        select(IncidentReport)
        .options(selectinload(IncidentReport.assessments), selectinload(IncidentReport.claims))
        .where(IncidentReport.booking_id == booking_id)
    )
    incident = result.scalars().first()
    if not incident:
        raise HTTPException(status_code=404, detail="No damage assessment recorded for this booking")
    return incident


@router.post("/{booking_id}/claims", response_model=DamageClaimResponse)
async def submit_owner_damage_claim(
    booking_id: uuid.UUID,
    body: DamageClaimCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Allows equipment owner to submit a formal damage claim with evidence and repair quotation."""
    booking = await get_booking_participant(booking_id, current_user, db)
    if booking.resource.owner_id != current_user.id and "ADMIN" not in current_user.roles:
        raise HTTPException(status_code=403, detail="Only the resource owner can submit damage claims")

    inc_res = await db.execute(
        select(IncidentReport)
        .options(selectinload(IncidentReport.claims))
        .where(IncidentReport.booking_id == booking_id)
    )
    incident = inc_res.scalars().first()
    if not incident:
        incident = IncidentReport(
            booking_id=booking_id,
            raised_by_id=current_user.id,
            status=IncidentStatus.OPEN,
        )
        db.add(incident)
        await db.commit()
        await db.refresh(incident)

    # Check for duplicate active claims
    for existing in getattr(incident, "claims", []):
        if existing.status in [ClaimStatus.SUBMITTED, ClaimStatus.RESEARCHER_REVIEW, ClaimStatus.DISPUTED]:
            raise HTTPException(
                status_code=400,
                detail="An active damage claim is already pending resolution for this booking",
            )

    claim = DamageClaim(
        incident_id=incident.id,
        claimant_id=current_user.id,
        description=body.description,
        photo_angles=body.photo_angles,
        justification=body.justification,
        estimated_cost=body.estimated_cost,
        invoice_url=body.invoice_url,
        requested_resolution=body.requested_resolution,
        status=ClaimStatus.RESEARCHER_REVIEW,
    )
    db.add(claim)

    # Move booking to DAMAGE_REVIEW
    booking.status = BookingStatus.DAMAGE_REVIEW
    incident.status = IncidentStatus.OPEN
    await db.commit()
    await db.refresh(claim)

    await log_transition(
        action="DAMAGE_CLAIM_SUBMITTED",
        booking_id=booking_id,
        user_id=current_user.id,
        previous_status=booking.status.value,
        new_status=BookingStatus.DAMAGE_REVIEW.value,
        db=db,
        metadata={"estimated_cost": str(body.estimated_cost), "resolution": body.requested_resolution.value},
    )

    # Notify researcher
    await notify(
        user_id=booking.user_id,
        type="DAMAGE_CLAIM_SUBMITTED",
        title="Action Required: Damage Claim Submitted",
        body=f"The equipment owner submitted a damage claim ({body.requested_resolution.value}). Please review and respond.",
        booking_id=booking.id,
        db=db,
    )

    return claim


@router.post("/claims/{claim_id}/respond", response_model=DamageClaimResponse)
async def respond_to_damage_claim(
    claim_id: uuid.UUID,
    body: DamageClaimResponseRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Allows researcher to accept, counter, or dispute the claim with evidence."""
    claim_res = await db.execute(
        select(DamageClaim)
        .options(selectinload(DamageClaim.incident).selectinload(IncidentReport.booking))
        .where(DamageClaim.id == claim_id)
    )
    claim = claim_res.scalars().first()
    if not claim:
        raise HTTPException(status_code=404, detail="Damage claim not found")

    booking = claim.incident.booking
    if booking.user_id != current_user.id and "ADMIN" not in current_user.roles:
        raise HTTPException(status_code=403, detail="Only the researcher can respond to this claim")

    now = datetime.now(timezone.utc)
    claim.researcher_response = body.action
    claim.researcher_note = body.note
    claim.researcher_counter_amount = body.counter_amount
    claim.researcher_evidence_url = body.evidence_url
    claim.responded_at = now

    if body.action == "ACCEPT":
        claim.status = ClaimStatus.ACCEPTED
        claim.agreed_compensation = claim.estimated_cost
        claim.settled_at = now
        claim.payment_reference = f"ESCROW_DEDUCT_{str(uuid.uuid4())[:8]}"
        claim.incident.status = IncidentStatus.RESOLVED_OWNER
        await log_transition("CLAIM_ACCEPTED", booking.id, current_user.id, None, "ACCEPTED", db)
    elif body.action == "COUNTER":
        claim.status = ClaimStatus.RESEARCHER_REVIEW
        claim.agreed_compensation = body.counter_amount
        await log_transition("CLAIM_COUNTERED", booking.id, current_user.id, None, "COUNTERED", db)
    elif body.action == "DISPUTE":
        claim.status = ClaimStatus.DISPUTED
        claim.incident.status = IncidentStatus.OPEN
        booking.status = BookingStatus.DISPUTE_OPEN
        await log_transition("CLAIM_DISPUTED", booking.id, current_user.id, None, "DISPUTED", db)

    await db.commit()
    await db.refresh(claim)

    # Notify owner
    resource_owner_id = booking.resource_id  # fetch owner
    b_full = (await db.execute(select(Booking).options(selectinload(Booking.resource)).where(Booking.id == booking.id))).scalars().first()
    if b_full and b_full.resource:
        await notify(
            user_id=b_full.resource.owner_id,
            type="CLAIM_RESPONDED",
            title=f"Damage Claim {body.action}",
            body=f"Researcher responded: {body.action}. Note: {body.note}",
            booking_id=booking.id,
            db=db,
        )

    return claim


@router.post("/claims/{claim_id}/withdraw", response_model=DamageClaimResponse)
async def withdraw_damage_claim(
    claim_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Allows owner to voluntarily withdraw claim."""
    claim = await db.get(DamageClaim, claim_id)
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")

    if claim.claimant_id != current_user.id and "ADMIN" not in current_user.roles:
        raise HTTPException(status_code=403, detail="Only the claimant or admin can withdraw this claim")

    claim.status = ClaimStatus.WITHDRAWN
    claim.settled_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(claim)
    return claim


@router.post("/claims/{claim_id}/repair-verify", response_model=DamageClaimResponse)
async def verify_repair_completion(
    claim_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Allows owner or admin to verify repair completion."""
    claim = await db.get(DamageClaim, claim_id)
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")

    claim.repair_verified_by_id = current_user.id
    claim.repair_verified_at = datetime.now(timezone.utc)
    claim.status = ClaimStatus.RESOLVED
    await db.commit()
    await db.refresh(claim)
    return claim


@router.post("/{booking_id}/close-contract")
async def trigger_contract_closure(
    booking_id: uuid.UUID,
    closure_reason: Optional[str] = "Normal completion after verified return and condition inspection",
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Executes the contract closure gate, validating all criteria before closing contract."""
    from app.dependencies.auth import get_booking_participant
    booking = await get_booking_participant(booking_id, current_user, db)
    return await verify_and_close_contract(
        booking_id=booking_id,
        actor_id=current_user.id,
        closure_reason=closure_reason,
        db=db,
    )


@router.post("/{booking_id}/closeup")
async def submit_closeup_photo(
    booking_id: uuid.UUID,
    body: CloseupSubmitRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.dependencies.auth import get_booking_participant
    booking = await get_booking_participant(booking_id, current_user, db)
    if booking.user_id != current_user.id and "ADMIN" not in current_user.roles:
        raise HTTPException(status_code=403, detail="Only the booking user can submit close-up photos")
    await damage_service.submit_closeup(booking_id, body.angle.value, body.image_url, db)
    return {"message": "Closeup image saved"}
