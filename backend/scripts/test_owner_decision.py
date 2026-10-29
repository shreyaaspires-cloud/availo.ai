import asyncio
import os
import sys
import uuid
from decimal import Decimal
from datetime import datetime, timezone, timedelta

sys.path.insert(0, os.path.join(os.getcwd(), 'backend'))

from app.database import AsyncSessionLocal
from app.models.booking import Booking, BookingStatus
from app.models.contract import Contract, ContractStatus, ContractSignature, ContractSignerRole
from app.models.condition_report import ConditionReport, ConditionImage, ReportType
from app.models.resource import Resource, ImageAngle
from app.models.incident import IncidentReport, IncidentStatus, DamageClaim, ClaimStatus, ClaimResolutionType, OwnerDecisionType
from app.models.user import User
from app.schemas.incident import OwnerDecisionRequest
from app.routers.incidents import submit_owner_return_decision
from sqlalchemy import select

async def run_owner_decision_tests():
    print("=== TESTING OWNER-CONTROLLED DAMAGE DECISION WORKFLOW ===")
    
    async with AsyncSessionLocal() as db:
        user_res = await db.execute(select(User).where(User.email == "demo_user@availo.app"))
        user = user_res.scalars().first()
        owner_res = await db.execute(select(User).where(User.email == "demo_owner@availo.app"))
        owner = owner_res.scalars().first()
        res_res = await db.execute(select(Resource).limit(1))
        resource = res_res.scalars().first()

        # Update resource owner to match demo_owner
        resource.owner_id = owner.id
        await db.commit()

        # Create Booking in RETURN_SUBMITTED with contract and checkout photos
        booking = Booking(
            resource_id=resource.id,
            user_id=user.id,
            status=BookingStatus.DAMAGE_REVIEW,
            start_dt=datetime.now(timezone.utc),
            end_dt=datetime.now(timezone.utc) + timedelta(days=2),
            deposit_amount=Decimal("200.00"),
        )
        db.add(booking)
        await db.commit()
        await db.refresh(booking)

        contract = Contract(
            booking_id=booking.id,
            content_html="<p>Official Contract</p>",
            status=ContractStatus.SIGNED,
        )
        db.add(contract)
        await db.commit()
        await db.refresh(contract)

        sig_user = ContractSignature(
            contract_id=contract.id,
            user_id=user.id,
            role_in_contract=ContractSignerRole.USER,
            signature_image_url="http://sig.png",
        )
        sig_owner = ContractSignature(
            contract_id=contract.id,
            user_id=owner.id,
            role_in_contract=ContractSignerRole.OWNER,
            signature_image_url="http://sig_owner.png",
        )
        db.add_all([sig_user, sig_owner])

        out_rep = ConditionReport(booking_id=booking.id, report_type=ReportType.CHECK_OUT)
        db.add(out_rep)
        await db.commit()
        await db.refresh(out_rep)

        for ang in [ImageAngle.FRONT, ImageAngle.BACK, ImageAngle.LEFT, ImageAngle.RIGHT, ImageAngle.TOP, ImageAngle.BOTTOM]:
            img = ConditionImage(
                report_id=out_rep.id,
                angle=ang,
                url=f"http://storage/{ang.value}.jpg",
                fingerprint="hash123",
            )
            db.add(img)
        await db.commit()

        # TEST 1: Unauthorized user (researcher) attempting owner decision must fail
        print("\nTest 1 - Verify Non-Owner is Blocked from Owner Decision:")
        try:
            req = OwnerDecisionRequest(decision=OwnerDecisionType.NO_DAMAGE_REPORTED)
            await submit_owner_return_decision(booking.id, req, current_user=user, db=db)
            assert False, "Non-owner should have been blocked"
        except Exception as e:
            print(f"  Passed: Blocked with HTTP 403: {e.detail}")

        # TEST 2: Owner chooses NO_DAMAGE_REPORTED despite high AI anomaly/flags
        print("\nTest 2 - Owner Confirms 'No Damage' (Overriding AI uncertainty if satisfied):")
        req_clean = OwnerDecisionRequest(
            decision=OwnerDecisionType.NO_DAMAGE_REPORTED,
            notes="Owner personally inspected the tool in person and verified it is fully intact.",
        )
        incident_res = await submit_owner_return_decision(booking.id, req_clean, current_user=owner, db=db)
        print(f"  Passed: Owner decision recorded: {incident_res.owner_decision.value}")
        print(f"          Decision timestamp: {incident_res.owner_decision_at}")

        # Verify booking is now COMPLETED
        await db.refresh(booking)
        print(f"          Booking status transitioned to: {booking.status.value}")
        assert booking.status == BookingStatus.COMPLETED
        assert incident_res.owner_decision == OwnerDecisionType.NO_DAMAGE_REPORTED

        # TEST 3: Report Damage creates persistent claim and sets owner decision
        print("\nTest 3 - Owner Chooses 'Report Damage':")
        booking_dmg = Booking(
            resource_id=resource.id,
            user_id=user.id,
            status=BookingStatus.DAMAGE_REVIEW,
            start_dt=datetime.now(timezone.utc),
            end_dt=datetime.now(timezone.utc) + timedelta(days=2),
            deposit_amount=Decimal("300.00"),
        )
        db.add(booking_dmg)
        await db.commit()
        await db.refresh(booking_dmg)

        req_dmg = OwnerDecisionRequest(
            decision=OwnerDecisionType.DAMAGE_REPORTED,
            notes="Minor crack observed on optical objective housing.",
        )
        inc_dmg = await submit_owner_return_decision(booking_dmg.id, req_dmg, current_user=owner, db=db)
        print(f"  Passed: Damage reported decision recorded: {inc_dmg.owner_decision.value}")
        await db.refresh(booking_dmg)
        assert booking_dmg.status == BookingStatus.DAMAGE_REVIEW

    print("\n=== ALL OWNER-CONTROLLED DECISION TESTS PASSED! ===")

if __name__ == '__main__':
    asyncio.run(run_owner_decision_tests())

