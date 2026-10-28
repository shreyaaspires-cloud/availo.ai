import asyncio
import hashlib
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import AsyncSessionLocal, Base, engine, is_sqlite
from app.models.user import User, VerificationBadge, BadgeType, BadgeStatus
from app.models.resource import Resource, ResourceImage, AvailabilitySlot, ImageAngle
from app.models.booking import Booking, BookingStatus
from app.models.contract import Contract, ContractStatus, ContractSignature, ContractSignerRole
from app.models.incident import IncidentReport, DamageAssessment, IncidentStatus
from app.models.condition_report import ConditionReport, ConditionImage, ReportType
from app.services.auth_service import hash_password
import app.models  # ensure all models registered


async def seed():
    if is_sqlite:
        for table in Base.metadata.tables.values():
            for column in table.columns:
                if column.server_default is not None:
                    arg_str = str(getattr(column.server_default, "arg", ""))
                    if "gen_random_uuid" in arg_str:
                        column.server_default = None
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as db:
        print("🌱 Seeding Availo database...")

        # 1. Users
        users_data = [
            {
                "email": "demo_user@availo.app",
                "password": settings.DEMO_USER_PASSWORD,
                "full_name": "Demo User (Researcher)",
                "roles": ["USER"],
                "trust_score": 100.0,
            },
            {
                "email": "demo_owner@availo.app",
                "password": settings.DEMO_OWNER_PASSWORD,
                "full_name": "Demo Resource Owner",
                "roles": ["USER", "OWNER"],
                "trust_score": 100.0,
            },
            {
                "email": "demo_admin@availo.app",
                "password": settings.DEMO_ADMIN_PASSWORD,
                "full_name": "Availo Administrator",
                "roles": ["USER", "OWNER", "ADMIN"],
                "trust_score": 100.0,
            },
        ]

        users = {}
        for u in users_data:
            existing = await db.execute(select(User).where(User.email == u["email"]))
            user = existing.scalars().first()
            if not user:
                user = User(
                    email=u["email"],
                    hashed_password=hash_password(u["password"]),
                    full_name=u["full_name"],
                    roles=u["roles"],
                    trust_score=u["trust_score"],
                    is_active=True,
                )
                db.add(user)
                await db.commit()
                await db.refresh(user)
                print(f"  ✓ Created user: {u['email']}")
            else:
                print(f"  - User already exists: {u['email']}")
            users[u["email"]] = user

        # 2. Approved Badge for demo_user
        demo_user = users["demo_user@availo.app"]
        badge_res = await db.execute(
            select(VerificationBadge).where(
                VerificationBadge.user_id == demo_user.id,
                VerificationBadge.badge_type == BadgeType.RESEARCHER,
            )
        )
        if not badge_res.scalars().first():
            badge = VerificationBadge(
                user_id=demo_user.id,
                badge_type=BadgeType.RESEARCHER,
                document_url="https://mock-storage.availo.app/verification-docs/researcher_cert.pdf",
                status=BadgeStatus.APPROVED,
                admin_note="Pre-approved academic researcher credential",
                verified_at=datetime.now(timezone.utc),
            )
            db.add(badge)
            await db.commit()
            print("  ✓ Created APPROVED RESEARCHER badge for demo_user")

        # 3. Resources owned by demo_owner
        demo_owner = users["demo_owner@availo.app"]
        resources_data = [
            {
                "title": "Scanning Electron Microscope",
                "description": "High-resolution SEM with energy-dispersive X-ray spectroscopy for advanced nanoscale analysis.",
                "category": "LABORATORY_EQUIPMENT",
                "deposit_amount": Decimal("5000.00"),
                "daily_rate": Decimal("500.00"),
                "requires_badge": ["RESEARCHER"],
                "location": "Building A, Room 204",
            },
            {
                "title": "Industrial 3D Printer",
                "description": "High-precision SLA & SLS dual polymer 3D printer for engineering prototypes and rapid fabrication.",
                "category": "FABRICATION",
                "deposit_amount": Decimal("2000.00"),
                "daily_rate": Decimal("200.00"),
                "requires_badge": [],
                "location": "Makerspace, Floor 1",
            },
            {
                "title": "Canon EOS R5 Camera Kit",
                "description": "Professional 8K full-frame mirrorless camera kit including RF 24-70mm f/2.8L and dual batteries.",
                "category": "MEDIA",
                "deposit_amount": Decimal("3000.00"),
                "daily_rate": Decimal("300.00"),
                "requires_badge": [],
                "location": "Media Lab, Room 12",
            },
        ]

        resources = {}
        for r_spec in resources_data:
            existing = await db.execute(select(Resource).where(Resource.title == r_spec["title"]))
            res = existing.scalars().first()
            if not res:
                res = Resource(
                    owner_id=demo_owner.id,
                    title=r_spec["title"],
                    description=r_spec["description"],
                    category=r_spec["category"],
                    location=r_spec["location"],
                    daily_rate=r_spec["daily_rate"],
                    deposit_amount=r_spec["deposit_amount"],
                    max_booking_days=7,
                    requires_badge=r_spec["requires_badge"],
                    condition="Pristine / Factory calibrated",
                    is_active=True,
                    fair_use_limit_per_week=2,
                )
                db.add(res)
                await db.commit()
                await db.refresh(res)

                # Add sample primary image
                img = ResourceImage(
                    resource_id=res.id,
                    url=f"https://images.unsplash.com/photo-1516035069371-29a1b244cc32?auto=format&fit=crop&w=800&q=80",
                    angle=ImageAngle.FRONT,
                    is_primary=True,
                )
                db.add(img)
                await db.commit()
                print(f"  ✓ Created resource: {r_spec['title']}")
            else:
                print(f"  - Resource already exists: {r_spec['title']}")
            resources[r_spec["title"]] = res

        # 4. Completed Demo Booking for Canon EOS R5
        camera_res = resources["Canon EOS R5 Camera Kit"]
        now = datetime.now(timezone.utc)
        yesterday = now - timedelta(days=2)
        today = now - timedelta(days=0)

        existing_b = await db.execute(
            select(Booking).where(
                Booking.resource_id == camera_res.id,
                Booking.user_id == demo_user.id,
            )
        )
        demo_booking = existing_b.scalars().first()
        if not demo_booking:
            demo_booking = Booking(
                resource_id=camera_res.id,
                user_id=demo_user.id,
                status=BookingStatus.COMPLETED,
                start_dt=yesterday,
                end_dt=today,
                purpose="Field documentation of research samples.",
                total_amount=Decimal("600.00"),
                deposit_amount=Decimal("3000.00"),
                payment_reference="pay_demo_canon_r5",
            )
            db.add(demo_booking)
            await db.commit()
            await db.refresh(demo_booking)

            # Contract
            contract_html = "<h1>Executed Availo Rental Contract</h1><p>Demo signed contract for Canon EOS R5 Kit.</p>"
            sha256 = hashlib.sha256(contract_html.encode("utf-8")).hexdigest()
            contract = Contract(
                booking_id=demo_booking.id,
                content_html=contract_html,
                pdf_url="https://mock-storage.availo.app/contracts/demo_canon_r5.pdf",
                sha256_hash=sha256,
                status=ContractStatus.SIGNED,
            )
            db.add(contract)
            await db.commit()
            await db.refresh(contract)

            # Contract Signatures
            db.add(ContractSignature(
                contract_id=contract.id,
                user_id=demo_user.id,
                role_in_contract=ContractSignerRole.USER,
                signature_image_url="https://mock-storage.availo.app/contracts/demo_user_sig.png",
                ip_address="127.0.0.1",
            ))
            db.add(ContractSignature(
                contract_id=contract.id,
                user_id=demo_owner.id,
                role_in_contract=ContractSignerRole.OWNER,
                signature_image_url="https://mock-storage.availo.app/contracts/demo_owner_sig.png",
                ip_address="127.0.0.1",
            ))

            # Incident & 6-Angle Damage Assessment
            incident = IncidentReport(
                booking_id=demo_booking.id,
                raised_by_id=demo_user.id,
                status=IncidentStatus.RESOLVED_USER,
                resolution_note="Automated AI Inspection passed with 0 anomalies. Escrow released.",
                resolved_at=now,
            )
            db.add(incident)
            await db.commit()
            await db.refresh(incident)

            for angle in [ImageAngle.FRONT, ImageAngle.BACK, ImageAngle.LEFT, ImageAngle.RIGHT, ImageAngle.TOP, ImageAngle.BOTTOM]:
                assessment = DamageAssessment(
                    incident_id=incident.id,
                    angle=angle,
                    before_image_url=f"https://mock-storage.availo.app/condition/{demo_booking.id}/in_{angle.value}.jpg",
                    after_image_url=f"https://mock-storage.availo.app/condition/{demo_booking.id}/out_{angle.value}.jpg",
                    confidence_score=0.05,
                    anomalies=[],
                    closeup_required=False,
                )
                db.add(assessment)

            await db.commit()
            print("  ✓ Created completed demo booking + signed contract + 6-angle damage assessment")

        print("✨ Database seeding complete!")


if __name__ == "__main__":
    asyncio.run(seed())
