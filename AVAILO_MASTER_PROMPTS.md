# Availo — Master Prompts (Antigravity Edition)
## For use with AI coding assistants (Claude, Cursor, Copilot, etc.)
> Generated from PRD v1.0 · TRD v1.0 · Tech Stack v1.0 · Backend Architecture v1.0

---

## HOW TO USE THESE PROMPTS

Each prompt below is self-contained. Paste it verbatim into your AI assistant at the start of the relevant task. The **SYSTEM CONTEXT** block at the top of each prompt locks the assistant to the exact stack. Do **not** remove it.

---

---

# ── SECTION 1 · PROJECT-WIDE SYSTEM PROMPT ──────────────────────────────────

> Paste this at the start of **every new chat session** to ground the assistant in the full Availo context before you give any task-specific prompt.

```
You are a senior full-stack engineer on Availo — a trusted resource-sharing platform for institutions and communities. Here is the complete project context you must never deviate from:

## Stack (locked — do not suggest alternatives)
- Backend: FastAPI 0.115.x · Python 3.12.x · Pydantic v2 · SQLAlchemy 2.x async · Alembic · asyncpg
- Database: PostgreSQL 15 via Supabase · Row-level security on · JSONB for condition reports
- Cache: Upstash Redis SDK 1.x (10,000 cmd/day free limit — be frugal with writes)
- Storage: Supabase Storage (3 buckets: condition-photos · verification-docs · contracts)
- Auth: JWT (python-jose 3.x) + passlib/bcrypt · access token 60 min · refresh token 30 days
- AI: Google Gemini 2.0 Flash (google-generativeai 0.8.x) — free tier: 15 RPM, 1M TPM
- PDF: WeasyPrint 62.x (pure Python — no headless Chrome)
- Email: Resend SDK 0.7.x (100 emails/day free)
- Frontend: Next.js 15.x · TypeScript 5.5 · TanStack Query 5.x · Zustand 4.x · Tailwind 3.4
- Real-time: WebSocket via FastAPI native — NOT polling
- Hosting: Railway (backend) · Vercel (frontend)

## Architecture Rules
- Routers are THIN — they validate input and call a service function. Zero business logic in routers.
- All business logic lives in app/services/. One service file per domain.
- All DB models in app/models/. All Pydantic schemas in app/schemas/.
- Async everywhere: async def for all route handlers and service methods. Use await for all DB calls.
- SQLAlchemy sessions injected via Depends(get_db) — never create sessions manually inside services.
- Never import a router inside another router. Never import a service inside a model.
- Audit logs are append-only. Never add UPDATE or DELETE on the audit_logs table.
- All secrets via environment variables only — pydantic-settings reads from .env via Settings class.

## Next.js 15 Breaking Change (CRITICAL)
- params, searchParams, cookies(), headers() are ALL async in Next.js 15.
- Always: const { id } = await params — never: params.id directly.

## Roles
USER · OWNER · ADMIN. A user can hold multiple roles (stored as string[] in JWT claims).

## Booking State Machine (strict — no shortcuts)
DRAFT → PENDING_APPROVAL → APPROVED | REJECTED | WAITLISTED
APPROVED → AWAITING_SIGNATURES → AWAITING_PAYMENT → CONFIRMED
CONFIRMED → CHECKED_IN → RETURN_SUBMITTED → DAMAGE_REVIEW | COMPLETED
DAMAGE_REVIEW → DISPUTE_OPEN → RESOLVED_OWNER | RESOLVED_USER | RESOLVED_SPLIT
Any state before CHECKED_IN can transition to CANCELLED.

## Free Tier Constraints (never exceed these in generated code)
- Gemini: batch all photo pairs in ONE API call. Never loop individual calls.
- Redis: cache reads aggressively; avoid write-on-every-request patterns.
- Resend: email is supplementary — WebSocket notification always fires first.
- Supabase Storage: signed URLs generated on-demand; never store signed URLs in DB.

When I give you a task, implement it following every rule above. If any rule conflicts with a suggestion you want to make, the rule wins. Ask me before breaking any rule.
```

---

---

# ── SECTION 2 · BACKEND PROMPTS ─────────────────────────────────────────────

---

## PROMPT B-01 · Project Scaffold

```
Using the Availo system context above, scaffold the complete FastAPI backend directory structure exactly as specified:

backend/
├── app/
│   ├── main.py
│   ├── config.py          ← Pydantic Settings reading from .env
│   ├── database.py        ← Async SQLAlchemy engine + session factory
│   ├── models/            ← one file per: user, resource, booking, condition_report, contract, incident, chat, notification, audit_log
│   ├── schemas/           ← one file per domain matching models
│   ├── routers/           ← thin handlers: auth, users, resources, bookings, conditions, contracts, incidents, chat, notifications, admin, websocket
│   ├── services/          ← business logic: auth_service, user_service, resource_service, booking_service, condition_service, damage_service, contract_service, incident_service, chat_service, notification_service, fairuse_service, audit_service, gemini_service
│   ├── storage/           ← supabase_storage.py
│   ├── middleware/        ← auth.py (JWT extraction), rate_limiter.py (slowapi)
│   └── dependencies/      ← auth.py (get_current_user, require_owner, require_admin), db.py (get_db)

Rules:
- Every __init__.py must exist and re-export the primary class/function from that module.
- main.py must: create FastAPI app, register all routers with /api/v1 prefix, configure CORS (restrict to FRONTEND_URL env var), add slowapi middleware, include WebSocket router.
- config.py must use pydantic-settings BaseSettings with all env vars from the .env spec (JWT, DB, Supabase, Upstash, Gemini, Resend, fair-use limits).
- database.py must: create async engine via asyncpg, define AsyncSessionLocal, provide get_db dependency that yields and closes.
- Output each file fully — no placeholders, no "# TODO" left in core wiring files.
```

