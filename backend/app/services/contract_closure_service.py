import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Dict, Any, Optional
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.booking import Booking, BookingStatus
from app.models.contract import Contract, ContractStatus, ContractSignature, ContractSignerRole
from app.models.incident import IncidentReport, IncidentStatus, DamageClaim, ClaimStatus
from app.models.condition_report import ConditionReport, ReportType
from app.models.user import User
from app.services.audit_service import log_transition
from app.services.notification_service import notify, notify_escrow_released


async def verify_and_close_contract(
    booking_id: uuid.UUID,
    actor_id: uuid.UUID,
    closure_reason: str,
    db: AsyncSession,
) -> Dict[str, Any]:
    """
    Contract Closure Gate:
    Strictly verifies all prerequisite conditions before closing a contract:
    1. Agreement signatures are complete (both User and Owner signed).
    2. Check-out return photos recorded (all 6 canonical angles).
    3. Inspection and condition review completed without open disputes.
    4. Any damage claims are resolved (or no claims exist).
    5. Required repair or compensation obligations fulfilled.
    6. Applicable deposit release processed or recorded.
    """
    booking = await db.get(Booking, booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    # Already closed check (idempotent)
    contract_res = await db.execute(
        select(Contract)
        .options(selectinload(Contract.signatures))
        .where(Contract.booking_id == booking_id)
    )
    contract = contract_res.scalars().first()
    if not contract:
        raise HTTPException(status_code=400, detail="Cannot close: No contract generated for booking")

    if booking.status == BookingStatus.COMPLETED and contract.status in [ContractStatus.SIGNED, ContractStatus.VOIDED]:
        return {
            "status": "ALREADY_CLOSED",
            "booking_id": booking.id,
            "contract_id": contract.id,
            "closure_reason": closure_reason,
            "message": "Contract and booking are already closed.",
        }

    # 1. Gate Check: Signatures
    sig_res = await db.execute(
        select(ContractSignature).where(ContractSignature.contract_id == contract.id)
    )
    all_sigs = list(sig_res.scalars().all())
    signed_roles = {
        s.role_in_contract.value if hasattr(s.role_in_contract, "value") else str(s.role_in_contract)
        for s in all_sigs
    }
    if "USER" not in signed_roles or "OWNER" not in signed_roles:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Contract closure gate failed: Agreement is missing required counter-signatures",
        )

    # 2. Gate Check: Return submitted
    out_rep = (
        await db.execute(
            select(ConditionReport)
            .options(selectinload(ConditionReport.images))
            .where(
                ConditionReport.booking_id == booking_id,
                ConditionReport.report_type == ReportType.CHECK_OUT,
            )
        )
    ).scalars().first()

    if not out_rep or len(out_rep.images) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Contract closure gate failed: 6-angle return inspection photos are incomplete or missing",
        )

    # 3. Gate Check: Open Claims or Unresolved Incidents
    inc_res = await db.execute(
        select(IncidentReport)
        .options(selectinload(IncidentReport.claims))
        .where(IncidentReport.booking_id == booking_id)
    )
    incident = inc_res.scalars().first()

    if incident:
        # Check active claims
        for claim in incident.claims:
            if claim.status in [ClaimStatus.SUBMITTED, ClaimStatus.RESEARCHER_REVIEW, ClaimStatus.DISPUTED]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Contract closure gate failed: Active damage claim #{str(claim.id)[:8]} is currently {claim.status.value}",
                )
            # If claim was accepted for repair, verify repair completion
            if claim.requested_resolution.value == "REPAIR" and not claim.repair_verified_at:
                if claim.status != ClaimStatus.WITHDRAWN:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Contract closure gate failed: Agreed repair has not been verified by owner/admin",
                    )
            # If compensation agreed, verify payment/settlement
            if claim.requested_resolution.value == "COMPENSATION" and claim.status == ClaimStatus.ACCEPTED and not claim.settled_at:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Contract closure gate failed: Agreed damage compensation payment has not been settled",
                )

        if incident.status == IncidentStatus.OPEN:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Contract closure gate failed: Incident report remains OPEN and requires determination",
            )

    # 4. Process Deposit Release (Demo/Simulated Escrow Release with Audit Trace)
    deposit_released = False
    if booking.deposit_amount > 0:
        deposit_released = True
        await notify_escrow_released(
            user_id=booking.user_id,
            amount=float(booking.deposit_amount),
            booking_id=booking.id,
            db=db,
        )

    # 5. Commit Terminal Closure States
    prev_status = booking.status.value
    booking.status = BookingStatus.COMPLETED
    # Note: Contract lifecycle reaches terminal state
    contract.status = ContractStatus.SIGNED  # fully executed and completed
    now = datetime.now(timezone.utc)

    if incident and incident.status == IncidentStatus.UNDER_REVIEW:
        incident.status = IncidentStatus.RESOLVED_USER
        incident.resolved_at = now
        incident.resolution_note = closure_reason

    await db.commit()

    # 6. Audit Log
    await log_transition(
        action="CONTRACT_CLOSURE_GATE_PASSED",
        booking_id=booking.id,
        user_id=actor_id,
        previous_status=prev_status,
        new_status=BookingStatus.COMPLETED.value,
        db=db,
        metadata={
            "closure_reason": closure_reason,
            "deposit_released": deposit_released,
            "deposit_amount": str(booking.deposit_amount),
            "timestamp": now.isoformat(),
        },
    )

    # Notify parties
    await notify(
        user_id=booking.user_id,
        type="CONTRACT_CLOSED",
        title="Rental Contract Successfully Closed",
        body=f"Your booking has satisfied all return and condition obligations. Reason: {closure_reason}",
        booking_id=booking.id,
        db=db,
    )

    return {
        "status": "CLOSED",
        "booking_id": booking.id,
        "contract_id": contract.id,
        "closed_at": now.isoformat(),
        "closure_reason": closure_reason,
        "deposit_released": deposit_released,
    }
