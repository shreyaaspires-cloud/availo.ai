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
from app.models.incident import IncidentReport, IncidentStatus, DamageClaim, ClaimStatus, ClaimResolutionType
from app.models.user import User
from app.services.contract_closure_service import verify_and_close_contract
from sqlalchemy import select

async def run_closure_lifecycle_tests():
    print("=== TESTING CONTRACT CLOSURE GATE & DAMAGE RESOLUTION WORKFLOW ===")
    
    async with AsyncSessionLocal() as db:
        # Load demo users
        user_res = await db.execute(select(User).where(User.email == "demo_user@availo.app"))
        user = user_res.scalars().first()
        owner_res = await db.execute(select(User).where(User.email == "demo_owner@availo.app"))
        owner = owner_res.scalars().first()
        res_res = await db.execute(select(Resource).limit(1))
        resource = res_res.scalars().first()

        assert user and owner and resource, "Demo data must be present"

        # TEST 1: Gate Blocks when signatures are incomplete
        print("\nTest 1 - Verify Gate Blocks on Incomplete Signatures:")
        booking1 = Booking(
            resource_id=resource.id,
            user_id=user.id,
            status=BookingStatus.CHECKED_IN,
            start_dt=datetime.now(timezone.utc),
            end_dt=datetime.now(timezone.utc) + timedelta(days=2),
            deposit_amount=Decimal("100.00"),
        )
        db.add(booking1)
        await db.commit()
        await db.refresh(booking1)

        contract1 = Contract(
            booking_id=booking1.id,
            content_html="<p>Test</p>",
            status=ContractStatus.PENDING_SIGNATURES,
        )
        db.add(contract1)
        await db.commit()

        try:
            await verify_and_close_contract(booking1.id, user.id, "Testing closure gate", db)
            assert False, "Should have failed signature check"
        except Exception as e:
            print(f"  Passed: Gate blocked as expected: {e.detail}")

        # Add both signatures
        sig_user = ContractSignature(
            contract_id=contract1.id,
            user_id=user.id,
            role_in_contract=ContractSignerRole.USER,
            signature_image_url="http://sig.png",
        )
        sig_owner = ContractSignature(
            contract_id=contract1.id,
            user_id=owner.id,
            role_in_contract=ContractSignerRole.OWNER,
            signature_image_url="http://sig_owner.png",
        )
        db.add_all([sig_user, sig_owner])
        await db.commit()

        # TEST 2: Gate Blocks when return photos are missing/incomplete
        print("\nTest 2 - Verify Gate Blocks on Missing 6-Angle Return Photos:")
        try:
            await verify_and_close_contract(booking1.id, user.id, "Testing closure gate", db)
            assert False, "Should have failed return photos check"
        except Exception as e:
            print(f"  Passed: Gate blocked as expected: {e.detail}")

        # Add all 6 checkout photos
        out_rep = ConditionReport(
            booking_id=booking1.id,
            report_type=ReportType.CHECK_OUT,
        )
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

        # TEST 3: Path A - Successful closure when no damage exists
        print("\nTest 3 - Path A: Clean Closure with Deposit Release:")
        res_closure = await verify_and_close_contract(booking1.id, user.id, "Normal return complete", db)
        print(f"  Passed: Closure result: {res_closure['status']} - Deposit Released: {res_closure['deposit_released']}")
        assert res_closure['status'] == "CLOSED"
        assert res_closure['deposit_released'] is True

        # TEST 4: Path B - Gate Blocks when open damage claim exists
        print("\nTest 4 - Path B: Verify Gate Blocks when Active Damage Claim is Unresolved:")
        booking2 = Booking(
            resource_id=resource.id,
            user_id=user.id,
            status=BookingStatus.DAMAGE_REVIEW,
            start_dt=datetime.now(timezone.utc),
            end_dt=datetime.now(timezone.utc) + timedelta(days=2),
            deposit_amount=Decimal("150.00"),
        )
        db.add(booking2)
        await db.commit()
        await db.refresh(booking2)

        contract2 = Contract(
            booking_id=booking2.id,
            content_html="<p>Test</p>",
            status=ContractStatus.SIGNED,
        )
        db.add(contract2)
        await db.commit()
        await db.refresh(contract2)

        sig_user2 = ContractSignature(
            contract_id=contract2.id,
            user_id=user.id,
            role_in_contract=ContractSignerRole.USER,
            signature_image_url="http://sig.png",
        )
        sig_owner2 = ContractSignature(
            contract_id=contract2.id,
            user_id=owner.id,
            role_in_contract=ContractSignerRole.OWNER,
            signature_image_url="http://sig_owner.png",
        )
        db.add_all([sig_user2, sig_owner2])

        out_rep2 = ConditionReport(booking_id=booking2.id, report_type=ReportType.CHECK_OUT)
        db.add(out_rep2)
        await db.commit()
        await db.refresh(out_rep2)

        for ang in [ImageAngle.FRONT, ImageAngle.BACK, ImageAngle.LEFT, ImageAngle.RIGHT, ImageAngle.TOP, ImageAngle.BOTTOM]:
            img = ConditionImage(
                report_id=out_rep2.id,
                angle=ang,
                url=f"http://storage/{ang.value}.jpg",
                fingerprint="hash123",
            )
            db.add(img)

        # Create active Incident with open damage claim
        inc2 = IncidentReport(
            booking_id=booking2.id,
            raised_by_id=owner.id,
            status=IncidentStatus.OPEN,
        )
        db.add(inc2)
        await db.commit()
        await db.refresh(inc2)

        claim2 = DamageClaim(
            incident_id=inc2.id,
            claimant_id=owner.id,
            description="Deep gouge on optical lens mount",
            justification="Photo comparison highlights crack",
            estimated_cost=Decimal("75.00"),
            requested_resolution=ClaimResolutionType.COMPENSATION,
            status=ClaimStatus.RESEARCHER_REVIEW,
        )
        db.add(claim2)
        await db.commit()

        try:
            await verify_and_close_contract(booking2.id, user.id, "Attempting early closure", db)
            assert False, "Should have failed due to active claim"
        except Exception as e:
            print(f"  Passed: Gate blocked as expected: {e.detail}")

        # Settle claim (agreed compensation)
        claim2.status = ClaimStatus.ACCEPTED
        claim2.settled_at = datetime.now(timezone.utc)
        inc2.status = IncidentStatus.UNDER_REVIEW
        await db.commit()

        # TEST 5: Closure now succeeds after claim is resolved
        print("\nTest 5 - Path B Resolution: Closure Succeeds After Claim Settlement:")
        res_closure2 = await verify_and_close_contract(booking2.id, user.id, "Settled agreed compensation", db)
        print(f"  Passed: Closure result: {res_closure2['status']}")
        assert res_closure2['status'] == "CLOSED"

    print("\n=== ALL LIFECYCLE & CONTRACT CLOSURE TESTS PASSED! ===")

if __name__ == '__main__':
    asyncio.run(run_closure_lifecycle_tests())