---

## PROMPT B-02 · Database Models

```
Using the Availo system context, write ALL SQLAlchemy 2.x async ORM models for the following files. Use mapped_column() and Mapped[] typing throughout. Every model must have created_at and updated_at with server_default=func.now() and onupdate=func.now().

### app/models/user.py
Tables: users, verification_badges
- users: id (UUID PK), email (unique, indexed), hashed_password, full_name, roles (ARRAY of String), trust_score (Float default 100.0), is_active, created_at, updated_at
- verification_badges: id, user_id (FK → users), badge_type (Enum: STUDENT, RESEARCHER, PROFESSIONAL, FACULTY), document_url, status (Enum: PENDING, APPROVED, REJECTED), admin_note, verified_at, created_at

### app/models/resource.py
Tables: resources, resource_images, availability_slots
- resources: id, owner_id (FK → users), title, description, category, location, daily_rate (Decimal), deposit_amount (Decimal), max_booking_days, requires_badge (ARRAY), condition (Text), is_active, fair_use_limit_per_week (Int), created_at, updated_at
- resource_images: id, resource_id (FK), url, angle (Enum: FRONT, BACK, LEFT, RIGHT, TOP, BOTTOM), is_primary, created_at
- availability_slots: id, resource_id (FK), start_dt, end_dt, is_blocked, created_at

### app/models/booking.py
Tables: bookings, waitlist_entries
- bookings: id, resource_id (FK), user_id (FK), status (Enum — all 14 states from state machine), start_dt, end_dt, purpose (Text), total_amount (Decimal), deposit_amount (Decimal), cancellation_reason, rejection_reason, created_at, updated_at
- waitlist_entries: id, resource_id (FK), user_id (FK), requested_start, requested_end, position (Int), notified_at, created_at

### app/models/condition_report.py
Tables: condition_reports, condition_images
- condition_reports: id, booking_id (FK unique per direction: check_in vs check_out), report_type (Enum: CHECK_IN, CHECK_OUT), submitted_at, notes
- condition_images: id, report_id (FK), url, angle (Enum: FRONT/BACK/LEFT/RIGHT/TOP/BOTTOM), exif_timestamp, exif_gps_lat, exif_gps_lon, fingerprint (String — for tamper detection), created_at

### app/models/contract.py
Tables: contracts, contract_signatures
- contracts: id, booking_id (FK unique), content_html (Text), pdf_url, sha256_hash (String), status (Enum: DRAFT, PENDING_SIGNATURES, SIGNED, VOIDED), generated_at, created_at
- contract_signatures: id, contract_id (FK), user_id (FK), role_in_contract (Enum: USER, OWNER), signature_image_url, signed_at, ip_address, user_agent

### app/models/incident.py
Tables: incident_reports, damage_assessments
- incident_reports: id, booking_id (FK), raised_by_id (FK → users), status (Enum: OPEN, UNDER_REVIEW, RESOLVED_OWNER, RESOLVED_USER, RESOLVED_SPLIT), resolution_note, resolved_at, created_at
- damage_assessments: id, incident_id (FK), angle (Enum), before_image_url, after_image_url, confidence_score (Float), anomalies (JSONB), closeup_required (Bool), closeup_image_url, created_at

### app/models/chat.py
Tables: chat_rooms, chat_messages
- chat_rooms: id, booking_id (FK unique), created_at
- chat_messages: id, room_id (FK), sender_id (FK → users), content (Text), attachment_url, read_at, created_at

### app/models/notification.py
Table: notifications
- id, user_id (FK), type (String), title, body, is_read, related_booking_id (FK nullable), created_at

### app/models/audit_log.py
Table: audit_logs — APPEND-ONLY
- id (BigInt autoincrement), booking_id (FK nullable), user_id (FK nullable), action (String), previous_status, new_status, metadata (JSONB), created_at
- Include a comment: # Postgres trigger prevents UPDATE/DELETE — enforced at DB level via Alembic migration

Output all files completely. Use proper SQLAlchemy relationship() back-references. Use __tablename__ strings that are snake_case plural.
```

---

## PROMPT B-03 · Auth Service + Router

```
Using the Availo system context, implement full JWT authentication.

### app/services/auth_service.py
Implement:
- hash_password(plain: str) → str  using passlib bcrypt
- verify_password(plain: str, hashed: str) → bool
- create_access_token(data: dict) → str  — 60-minute expiry, HS256, payload includes sub (user_id str), roles (list), exp
- create_refresh_token(data: dict) → str  — 30-day expiry
- decode_token(token: str) → dict  — raises HTTPException 401 on invalid/expired

### app/dependencies/auth.py
Implement:
- get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)) → User
  — decodes token, loads user from DB, raises 401 if not found or inactive
- require_owner(current_user: User = Depends(get_current_user)) → User
  — raises 403 if "OWNER" not in current_user.roles
- require_admin(current_user: User = Depends(get_current_user)) → User
  — raises 403 if "ADMIN" not in current_user.roles

### app/routers/auth.py
Endpoints (thin — call auth_service and user_service only):
- POST /auth/register — creates user (hashes password, assigns USER role, trust_score=100)
- POST /auth/login — verifies credentials, returns {access_token, refresh_token, token_type}
- POST /auth/refresh — validates refresh token from httpOnly cookie, returns new access_token
- POST /auth/logout — clears refresh cookie
- GET /auth/me — returns current user profile (requires get_current_user)

### app/schemas/auth.py
RegisterRequest, LoginRequest, TokenResponse, UserResponse schemas using Pydantic v2 model_config.

Rate limit: 5 login attempts per 15 minutes per IP using slowapi. Apply limiter decorator on POST /auth/login.

Output all four files completely.
```

