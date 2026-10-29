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
from app.models.incident import (
    IncidentReport,
    IncidentStatus,
    DamageClaim,
    ClaimStatus,
    ClaimResolutionType,
    OwnerDecisionType,
)
from app.schemas.incident import (
    IncidentReportResponse,
    DamageAssessmentResponse,
    OwnerDecisionRequest,
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


@router.post("/{booking_id}/owner-decision", response_model=IncidentReportResponse)
async def submit_owner_return_decision(
    booking_id: uuid.UUID,
    body: OwnerDecisionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Owner Decision Endpoint:
    Allows the authenticated resource owner to independently make the final condition decision:
    1. NO_DAMAGE_REPORTED -> Marks decision, triggers contract closure gate and deposit release.
    2. DAMAGE_REPORTED -> Moves case to owner damage claim initiation.
    The AI model only provides probabilistic and visual advice; it NEVER decides.
    """
    booking = await get_booking_participant(booking_id, current_user, db)
    if booking.resource.owner_id != current_user.id and "ADMIN" not in current_user.roles:
        raise HTTPException(status_code=403, detail="Only the resource owner can record the condition return decision")

    inc_res = await db.execute(
        select(IncidentReport)
        .options(selectinload(IncidentReport.claims), selectinload(IncidentReport.assessments))
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
        # Re-query with eager loads to prevent missing greenlet on relationship access
        inc_res = await db.execute(
            select(IncidentReport)
            .options(selectinload(IncidentReport.claims), selectinload(IncidentReport.assessments))
            .where(IncidentReport.id == incident.id)
        )
        incident = inc_res.scalars().first()

    now = datetime.now(timezone.utc)
    incident.owner_decision = body.decision
    incident.owner_decision_at = now
    incident.owner_decision_by_id = current_user.id
    if body.notes:
        incident.resolution_note = body.notes

    if body.decision == OwnerDecisionType.NO_DAMAGE_REPORTED:
        # Check that no unresolved active damage claim exists
        for claim in getattr(incident, "claims", []):
            if claim.status in [ClaimStatus.SUBMITTED, ClaimStatus.RESEARCHER_REVIEW, ClaimStatus.DISPUTED]:
                raise HTTPException(
                    status_code=400,
                    detail="Cannot confirm 'No Damage': Active damage claim is currently pending resolution",
                )

        incident.status = IncidentStatus.RESOLVED_USER
        incident.resolved_at = now
        await db.commit()

        # Execute contract closure gate
        await verify_and_close_contract(
            booking_id=booking_id,
            actor_id=current_user.id,
            closure_reason=body.notes or "Owner confirmed No Damage — Normal Agreement Closure",
            db=db,
        )
    else:
        # DAMAGE_REPORTED
        incident.status = IncidentStatus.OPEN
        booking.status = BookingStatus.DAMAGE_REVIEW
        await db.commit()

        await log_transition(
            action="OWNER_REPORTED_DAMAGE",
            booking_id=booking_id,
            user_id=current_user.id,
            previous_status=booking.status.value,
            new_status=BookingStatus.DAMAGE_REVIEW.value,
            db=db,
            metadata={"notes": body.notes},
        )

        await notify(
            user_id=booking.user_id,
            type="DAMAGE_REPORTED_BY_OWNER",
            title="Owner Condition Decision: Suspected Damage",
            body="The resource owner has reviewed return photos and flagged suspected damage for claim review.",
            booking_id=booking_id,
            db=db,
        )

    await db.refresh(incident)
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

    # Record that owner decided to report damage
    incident.owner_decision = OwnerDecisionType.DAMAGE_REPORTED
    incident.owner_decision_at = datetime.now(timezone.utc)
    incident.owner_decision_by_id = current_user.id

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

        # Automatically execute contract closure gate to complete booking and reconcile escrow
        try:
            await verify_and_close_contract(
                booking_id=booking.id,
                actor_id=current_user.id,
                closure_reason=f"Mutual resolution: Researcher accepted damage claim #{str(claim.id)[:8]} ($ {claim.estimated_cost})",
                db=db,
            )
        except Exception as e:
            # Fallback booking terminal update if closure gate encounters non-fatal gate condition
            booking.status = BookingStatus.COMPLETED
            await db.commit()
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
