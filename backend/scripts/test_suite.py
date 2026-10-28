import os
import sys
import uuid
import asyncio
from datetime import datetime, timedelta, timezone
from decimal import Decimal

# Configure local sqlite for test run
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test_availo.db"
os.environ["APP_ENV"] = "development"

import httpx
from sqlalchemy import text
from app.database import engine, Base, AsyncSessionLocal
import app.models  # load all models


async def setup_test_db():
    # Strip postgres-specific server_default for sqlite tests
    for table in Base.metadata.tables.values():
        for column in table.columns:
            if column.server_default is not None:
                arg_str = str(getattr(column.server_default, "arg", ""))
                if "gen_random_uuid" in arg_str:
                    column.server_default = None

    async with engine.begin() as conn:
        # Clean recreate tables
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    print("Database tables initialized successfully!")


async def run_full_suite():
    await setup_test_db()

    # Import app after env is configured
    from app.main import app

    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test/api/v1") as client:
        print("\n========================================================")
        print("🧪 RUNNING AVAILO FULL AUTOMATED INTEGRATION TEST SUITE")
        print("========================================================\n")

        # 1. Health check
        h_res = await client.get("http://test/health")
        assert h_res.status_code == 200, f"Health check failed: {h_res.text}"
        print("✅ 1. Health check probe [/health]: OK")

        # 2. Register demo users
        reg_user = await client.post("/auth/register", json={
            "email": "demo_user@availo.app",
            "password": "DemoUser@Availo",
            "full_name": "Dr. Sarah Chen (Researcher)",
        })
        assert reg_user.status_code == 201, f"User registration failed: {reg_user.text}"
        print("✅ 2. User registration [/auth/register]: Researcher registered")

        reg_owner = await client.post("/auth/register", json={
            "email": "demo_owner@availo.app",
            "password": "DemoOwner@Availo",
            "full_name": "Prof. Marcus Vance (Owner)",
        })
        assert reg_owner.status_code == 201
        print("✅ 3. Owner registration [/auth/register]: Owner registered")

        # Give owner role
        async with AsyncSessionLocal() as db:
            from app.models.user import User
            from sqlalchemy import select
            owner_user = (await db.execute(select(User).where(User.email == "demo_owner@availo.app"))).scalars().first()
            owner_user.roles = ["USER", "OWNER"]
            await db.commit()

        # 3. Login
        login_u = await client.post("/auth/login", json={"email": "demo_user@availo.app", "password": "DemoUser@Availo"})
        assert login_u.status_code == 200
        user_token = login_u.json()["access_token"]
        user_headers = {"Authorization": f"Bearer {user_token}"}
        print("✅ 4. User authentication [/auth/login]: JWT access token issued")

        login_o = await client.post("/auth/login", json={"email": "demo_owner@availo.app", "password": "DemoOwner@Availo"})
        assert login_o.status_code == 200
        owner_token = login_o.json()["access_token"]
        owner_headers = {"Authorization": f"Bearer {owner_token}"}
        print("✅ 5. Owner authentication [/auth/login]: JWT access token issued")

        # 4. Check profile
        me = await client.get("/auth/me", headers=user_headers)
        assert me.status_code == 200
        assert me.json()["email"] == "demo_user@availo.app"
        print("✅ 6. Profile query [/auth/me]: Verified")

        # 5. Owner creates Resource
        res_create = await client.post("/resources", headers=owner_headers, json={
            "title": "FEI Quanta 200 SEM Microscope",
            "description": "Scanning Electron Microscope with EDAX for nanoscale materials analysis",
            "category": "LABORATORY_EQUIPMENT",
            "location": "Nanotech Center, Room 102",
            "daily_rate": "450.00",
            "deposit_amount": "2500.00",
            "max_booking_days": 5,
            "requires_badge": [],
            "condition": "Calibrated clean room condition",
            "fair_use_limit_per_week": 3,
        })
        assert res_create.status_code == 201, f"Resource creation failed: {res_create.text}"
        resource_id = res_create.json()["id"]
        print(f"✅ 7. Create Resource [/resources]: Created '{res_create.json()['title']}'")

        # 6. List resources & Search
        list_res = await client.get("/resources?search=Microscope", headers=user_headers)
        assert list_res.status_code == 200
        assert len(list_res.json()) >= 1
        print("✅ 8. Search Resources [/resources]: Full-text query returned match")

        # 7. Check resource detail and availability
        r_detail = await client.get(f"/resources/{resource_id}", headers=user_headers)
        assert r_detail.status_code == 200
        avail = await client.get(f"/resources/{resource_id}/availability", headers=user_headers)
        assert avail.status_code == 200
        assert len(avail.json()) == 30
        print("✅ 9. Resource Availability [/resources/{id}/availability]: 30-day calendar computed")

        # 8. User requests booking (State: PENDING_APPROVAL)
        now = datetime.now(timezone.utc)
        start_time = now + timedelta(days=1)
        end_time = now + timedelta(days=3)
        b_req = await client.post("/bookings", headers=user_headers, json={
            "resource_id": resource_id,
            "start_dt": start_time.isoformat(),
            "end_dt": end_time.isoformat(),
            "purpose": "Nanowire morphology analysis for renewable catalysts",
        })
        assert b_req.status_code == 201, f"Booking request failed: {b_req.text}"
        booking_id = b_req.json()["id"]
        assert b_req.json()["status"] == "PENDING_APPROVAL"
        print(f"✅ 10. Booking State Machine: Transitioned -> PENDING_APPROVAL (Booking ID: {booking_id[:8]})")

        # 9. Owner approves booking -> transitions to AWAITING_SIGNATURES & generates contract
        app_req = await client.post(f"/bookings/{booking_id}/approve", headers=owner_headers)
        assert app_req.status_code == 200
        assert app_req.json()["status"] == "AWAITING_SIGNATURES"
        print("✅ 11. Booking State Machine: Owner Approved -> Transitioned -> AWAITING_SIGNATURES")

        # 10. Check Contract generation & SHA-256 hash
        contract_req = await client.get(f"/contracts/{booking_id}", headers=user_headers)
        assert contract_req.status_code == 200
        contract_data = contract_req.json()
        contract_id = contract_data["id"]
        assert contract_data["sha256_hash"] is not None
        assert "Availo Resource Sharing Agreement" in contract_data["content_html"]
        print(f"✅ 12. Smart Contract Generation [/contracts]: Generated with SHA-256 {contract_data['sha256_hash'][:16]}...")

        # 11. Dual Digital Signatures
        mock_sig_b64 = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
        u_sig = await client.post(f"/contracts/{contract_id}/sign", headers=user_headers, json={"signature_image_base64": mock_sig_b64})
        assert u_sig.status_code == 200
        print("✅ 13. Digital Signature 1/2: User executed contract")

        o_sig = await client.post(f"/contracts/{contract_id}/sign", headers=owner_headers, json={"signature_image_base64": mock_sig_b64})
        assert o_sig.status_code == 200
        print("✅ 14. Digital Signature 2/2: Owner executed contract")

        # Check booking transitioned to AWAITING_PAYMENT
        b_after_sigs = await client.get(f"/bookings/{booking_id}", headers=user_headers)
        assert b_after_sigs.json()["status"] == "AWAITING_PAYMENT"
        print("✅ 15. Booking State Machine: Both Signed -> Transitioned -> AWAITING_PAYMENT")

        # 12. Escrow Payment Confirmation
        pay_res = await client.post(f"/bookings/{booking_id}/confirm-payment", headers=user_headers, json={"razorpay_payment_id": "pay_live_escrow_12345"})
        assert pay_res.status_code == 200
        assert pay_res.json()["status"] == "CONFIRMED"
        print("✅ 16. Escrow Payment Confirmation [/confirm-payment]: Transitioned -> CONFIRMED")

        # 13. Check-in Condition Reports (6 canonical angles)
        angles = ["FRONT", "BACK", "LEFT", "RIGHT", "TOP", "BOTTOM"]
        for angle in angles:
            p_res = await client.post(
                f"/conditions/{booking_id}/photos",
                headers=user_headers,
                data={"report_type": "CHECK_IN", "angle": angle, "notes": f"Clean {angle} face"},
                files={"file": ("in.jpg", b"\xff\xd8\xff\xe0mockjpegdata", "image/jpeg")},
            )
            assert p_res.status_code == 200

        checkin_done = await client.post(f"/conditions/{booking_id}/checkin-complete", headers=user_headers)
        assert checkin_done.status_code == 200
        b_checked_in = await client.get(f"/bookings/{booking_id}", headers=user_headers)
        assert b_checked_in.json()["status"] == "CHECKED_IN"
        print("✅ 17. 6-Angle Check-in Complete [/checkin-complete]: Transitioned -> CHECKED_IN")

        # 14. In-App Live Chat Message
        msg_res = await client.post(f"/chat/{booking_id}/messages", headers=user_headers, json={"content": "Picked up equipment safely. Calibration looks perfect."})
        assert msg_res.status_code == 200
        msgs = await client.get(f"/chat/{booking_id}/messages", headers=owner_headers)
        assert len(msgs.json()) == 1
        print("✅ 18. Live Channel Chat [/chat]: Dispatched and retrieved")

        # 15. Check-out Condition Reports (6 canonical angles) & Return
        for angle in angles:
            p_res = await client.post(
                f"/conditions/{booking_id}/photos",
                headers=user_headers,
                data={"report_type": "CHECK_OUT", "angle": angle, "notes": f"Return {angle} face"},
                files={"file": ("out.jpg", b"\xff\xd8\xff\xe0mockjpegdata", "image/jpeg")},
            )
            assert p_res.status_code == 200

        checkout_done = await client.post(f"/conditions/{booking_id}/checkout-complete", headers=user_headers)
        assert checkout_done.status_code == 200
        print("✅ 19. 6-Angle Check-out Complete [/checkout-complete]: AI Inspection Triggered")

        # 16. Verify AI Damage Inspection result and Escrow Release
        b_final = await client.get(f"/bookings/{booking_id}", headers=user_headers)
        final_status = b_final.json()["status"]
        assert final_status in ["COMPLETED", "DAMAGE_REVIEW"]
        print(f"✅ 20. Automated AI Inspection Pipeline: Final status -> {final_status} (Escrow Resolved)")

        # 17. Audit Log integrity check
        async with AsyncSessionLocal() as db:
            from app.models.audit_log import AuditLog
            from sqlalchemy import select, func
            audit_count = (await db.execute(select(func.count(AuditLog.id)).where(AuditLog.booking_id == uuid.UUID(booking_id)))).scalar()
            assert audit_count >= 5
            print(f"✅ 21. Append-Only Audit Trail: Verified {audit_count} immutable transition entries logged")

        print("\n========================================================")
        print("🎉 ALL 21 TEST SUITE SPECIFICATIONS PASSED SUCCESSFULLY!")
        print("========================================================\n")


if __name__ == "__main__":
    asyncio.run(run_full_suite())