---

## PROMPT B-04 · Resource Service + Router

```
Using the Availo system context, implement the resource listing and discovery system.

### app/services/resource_service.py
Implement these async functions:
- create_resource(owner_id, data: ResourceCreate, db) → Resource
- get_resource(resource_id, db) → Resource | None
- list_resources(filters: ResourceFilter, db) → list[Resource]
  Filter params: category, location, date_start, date_end (availability check), badge_required, max_daily_rate
  Use PostgreSQL tsvector full-text search on title+description+location. Cache result 60 seconds in Redis.
- update_resource(resource_id, owner_id, data: ResourceUpdate, db) → Resource
  Raise 403 if owner_id doesn't match resource.owner_id
- delete_resource(resource_id, owner_id, db)  — soft delete (is_active=False)
- check_availability(resource_id, start_dt, end_dt, db) → bool
  Query bookings table: any CONFIRMED/CHECKED_IN booking overlapping the window = unavailable
- check_eligibility(resource_id, user: User, db) → EligibilityResult
  Return {eligible: bool, missing_badges: list[str], reason: str}
  Logic: if resource.requires_badge contains "RESEARCHER" and user has no APPROVED badge of type RESEARCHER → not eligible

### app/routers/resources.py
- GET /resources — list with filters (calls list_resources, caches)
- POST /resources — create (requires OWNER role)
- GET /resources/{id} — detail + eligibility for current user
- PATCH /resources/{id} — update (owner only)
- DELETE /resources/{id} — soft delete (owner only)
- GET /resources/{id}/availability — returns available slots for next 30 days
- POST /resources/{id}/images — upload image to Supabase Storage (condition-photos bucket), create ResourceImage record

### app/schemas/resource.py
ResourceCreate, ResourceUpdate, ResourceResponse, ResourceFilter, EligibilityResult — full Pydantic v2 models.

Output all three files completely.
```

---

## PROMPT B-05 · Booking Service + State Machine

```
Using the Availo system context, implement the complete booking lifecycle — this is the most critical service.

### app/services/booking_service.py
Implement ALL of the following. Each function must write an audit log entry on every state transition via audit_service.log_transition().

- create_booking_request(user_id, resource_id, data: BookingCreate, db) → Booking
  1. Check eligibility (call resource_service.check_eligibility)
  2. Check availability (call resource_service.check_availability)
  3. Check fair-use: user must not exceed MAX_ACTIVE_BOOKINGS_PER_USER concurrent active bookings
  4. Check resource fair_use_limit_per_week for this user
  5. If resource is booked for that window → create WaitlistEntry, raise HTTP 409 with waitlist position
  6. Create Booking with status=PENDING_APPROVAL
  7. Notify owner via notification_service

- approve_booking(booking_id, owner_id, db) → Booking
  Transition: PENDING_APPROVAL → APPROVED
  Then immediately: APPROVED → AWAITING_SIGNATURES
  Auto-trigger contract generation via contract_service.generate_contract() as BackgroundTask

- reject_booking(booking_id, owner_id, reason: str, db) → Booking
  Transition: PENDING_APPROVAL → REJECTED
  Notify user with reason.

- waitlist_booking(booking_id, owner_id, db) → Booking
  Transition: PENDING_APPROVAL → WAITLISTED
  Assign position in waitlist queue (Redis ZADD keyed by resource_id:date_window).

- confirm_payment(booking_id, razorpay_payment_id: str, db) → Booking
  Transition: AWAITING_PAYMENT → CONFIRMED
  Store payment ID. Notify both parties.

- cancel_booking(booking_id, user_id, db) → Booking
  Allowed states: CONFIRMED, AWAITING_SIGNATURES
  Compute refund: if > 24h before start_dt → 100% refund; else → 50% refund.
  Transition to CANCELLED. Trigger waitlist promotion.

- promote_waitlist(resource_id, released_window, db)
  Find first WAITLISTED entry for resource+window. Transition its booking to PENDING_APPROVAL.
  Send notification. TTL: user has 30 minutes to accept.

- get_booking(booking_id, requesting_user: User, db) → Booking
  Raise 403 if user is neither booking.user_id, resource.owner_id, nor ADMIN.

### app/routers/bookings.py
- POST /bookings — create request (verified user only)
- GET /bookings — list own bookings (user sees theirs; owner sees their resource bookings)
- GET /bookings/{id} — detail (access controlled)
- POST /bookings/{id}/approve — owner only
- POST /bookings/{id}/reject — owner only, body: {reason: str}
- POST /bookings/{id}/cancel — booking user only
- POST /bookings/{id}/confirm-payment — user only, body: {razorpay_payment_id: str}

Output booking_service.py and routers/bookings.py completely.
```

---

## PROMPT B-06 · AI Damage Detection Service

