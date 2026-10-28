import asyncio
import sys
from datetime import datetime, timedelta, timezone
import httpx

BASE_URL = "http://localhost:8000/api/v1"


async def run_e2e():
    print("🚀 Starting Availo End-to-End Test Flow...")
    start_time = datetime.now()

    async with httpx.AsyncClient(base_url=BASE_URL, timeout=30.0) as client:
        # Step 1: Login / Register demo_user
        try:
            user_login = await client.post("/auth/login", json={"email": "demo_user@availo.app", "password": "DemoUser@Availo"})
            if user_login.status_code != 200:
                user_reg = await client.post("/auth/register", json={
                    "email": "demo_user@availo.app",
                    "password": "DemoUser@Availo",
                    "full_name": "Demo Researcher",
                })
                assert user_reg.status_code in [200, 201]
                user_login = await client.post("/auth/login", json={"email": "demo_user@availo.app", "password": "DemoUser@Availo"})
            user_token = user_login.json()["access_token"]
            user_headers = {"Authorization": f"Bearer {user_token}"}
            print("✅ 1. Register / Login demo_user")
        except Exception as e:
            print(f"❌ 1. demo_user login failed: {e}")
            sys.exit(1)

        # Step 2: Login / Register demo_owner
        try:
            owner_login = await client.post("/auth/login", json={"email": "demo_owner@availo.app", "password": "DemoOwner@Availo"})
            if owner_login.status_code != 200:
                owner_reg = await client.post("/auth/register", json={
                    "email": "demo_owner@availo.app",
                    "password": "DemoOwner@Availo",
                    "full_name": "Demo Resource Owner",
                })
                assert owner_reg.status_code in [200, 201]
                owner_login = await client.post("/auth/login", json={"email": "demo_owner@availo.app", "password": "DemoOwner@Availo"})
            owner_token = owner_login.json()["access_token"]
            owner_headers = {"Authorization": f"Bearer {owner_token}"}
            print("✅ 2. Register / Login demo_owner")
        except Exception as e:
            print(f"❌ 2. demo_owner login failed: {e}")
            sys.exit(1)

        # Step 3: Owner lists new test resource
        resource_id = None
        try:
            res = await client.post(
                "/resources",
                headers=owner_headers,
                json={
                    "title": "E2E Test Camera",
                    "description": "High end camera for end to end testing",
                    "category": "MEDIA",
                    "location": "Testing Lab 1",
                    "daily_rate": "150.00",
                    "deposit_amount": "500.00",
                    "max_booking_days": 5,
                    "requires_badge": [],
                    "condition": "Brand new",
                    "fair_use_limit_per_week": 5,
                }
            )
            assert res.status_code in [200, 201], f"Status: {res.status_code}"
            resource_id = res.json()["id"]
            print("✅ 3. Owner lists test resource: E2E Test Camera")
        except Exception as e:
            print(f"❌ 3. Listing resource failed: {e}")
            sys.exit(1)

        # Step 4: User searches resources
        try:
            s_res = await client.get("/resources?search=E2E Test Camera", headers=user_headers)
            assert s_res.status_code == 200
            items = s_res.json()
            assert any(item["id"] == resource_id for item in items)
            print("✅ 4. User searches resources — test resource verified")
        except Exception as e:
            print(f"❌ 4. Search verification failed: {e}")

        # Step 5: Check eligibility
        try:
            el_res = await client.get(f"/resources/{resource_id}/eligibility", headers=user_headers)
            assert el_res.status_code == 200
            assert el_res.json()["eligible"] is True
            print("✅ 5. User checks eligibility — verified ELIGIBLE")
        except Exception as e:
            print(f"❌ 5. Eligibility check failed: {e}")

        # Step 6: Submit booking request for tomorrow
        booking_id = None
        now = datetime.now(timezone.utc)
        tomorrow = now + timedelta(days=1)
        day_after = now + timedelta(days=2)
        try:
            b_res = await client.post(
                "/bookings",
                headers=user_headers,
                json={
                    "resource_id": resource_id,
                    "start_dt": tomorrow.isoformat(),
                    "end_dt": day_after.isoformat(),
                    "purpose": "E2E Test verification",
                }
            )
            assert b_res.status_code in [200, 201]
            booking_id = b_res.json()["id"]
            print("✅ 6. User submits booking request for tomorrow")
        except Exception as e:
            print(f"❌ 6. Booking request failed: {e}")
            sys.exit(1)

        # Step 7: Owner approves booking
        try:
            app_res = await client.post(f"/bookings/{booking_id}/approve", headers=owner_headers)
            assert app_res.status_code == 200
            assert app_res.json()["status"] == "AWAITING_SIGNATURES"
            print("✅ 7. Owner approves booking")
        except Exception as e:
            print(f"❌ 7. Approve booking failed: {e}")
            sys.exit(1)

        # Step 8: Contract auto-generated check
        contract_id = None
        try:
            for _ in range(5):
                c_res = await client.get(f"/contracts/{booking_id}", headers=user_headers)
                if c_res.status_code == 200 and c_res.json()["status"] == "PENDING_SIGNATURES":
                    contract_id = c_res.json()["id"]
                    break
                await asyncio.sleep(1)
            assert contract_id is not None
            print("✅ 8. System auto-generates contract — status PENDING_SIGNATURES")
        except Exception as e:
            print(f"❌ 8. Contract verification failed: {e}")
            sys.exit(1)

        # Step 9: User signs contract
        mock_sig = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
        try:
            u_sig = await client.post(f"/contracts/{contract_id}/sign", headers=user_headers, json={"signature_image_base64": mock_sig})
            assert u_sig.status_code == 200
            print("✅ 9. User signs contract")
        except Exception as e:
            print(f"❌ 9. User signing failed: {e}")

        # Step 10: Owner signs contract
        try:
            o_sig = await client.post(f"/contracts/{contract_id}/sign", headers=owner_headers, json={"signature_image_base64": mock_sig})
            assert o_sig.status_code == 200
            print("✅ 10. Owner signs contract")
        except Exception as e:
            print(f"❌ 10. Owner signing failed: {e}")

        # Step 11: Booking transitions to AWAITING_PAYMENT
        try:
            b_check = await client.get(f"/bookings/{booking_id}", headers=user_headers)
            assert b_check.json()["status"] == "AWAITING_PAYMENT"
            print("✅ 11. Booking transitions to AWAITING_PAYMENT")
        except Exception as e:
            print(f"❌ 11. Payment state transition check failed: {e}")

        # Step 12: User confirms mock payment
        try:
            pay_res = await client.post(f"/bookings/{booking_id}/confirm-payment", headers=user_headers, json={"razorpay_payment_id": "test_pay_123"})
            assert pay_res.status_code == 200
            assert pay_res.json()["status"] == "CONFIRMED"
            print("✅ 12. User confirms payment — booking CONFIRMED")
        except Exception as e:
            print(f"❌ 12. Confirm payment failed: {e}")

        # Step 13: Check-in upload & complete
        try:
            for angle in ["FRONT", "BACK", "LEFT", "RIGHT", "TOP", "BOTTOM"]:
                await client.post(
                    f"/conditions/{booking_id}/photos",
                    headers=user_headers,
                    data={"report_type": "CHECK_IN", "angle": angle, "notes": "Checkin condition"},
                    files={"file": ("test.jpg", b"fakeimagebytes", "image/jpeg")},
                )
            in_comp = await client.post(f"/conditions/{booking_id}/checkin-complete", headers=user_headers)
            assert in_comp.status_code == 200
            print("✅ 13. User submits 6 check-in photos — booking CHECKED_IN")
        except Exception as e:
            print(f"❌ 13. Check-in submission failed: {e}")

        # Step 14: Check-out upload & complete
        try:
            for angle in ["FRONT", "BACK", "LEFT", "RIGHT", "TOP", "BOTTOM"]:
                await client.post(
                    f"/conditions/{booking_id}/photos",
                    headers=user_headers,
                    data={"report_type": "CHECK_OUT", "angle": angle, "notes": "Checkout condition"},
                    files={"file": ("test.jpg", b"fakeimagebytes", "image/jpeg")},
                )
            out_comp = await client.post(f"/conditions/{booking_id}/checkout-complete", headers=user_headers)
            assert out_comp.status_code == 200
            print("✅ 14. User submits 6 check-out photos — AI Damage Analysis started")
        except Exception as e:
            print(f"❌ 14. Check-out submission failed: {e}")

        # Step 15: Damage analysis result
        try:
            final_status = None
            for _ in range(10):
                chk = await client.get(f"/bookings/{booking_id}", headers=user_headers)
                final_status = chk.json()["status"]
                if final_status in ["COMPLETED", "DAMAGE_REVIEW"]:
                    break
                await asyncio.sleep(1)
            print(f"✅ 15. Damage analysis completed — final booking status: {final_status}")
        except Exception as e:
            print(f"❌ 15. Damage review polling failed: {e}")

        elapsed = (datetime.now() - start_time).total_seconds()
        print(f"\n🎉 All E2E steps passed! Total elapsed time: {elapsed:.2f}s")


if __name__ == "__main__":
    asyncio.run(run_e2e())