```
Using the Availo system context, implement the complete AI damage detection pipeline.

### app/services/damage_service.py

The system captures 6 photos at CHECK_IN and 6 photos at CHECK_OUT — one per angle: FRONT, BACK, LEFT, RIGHT, TOP, BOTTOM.

Implement:

- analyze_damage(booking_id: UUID, checkin_report_id: UUID, checkout_report_id: UUID, db: AsyncSession) → DamageAnalysisResult
  
  Steps:
  1. Load all 6 checkin ConditionImages and all 6 checkout ConditionImages from DB.
  2. Download each image from Supabase Storage (signed URL, fetch bytes).
  3. Build a SINGLE Gemini API call (NEVER loop — one call for all 6 pairs).
     Use model: gemini-2.0-flash.
     Construct prompt requesting JSON response with this exact schema:
     {
       "pairs": [
         {
           "angle": "FRONT",
           "match": true/false,
           "confidence": 0.0-1.0,
           "anomalies": ["description of issue if any"],
           "closeup_required": true/false
         },
         ... (one entry per angle)
       ],
       "overall_damage_detected": true/false,
       "overall_confidence": 0.0-1.0,
       "summary": "plain English summary"
     }
  4. Parse the JSON response. For each pair:
     - Create a DamageAssessment record in DB
     - If closeup_required=true → send notification to user requesting closeup photo for that angle
  5. If overall_damage_detected=true:
     - Transition booking to DAMAGE_REVIEW
     - Notify owner
  6. If no damage detected:
     - Transition booking to COMPLETED
     - Release escrow (call payment_service.release_escrow)
  7. Return DamageAnalysisResult with all pair results.

  Error handling:
  - If Gemini returns non-JSON or times out → log error, set booking to DAMAGE_REVIEW with note "AI_REVIEW_FAILED — manual review required", notify admin.
  - Cache the result in Redis keyed by booking_id:damage_result (TTL 7 days) to avoid re-running on demo.

- request_closeup(booking_id: UUID, angle: str, db) — sends WebSocket notification + Resend email to user.

- submit_closeup(booking_id: UUID, angle: str, image_url: str, db) — stores closeup URL in DamageAssessment. If all closeups received → re-trigger analyze_damage.

### Gemini prompt template to use:
"You are an equipment damage inspector. Compare the BEFORE and AFTER photos of a resource for each angle. For each pair, assess whether there is new damage, scratches, dents, missing parts, or stains that were not present in the BEFORE image. Return ONLY valid JSON, no explanation, no markdown code fences."

Output damage_service.py completely.
```

---

## PROMPT B-07 · Contract Generation Service

```
Using the Availo system context, implement the digital contract generation and e-signature pipeline.

### app/services/contract_service.py
Implement:

- generate_contract(booking_id: UUID, db: AsyncSession) → Contract
  Steps:
  1. Load booking + resource + user + owner from DB.
  2. Call Gemini text API (gemini-2.0-flash) with this system prompt:
     "You are a legal document drafter. Generate a plain-English equipment rental contract in valid HTML. The contract must include: parties (full names, roles), resource description, booking dates, daily rate, total amount, deposit amount, return condition requirements, damage liability clause, escrow release conditions, dispute resolution clause. Use <h2> for sections, <p> for body text, <table> for financial terms. Return ONLY the HTML — no markdown, no preamble."
  3. Inject booking data into the Gemini prompt as structured context.
  4. Receive HTML string from Gemini.
  5. Render HTML → PDF using WeasyPrint: HTML(string=html_content).write_pdf()
  6. Compute SHA-256 hash of the PDF bytes.
  7. Upload PDF to Supabase Storage (contracts bucket) → get URL.
  8. Create Contract record: status=PENDING_SIGNATURES, pdf_url, sha256_hash, content_html.
  9. Send signature request notification to both user and owner via WebSocket + Resend email.
  10. Return Contract.

- collect_signature(contract_id: UUID, user_id: UUID, signature_image_base64: str, ip: str, ua: str, db) → ContractSignature
  Steps:
  1. Decode base64 PNG, upload to Supabase Storage (contracts bucket) as {contract_id}_{user_id}_sig.png.
  2. Create ContractSignature record with signed_at=now(), ip_address, user_agent.
  3. Check if BOTH signatures now exist for this contract.
  4. If yes → update contract.status = SIGNED → transition booking to AWAITING_PAYMENT → notify both parties.
  5. Return signature record.

- verify_contract_integrity(contract_id: UUID, pdf_bytes: bytes, db) → dict
  Recompute SHA-256 of provided bytes, compare to stored hash.
  Return {"status": "VALID" | "TAMPERED", "stored_hash": str, "provided_hash": str}

### app/routers/contracts.py
- GET /contracts/{booking_id} — get contract for a booking (access controlled)
- POST /contracts/{id}/sign — submit canvas signature (base64 PNG in body)
- POST /contracts/{id}/verify — verify PDF integrity (accepts PDF file upload)

Output contract_service.py and routers/contracts.py completely.
```

---

## PROMPT B-08 · WebSocket + Notification System

```
Using the Availo system context, implement the real-time notification infrastructure.

### app/routers/websocket.py
Implement a WebSocket connection manager:

class ConnectionManager:
    - __init__: self.active_connections: dict[str, WebSocket] = {}  # keyed by user_id
    - async connect(user_id: str, ws: WebSocket)
    - disconnect(user_id: str)
    - async send_to_user(user_id: str, message: dict)  — sends JSON; silently no-ops if user offline
    - async broadcast_to_booking(booking_id: UUID, message: dict, db)  — sends to both booking.user_id and resource.owner_id

WebSocket endpoint: WS /ws/{user_id}?token={jwt}
- Validate JWT token from query param before upgrading connection.
- Register connection in ConnectionManager.
- Keep alive with ping/pong every 30 seconds.
- On disconnect: clean up from manager.

### app/services/notification_service.py
Implement:

- async notify(user_id: UUID, type: str, title: str, body: str, booking_id: UUID | None, db)
  1. Create Notification record in DB (is_read=False).
  2. Push via WebSocket: connection_manager.send_to_user(str(user_id), {type, title, body, booking_id, created_at})
  3. Send email via Resend IF type is in [BOOKING_APPROVED, DAMAGE_DETECTED, OVERDUE_RETURN, CONTRACT_READY]:
     resend.Emails.send({from: RESEND_FROM_EMAIL, to: user.email, subject: title, html: body})
  4. Deduplicate: check Redis key notify:{user_id}:{type}:{booking_id} — if exists (TTL 60s) skip email. Set key after send.

- Common notification helpers (call notify internally):
  - notify_booking_request(owner_id, booking) 
  - notify_booking_approved(user_id, booking)
  - notify_booking_rejected(user_id, booking, reason)
  - notify_contract_ready(user_id, owner_id, contract)
  - notify_damage_detected(owner_id, booking, confidence)
  - notify_closeup_required(user_id, booking, angles: list[str])
  - notify_escrow_released(user_id, amount)
  - notify_dispute_opened(admin_id, booking)

Output websocket.py and notification_service.py completely. Export connection_manager as a module-level singleton from websocket.py.
```

---

## PROMPT B-09 · Admin Router + Badge Verification

```
Using the Availo system context, implement all admin-only functionality.

### app/routers/admin.py
All routes require require_admin dependency.

- GET /admin/dashboard — returns:
  {
    pending_verifications: count,
    open_disputes: count,
    overdue_returns: count (bookings in CHECKED_IN past end_dt),
    active_bookings: count,
    platform_utilisation_pct: float  (CONFIRMED+CHECKED_IN bookings / total available slots)
  }

- GET /admin/verifications — list all PENDING VerificationBadge records with user info
- POST /admin/verifications/{id}/approve — approve badge, set status=APPROVED, notify user
- POST /admin/verifications/{id}/reject — reject badge, body: {reason: str}, notify user

- GET /admin/disputes — list all DISPUTE_OPEN bookings
- POST /admin/disputes/{booking_id}/resolve — body: {outcome: "OWNER"|"USER"|"SPLIT", note: str}
  Transition booking through DISPUTE_OPEN → RESOLVED_* 
  If OWNER: release escrow to owner. If USER: refund deposit to user. If SPLIT: split 50/50.

- GET /admin/overdue — bookings in CHECKED_IN where end_dt < now()
- POST /admin/overdue/{booking_id}/escalate — transition to DISPUTE_OPEN, notify admin+user+owner

### app/services/gemini_service.py  (badge pre-screen addition)
Add function:
- async prescreeen_verification_document(image_url: str, claimed_badge_type: str) → BadgePreScreenResult
  Call Gemini Vision with the document image.
  Prompt: "You are a credential verifier. Examine this document image. Determine if it is a valid {claimed_badge_type} credential. Return ONLY JSON: {verified: bool, detected_type: str, institution: str, confidence: float, notes: str}"
  Store result as metadata on VerificationBadge. Admin sees this pre-screen result alongside their approval decision.

### app/routers/users.py (badge application)
- POST /users/me/badges/apply — user uploads document + states badge_type
  1. Upload doc to Supabase Storage (verification-docs bucket), store URL.
  2. Create VerificationBadge record with status=PENDING.
  3. Trigger prescreeen_verification_document() as BackgroundTask.
  4. Return {message: "Application submitted. Admin review within 24 hours."}

Output admin.py, the gemini_service addition, and the badge apply endpoint completely.
```

---

## PROMPT B-10 · Alembic Migrations + Seed Script

```
Using the Availo system context, generate:

### alembic/versions/001_initial_schema.py
Create an Alembic migration that creates ALL tables defined in the models (users, verification_badges, resources, resource_images, availability_slots, bookings, waitlist_entries, condition_reports, condition_images, contracts, contract_signatures, incident_reports, damage_assessments, chat_rooms, chat_messages, notifications, audit_logs).

Key constraints:
- All UUID primary keys use server_default=text("gen_random_uuid()") — requires pgcrypto extension.
- Create a Postgres TRIGGER on audit_logs that raises EXCEPTION on any UPDATE or DELETE attempt.
- Create tsvector index on resources (title || description || location) for full-text search.
- Include op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto") at migration start.

### scripts/seed.py
Seed the following demo data (idempotent — check before inserting):

Users (use bcrypt-hashed passwords from settings.DEMO_*_PASSWORD):
1. demo_user@availo.app — roles: [USER], trust_score: 100, has APPROVED RESEARCHER badge
2. demo_owner@availo.app — roles: [USER, OWNER]
3. demo_admin@availo.app — roles: [USER, OWNER, ADMIN]

Resources (owned by demo_owner):
1. "Scanning Electron Microscope" — category: LABORATORY_EQUIPMENT, deposit: ₹5000, daily_rate: ₹500, requires_badge: [RESEARCHER], location: "Building A, Room 204"
2. "Industrial 3D Printer" — category: FABRICATION, deposit: ₹2000, daily_rate: ₹200, requires_badge: [], location: "Makerspace, Floor 1"
3. "Canon EOS R5 Camera Kit" — category: MEDIA, deposit: ₹3000, daily_rate: ₹300, requires_badge: [], location: "Media Lab, Room 12"

One completed demo booking:
- demo_user books "Canon EOS R5 Camera Kit" for 2 days (yesterday → today)
- Status: COMPLETED (so damage analysis result is already cached)
- Pre-seed a DamageAssessment for all 6 angles: confidence: 0.05, match: true, anomalies: []
- Pre-seed a Contract with status: SIGNED and a sha256_hash

Output migration file and seed.py completely.
```

---

---

# ── SECTION 3 · FRONTEND PROMPTS ────────────────────────────────────────────

---

## PROMPT F-01 · Frontend Project Setup

```
Using the Availo system context, set up the complete Next.js 15 frontend.

### Directory Structure to scaffold:
frontend/src/
├── app/                        ← Next.js App Router
│   ├── layout.tsx              ← root layout: QueryProvider + ZustandProvider + Toaster
│   ├── page.tsx                ← landing/redirect
│   ├── (auth)/
│   │   ├── login/page.tsx
│   │   └── register/page.tsx
│   ├── dashboard/page.tsx      ← role-aware: USER / OWNER / ADMIN views
│   ├── resources/
│   │   ├── page.tsx            ← discovery/search
│   │   └── [id]/page.tsx       ← detail + eligibility + booking CTA
│   ├── bookings/
│   │   ├── page.tsx            ← my bookings list
│   │   └── [id]/page.tsx       ← booking detail + state-machine timeline
│   └── admin/
│       ├── page.tsx            ← admin dashboard
│       ├── verifications/page.tsx
│       └── disputes/page.tsx
├── components/
│   ├── ui/                     ← reusable: Button, Badge, Modal, Spinner, Toast, Card
│   ├── booking/                ← BookingCard, BookingTimeline, StateBadge
│   ├── resource/               ← ResourceCard, ResourceGrid, EligibilityGate
│   ├── condition/              ← SixAnglePhotoUpload, PhotoComparison
│   ├── contract/               ← ContractViewer, SignatureCanvas
│   ├── chat/                   ← ChatWindow, MessageBubble
│   ├── damage/                 ← DamageReport, ConfidenceBar
│   └── admin/                  ← VerificationCard, DisputePanel
├── lib/
│   ├── api.ts                  ← axios/fetch client with JWT auto-attach + refresh logic
│   ├── ws.ts                   ← WebSocket client singleton with reconnect
│   └── utils.ts                ← cn(), formatCurrency(), formatDate()
├── hooks/
│   ├── useAuth.ts              ← reads Zustand auth store
│   ├── useBooking.ts           ← TanStack Query hooks for booking CRUD
│   ├── useResource.ts          ← TanStack Query hooks for resource CRUD
│   └── useWebSocket.ts         ← subscribes to WS, dispatches to Zustand
└── store/
    ├── authStore.ts            ← Zustand: {user, token, roles, setUser, clearUser}
    └── notificationStore.ts    ← Zustand: {notifications[], addNotification, markRead}

### lib/api.ts
- Base URL from NEXT_PUBLIC_API_URL env var
- Attach Authorization: Bearer {token} from authStore on every request
- On 401 → call /auth/refresh → retry original request once → on second 401 → clearUser() + redirect /login
- Export typed functions: get<T>, post<T>, patch<T>, del<T>

### lib/ws.ts
- Connect to NEXT_PUBLIC_WS_URL/ws/{user_id}?token={jwt}
- Auto-reconnect with exponential backoff (max 30s)
- On message: parse JSON, call notificationStore.addNotification(), toast if type matches

Output all scaffold files. For page.tsx files output the full component. For lib/ files output the complete implementation.

CRITICAL: All params, searchParams, cookies in page/layout files must be async (Next.js 15). Example:
export default async function Page({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params
```

---

## PROMPT F-02 · Resource Discovery Page

```
Using the Availo system context, implement the resource discovery experience.

### app/resources/page.tsx
A full-page resource browser with:
- Search bar (full-text, debounced 300ms, calls GET /resources?search=)
- Filter sidebar: category (dropdown), max_daily_rate (range slider), date_start + date_end (date pickers), requires_badge (multi-select checkboxes)
- Results grid using ResourceCard component
- Empty state with illustration when no results
- Loading skeleton grid (6 skeleton cards) during fetch
- Uses TanStack Query: useQuery({ queryKey: ['resources', filters], queryFn: ... })
- Pagination: load more button (not infinite scroll — simpler for demo)

### components/resource/ResourceCard.tsx
Props: resource (ResourceResponse)
Display:
- Primary image (or placeholder icon if none)
- Title, category badge, location (with Lucide MapPin icon)
- Daily rate formatted as ₹{amount}/day
- Deposit badge
- "Verified Researcher Required" tag if requires_badge includes RESEARCHER
- Availability indicator: green dot (available this week) / grey dot (booked)
- CTA: "View & Book" button → navigates to /resources/{id}

### app/resources/[id]/page.tsx
Display:
- Image gallery (thumbnail strip for all 6 resource angles)
- Full resource description, condition notes, fair-use policy
- EligibilityGate component: shows green checkmark per badge requirement met; red X for missing
- Availability calendar (next 30 days, grey out booked dates, use Leaflet for location map)
- "Request Booking" form: start_dt, end_dt date pickers + purpose textarea
- On submit: POST /bookings → optimistic status "Pending Approval" → redirect to /bookings/{id}

Use Tailwind for all styling. Role-based colour: USER=blue, OWNER=green, ADMIN=purple (CSS variables in tailwind config).
```

---

## PROMPT F-03 · Condition Photo Upload + Damage Report UI

```
Using the Availo system context, implement the 6-angle photo capture and damage comparison UI.

### components/condition/SixAnglePhotoUpload.tsx
Props: bookingId, reportType ("CHECK_IN" | "CHECK_OUT"), onComplete: () => void

Layout: 2×3 grid of upload zones, one per angle (FRONT, BACK, LEFT, RIGHT, TOP, BOTTOM)
Each zone:
- Label with Lucide icon (Camera)
- Drag-and-drop or click to upload (react-dropzone)
- Preview thumbnail once uploaded
- Upload progress bar (progress fed via WebSocket message type: PHOTO_UPLOAD_PROGRESS)
- Green checkmark overlay when upload confirmed server-side
- Angle label beneath

Behaviour:
- Upload each photo individually to POST /conditions/{bookingId}/photos as FormData
- Track which angles are complete in local state
- Submit button disabled until all 6 angles are complete
- On submit: POST /conditions/{bookingId}/submit → calls onComplete()

### components/damage/DamageReport.tsx
Props: bookingId

Fetch: GET /incidents/{bookingId}/damage-assessment

Display for each of the 6 angles:
- Side-by-side: BEFORE photo | AFTER photo (labelled)
- Confidence bar: colour-coded (green < 0.3, yellow 0.3–0.6, red > 0.6)
- Anomalies list (bullet points from AI response)
- "Closeup Required" banner if closeup_required=true
  → shows upload zone for that specific angle's closeup

Overall summary:
- "No damage detected — escrow will be released automatically" banner (green)
- OR "Damage detected — owner review required" banner (red) with summary text

### components/damage/ConfidenceBar.tsx
Props: score (0.0–1.0), label: string
Renders a horizontal progress bar.
Color: score < 0.3 → green, 0.3–0.6 → yellow, > 0.6 → red
Shows percentage label on right: e.g. "62% — Review Required"

Output all three components completely.
```

---

## PROMPT F-04 · Contract Viewer + Signature Canvas

```
Using the Availo system context, implement the contract signing experience.

### components/contract/ContractViewer.tsx
Props: bookingId

Fetch: GET /contracts/{bookingId}

Display:
- Contract HTML rendered inside a scrollable iframe or div (use dangerouslySetInnerHTML — content is server-generated, not user input)
- SHA-256 hash shown at bottom: "Document Hash: {hash}" in monospace, copy-to-clipboard button
- Signature status panel:
  - User signature: signed / awaiting (with timestamp if signed)
  - Owner signature: signed / awaiting
- If current user has NOT signed → show SignatureCanvas below
- If both signed → show "Contract Fully Executed" badge + download PDF button

### components/contract/SignatureCanvas.tsx
Props: contractId, onSigned: () => void

Implementation:
- Use react-signature-canvas library
- Canvas size: full width, 150px height, white background, blue pen
- Buttons: "Clear" (resets canvas) | "Submit Signature" (disabled if canvas is empty)
- On submit:
  1. canvas.toDataURL('image/png') → base64 string
  2. POST /contracts/{contractId}/sign with body: { signature_image_base64: string }
  3. Show spinner on button during upload
  4. On success: toast "Signature captured" + call onSigned()
  5. On error: toast "Signature failed — please retry"

Output both components completely.
```

---

## PROMPT F-05 · Booking Detail Page (State Machine Timeline)

```
Using the Availo system context, implement the booking detail page showing the full lifecycle.

### app/bookings/[id]/page.tsx
Fetch: GET /bookings/{id} — poll every 10 seconds via TanStack Query refetchInterval: 10_000

Layout:
- Left column (60%): booking timeline + current action panel
- Right column (40%): chat window

### components/booking/BookingTimeline.tsx
Props: booking (BookingResponse)

Vertical timeline showing all 14 states. Completed states have green dot + timestamp. Current state has pulsing blue dot. Future states have grey dots.

State labels and sub-labels:
- PENDING_APPROVAL: "Awaiting Owner Review"
- AWAITING_SIGNATURES: "Sign Contract" → if pending for current user → show CTA button
- AWAITING_PAYMENT: "Complete Payment" → show Razorpay checkout button
- CONFIRMED: "Booking Confirmed — Check in on {start_dt}"
- CHECKED_IN: "Resource In Use — Return by {end_dt}"
- RETURN_SUBMITTED: "AI Damage Analysis Running..." (show spinner)
- DAMAGE_REVIEW: "Damage Detected — Owner Review" (red banner)
- DISPUTE_OPEN: "Dispute Filed — Admin Reviewing"
- COMPLETED: "Booking Completed ✓" (green banner)
- CANCELLED: "Booking Cancelled" (grey banner)

Action panel (shown below timeline, context-sensitive):
- AWAITING_SIGNATURES → render ContractViewer
- AWAITING_PAYMENT → render Razorpay checkout button
- CONFIRMED (within 1 hour of start_dt) → render SixAnglePhotoUpload (CHECK_IN)
- CHECKED_IN → render SixAnglePhotoUpload (CHECK_OUT) + countdown to end_dt
- RETURN_SUBMITTED → render "Analysis in progress" spinner
- DAMAGE_REVIEW → render DamageReport component
- COMPLETED → render DamageReport + "Download Audit Log" button

### StateBadge component
Props: status: BookingStatus
Returns a pill badge. Colour map: COMPLETED=green, CANCELLED=grey, DISPUTE_OPEN=red, DAMAGE_REVIEW=orange, PENDING_APPROVAL=yellow, CONFIRMED=blue, rest=grey.

Output page.tsx, BookingTimeline.tsx, and StateBadge.tsx completely.
```

---

---

# ── SECTION 4 · INTEGRATION & DEMO PROMPTS ───────────────────────────────────

---

## PROMPT I-01 · Demo Data Pre-Cache Script

```
Using the Availo system context, write a Python script: scripts/precache_demo.py

This script prepares all slow AI operations BEFORE the demo so they serve instantly.

Steps:
1. Connect to DB (use DATABASE_URL from .env).
2. Find the demo booking (demo_user + Canon EOS R5, status=COMPLETED).
3. Pre-run damage analysis IF not already cached in Redis:
   - Fetch all 12 condition images (6 check-in + 6 check-out) from their URLs.
   - Call Gemini Vision with full batch prompt.
   - Store JSON result in Redis key: damage_result:{booking_id} with TTL 86400 (24h).
4. Pre-generate the contract PDF for the demo booking IF not already in Supabase Storage:
   - Call contract_service.generate_contract() — this also stores PDF in Supabase.
5. Print a checklist at the end:
   ✅ / ❌ Database connection
   ✅ / ❌ Supabase Storage accessible
   ✅ / ❌ Redis accessible
   ✅ / ❌ Gemini API responding
   ✅ / ❌ Demo damage result cached
   ✅ / ❌ Demo contract PDF generated
   ✅ / ❌ Demo users seeded

Run this with: python scripts/precache_demo.py
It must be safe to run multiple times (idempotent).
```

---

## PROMPT I-02 · End-to-End Flow Test

```
Using the Availo system context, write a Python integration test script: scripts/e2e_test.py

This script simulates the FULL booking lifecycle using httpx against a running local server (http://localhost:8000/api/v1).

Test the following flow sequentially, printing ✅ / ❌ for each step:

1. Register demo_user (or login if exists)
2. Register demo_owner (or login if exists)
3. Owner lists a new test resource: "E2E Test Camera"
4. User searches resources — verify test resource appears
5. User checks eligibility for test resource — should be ELIGIBLE
6. User submits booking request for tomorrow
7. Owner approves the booking
8. System auto-generates contract — poll GET /contracts/{booking_id} until status=PENDING_SIGNATURES (max 15 seconds)
9. User signs contract
10. Owner signs contract
11. Booking transitions to AWAITING_PAYMENT — verify
12. User confirms mock payment (POST /bookings/{id}/confirm-payment with razorpay_payment_id="test_pay_123")
13. Booking status = CONFIRMED — verify
14. User submits check-in (POST /conditions/{id}/checkin-complete with mock photo URLs)
15. User submits check-out (POST /conditions/{id}/checkout-complete with mock photo URLs)
16. Poll for damage analysis result — max 35 seconds
17. If damage_detected=false → verify booking.status = COMPLETED ✅
18. Print total elapsed time

Cleanup: DELETE the test resource and booking at the end.

Use httpx.AsyncClient for all requests. Print coloured output (green ✅, red ❌). Exit with code 1 if any step fails.
```

---

## PROMPT I-03 · Railway + Vercel Deployment Checklist

```
Generate a deployment checklist Markdown file: DEPLOY.md for the Availo project covering:

## Pre-Deploy (T-2 hours)
- [ ] Railway account created and CLI installed (npm install -g @railway/cli)
- [ ] railway login && railway init run inside /backend
- [ ] All environment variables set via railway variables set KEY=VALUE (list every variable from .env spec)
- [ ] railway up — confirm deploy succeeds, note the Railway URL
- [ ] Test: curl https://{railway-url}/docs — FastAPI Swagger UI must load
- [ ] UptimeRobot ping set to Railway URL + Supabase URL every 5 minutes

## Database (T-1.5 hours)
- [ ] alembic upgrade head run against production DATABASE_URL
- [ ] python scripts/seed.py run — verify demo users created
- [ ] python scripts/create_buckets.py run — verify 3 Supabase Storage buckets created with correct policies
- [ ] Supabase project NOT paused (last activity check)

## AI Pre-Cache (T-1 hour)
- [ ] python scripts/precache_demo.py run — all 7 checks green
- [ ] Manually hit GET /resources once to warm Redis cache

## Frontend (T-45 min)
- [ ] NEXT_PUBLIC_API_URL set to Railway URL in Vercel environment
- [ ] git push origin main — Vercel auto-deploys
- [ ] Test on Vercel URL: login, browse resources, check booking flow

## T-15 Min Demo Checklist
- [ ] Open demo_user session in Chrome (incognito)
- [ ] Open demo_owner session in Firefox
- [ ] Open admin session in Safari / Edge
- [ ] Pre-navigate: user to /resources, owner to /dashboard, admin to /admin
- [ ] WebSocket connected (check browser console — no WS errors)
- [ ] Condition photos pre-uploaded (6 before + 6 after) — URLs noted
- [ ] Contract pre-generated — PDF link working

## Known Risks + Mitigations
| Risk | Signal | Mitigation |
|------|--------|------------|
| Supabase paused | 500 on any DB call | UptimeRobot; restart from Supabase dashboard |
| Gemini rate limit (15 RPM) | 429 response | Pre-cached result served from Redis |
| Railway cold start | First request takes 8–10s | Hit /docs 5 min before demo |
| WebSocket drops | Toast "Reconnecting..." visible | ws.ts auto-reconnect fires in < 5s |
| Contract PDF slow | > 10s on first generation | Pre-generated in precache_demo.py |
```

---

---

# ── SECTION 5 · QUICK REFERENCE ─────────────────────────────────────────────

## Stack Versions Cheatsheet

| Package | Version |
|---------|---------|
| fastapi | 0.115.0 |
| sqlalchemy[asyncio] | 2.0.36 |
| pydantic | 2.9.2 |
| python-jose | 3.3.0 |
| google-generativeai | 0.8.3 |
| weasyprint | 62.3 |
| next | 15.0.3 |
| react | 19.0.0 |
| @tanstack/react-query | 5.59.20 |
| zustand | 5.0.1 |
| tailwindcss | 3.4.14 |
| lucide-react | 0.460.0 |

## Booking Status → UI Colour

| Status | Tailwind Class |
|--------|---------------|
| COMPLETED | bg-green-100 text-green-800 |
| CONFIRMED | bg-blue-100 text-blue-800 |
| PENDING_APPROVAL | bg-yellow-100 text-yellow-800 |
| DAMAGE_REVIEW | bg-orange-100 text-orange-800 |
| DISPUTE_OPEN | bg-red-100 text-red-800 |
| CANCELLED | bg-gray-100 text-gray-600 |
| WAITLISTED | bg-purple-100 text-purple-800 |

## API Route Prefix Map

| Domain | Base Path |
|--------|-----------|
| Auth | /api/v1/auth/* |
| Users | /api/v1/users/* |
| Resources | /api/v1/resources/* |
| Bookings | /api/v1/bookings/* |
| Conditions | /api/v1/conditions/* |
| Contracts | /api/v1/contracts/* |
| Incidents | /api/v1/incidents/* |
| Chat | /api/v1/chat/* |
| Admin | /api/v1/admin/* |
| WebSocket | /ws/{user_id} |

---

*Generated for Availo v1.0 — National Hackathon Edition*
