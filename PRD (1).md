# Product Requirements Document — Availo
## Trusted Resource-Sharing Platform for Institutions and Communities
> Version 1.0 | National Hackathon Edition | Team: Availo

---

## §1 — Problem Statement

Colleges, research laboratories, makerspaces, community organisations and small businesses own valuable equipment and spaces that sit unused for long stretches of time. Students, researchers, independent creators and early-stage teams who could benefit from these resources cannot afford to purchase or privately rent them. Existing booking platforms handle calendars — they do not handle trust.

The trust gap has two sides. **Owners** cannot verify who is using their equipment, whether the user is qualified, what condition the resource was in before and after use, or whether damage will be compensated. **Users** cannot prove their credentials, understand why a request was rejected, or know when a resource will actually be available to them. Both sides lack enforceable accountability.

**What is missing is not a booking system. What is missing is a governance layer built on top of one.**

Availo fills that layer with: credential-verified user profiles, AI-powered damage detection, legally binding digital contracts, escrow-protected payments, transparent allocation logic, and a complete auditable history for every resource transaction.

---

## §2 — Problem Analysis (5W2H)

| Dimension | Answer |
|-----------|--------|
| **Who** | Resource owners (faculty, lab managers, makerspace admins, community org leads); Resource users (students, researchers, early-stage founders, creators, freelancers) |
| **What** | No platform bridges booking with trust, verification, legal accountability, and damage resolution |
| **When** | Occurs every time a valuable shared resource changes hands — check-in, use, return |
| **Where** | University campuses, research institutes, community makerspaces, co-working facilities, small business tool-sharing groups |
| **Why** | Owners fear liability and property damage; institutional procurement processes prohibit ad-hoc sharing without formal records |
| **How (currently broken)** | Manual email chains; generic booking tools with no verification; verbal agreements with no enforcement; damage goes unrecorded or disputed endlessly |
| **How Much** | Equipment utilisation in universities averages 20–35% of capacity (EDUCAUSE, 2023); 67% of lab managers report they would share equipment if liability and damage concerns were addressed |

---

## §3 — Solution Overview

**Availo** is a resource-sharing platform where every transaction is verifiable, every condition is documented, and every party is protected.

An **owner** lists a resource with photos, availability windows, access conditions, eligibility rules, and usage fees. A **user** discovers the resource, checks their own eligibility, and submits a booking request with a stated purpose. The system verifies eligibility, generates a digital contract, holds payment in escrow, and guides both parties through check-in, use, return, and condition confirmation — entirely within the platform.

The key differentiators from any existing booking tool are:

1. **Verification Badges** — users prove occupation/qualifications; a Gemini-screened document check gates badge assignment, so a "Verified Researcher" label is meaningful, not decorative.
2. **Escrow Payment** — funds are held at booking confirmation and released only after return is confirmed damage-free. Users cannot escape payment; owners cannot withhold funds unfairly beyond a dispute window.
3. **AI Damage Detection** — six-direction photo capture (Front, Back, Left, Right, Top, Bottom) at check-in and check-out. Gemini Vision compares each pair, produces a confidence-scored damage report, and requests close-up photos of suspicious areas before releasing escrow.
4. **Digital Legal Contracts** — auto-generated from booking details, signed by both parties within the platform using a canvas signature. Stored as a tamper-evident hashed PDF. No DocuSign subscription needed.
5. **In-Platform Chat** — real-time messaging between user and owner, linked to the booking, persisted as an auditable communication record.

---

## §4 — User Personas

### Persona 1 — Resource Owner / Institution Representative
| Field | Detail |
|-------|--------|
| Name | Dr. Meera Nair |
| Role | Lab Manager, Materials Engineering Department |
| Tech literacy | Medium |
| Resources managed | Scanning electron microscope, 3D printers, tensile testing machine |
| Pain points | Cannot allow unsupervised access; worried about damage; no way to enforce usage limits; paperwork for every external user |
| What success looks like | List once, approve once, get a signed contract automatically, see timestamped condition photos before and after, have escrow cover any damage |
| Primary device | Desktop (office) |

### Persona 2 — Verified Professional User
| Field | Detail |
|-------|--------|
| Name | Rohan Sharma |
| Role | PhD Researcher, Materials Science, different institution |
| Tech literacy | High |
| Pain point | Cannot access specialised equipment at other institutions; months-long procurement if buying outright |
| What success looks like | Find available equipment, prove credentials once, book, check in with photo record, return cleanly, get deposit back automatically |
| Primary device | Mobile + Desktop |

### Persona 3 — Student / Early-Stage User
| Field | Detail |
|-------|--------|
| Name | Priya Krishnan |
| Role | Final-year engineering student building a prototype |
| Tech literacy | High |
| Pain point | Cannot afford cameras, fabrication tools; maker competition deadlines don't align with college lab hours |
| What success looks like | Filter by "student-eligible" resources, understand exactly what training is required, book, pay only if returned safely |
| Primary device | Mobile |

### Persona 4 — Platform Administrator
| Field | Detail |
|-------|--------|
| Name | Vikram Singh |
| Role | Platform admin / community manager |
| Tech literacy | Very high |
| Responsibility | Approve verification badges, moderate disputes, configure fair-usage rules, audit flagged transactions |
| What success looks like | Dashboard showing all pending verifications, active disputes, overdue returns, and platform-wide utilisation metrics |
| Primary device | Desktop |

---

## §5 — User Stories

| ID | Persona | Story | Priority |
|----|---------|-------|----------|
| US-01 | Owner | As an owner, I want to list a resource with photos, availability, eligibility requirements, and a refundable deposit amount so that only suitable users can book it | M |
| US-02 | User | As a user, I want to search and filter resources by type, location, date, and my verified credentials so I only see resources I am eligible to book | M |
| US-03 | User | As a user, I want to submit a booking request with a stated purpose so the owner can make an informed approval decision | M |
| US-04 | Owner | As an owner, I want to approve, reject, or waitlist a booking request with a reason so that users understand the outcome | M |
| US-05 | User | As a user, I want to upload my qualification documents once and receive a verified badge so I don't have to re-prove credentials for every booking | M |
| US-06 | User | As a user, I want a digital contract generated from my booking details that both the owner and I must sign before access is granted | M |
| US-07 | User | As a user, I want to check in by uploading six directional photos of the resource so the initial condition is on record | M |
| US-08 | User | As a user, I want to check out by uploading six matching directional photos so any damage is documented and not disputed later | M |
| US-09 | Platform | As the system, I want to use AI to compare check-in and check-out photos and produce a damage confidence score, requesting close-up photos if suspicious | M |
| US-10 | User | As a user, I want the platform to hold my payment in escrow and release it to the owner only after a clean return is confirmed | M |
| US-11 | Owner | As an owner, I want to initiate a damage report if the AI flags issues so a dispute resolution process begins automatically | M |
| US-12 | User/Owner | As either party, I want to message the other party within the platform so all communication is recorded against the booking | M |
| US-13 | User | As a user, I want to see a transparent waiting list position and estimated availability if a resource is fully booked | S |
| US-14 | Admin | As an admin, I want to see all pending badge verifications and approve or reject them with a reason | M |
| US-15 | User | As a user, I want to cancel a booking before check-in with a clear refund policy applied automatically | S |
| US-16 | Owner | As an owner, I want to set a fair-usage limit (e.g. max 3 bookings per user per month) so no single user monopolises my resource | S |
| US-17 | User/Owner | As either party, I want to view the complete auditable history of our transaction in one timeline | M |
| US-18 | Admin | As an admin, I want to see overdue returns flagged and be able to escalate them to a formal incident | S |
| US-19 | Owner | As an owner, I want real-time notifications for new booking requests, check-ins, check-outs, and damage reports | M |
| US-20 | User | As a user, I want a reminder 24 hours before my booking and 1 hour before my return is due | S |

---

## §6 — Functional Requirements

### 6.1 Resource Management
| ID | Requirement | Demo Verification |
|----|-------------|-------------------|
| FR-01 | Owner can create a resource listing with name, category, description, location, photos (up to 10), availability windows, deposit amount, and usage fee per hour/day | Create listing → resource appears in search |
| FR-02 | Owner can define eligibility rules: required badge types, minimum trust score, institution restrictions, training certification flags | Set "Verified Researcher" required → unverified user sees lock on booking |
| FR-03 | Owner can set fair-usage limits: max bookings per user per rolling 30 days, max continuous booking duration | Exceed limit → system blocks new request with explanation |
| FR-04 | Owner can define cancellation policy: full refund window, partial refund window, no refund after | Cancel within window → correct refund applied |
| FR-05 | Resource listings display real-time availability calendar | Calendar updates within 5s of a confirmed booking |

### 6.2 Discovery and Search
| ID | Requirement | Demo Verification |
|----|-------------|-------------------|
| FR-06 | Full-text search across resource name, description, category, and location | Search "electron microscope" → correct results |
| FR-07 | Filter by: category, date range, price range, location, required badge level, availability | Apply filters → correctly narrowed results |
| FR-08 | Eligibility gate: booking button shows user's current eligibility status and missing requirements | Unverified user sees "Requires: Researcher Badge" with link to verify |
| FR-09 | AI-assisted matching: Gemini suggests resources matching user's stated project description | Enter "carbon fibre composite testing" → ranked resource suggestions |

### 6.3 Verification Badge System
| ID | Requirement | Demo Verification |
|----|-------------|-------------------|
| FR-10 | User submits verification request: selects badge type (Student, Researcher, Professional, Institution), uploads credential documents | Submit → pending badge shown on profile |
| FR-11 | Gemini Vision pre-screens uploaded documents for authenticity signals (institution logo, issue date, name match) and produces a pre-check confidence score | Pre-check result shown to admin with confidence score |
| FR-12 | Admin reviews pre-check result, views documents, and approves or rejects with a mandatory reason | Admin action → user notified instantly via WebSocket |
| FR-13 | Approved badge appears on user profile with badge type, issuing context, and date. Badge is shown on all booking requests | Badge visible on user card in owner's approval view |
| FR-14 | Badges expire based on document validity (e.g. institutional email domains auto-checked annually) | Expired badge → user prompted to re-verify |

### 6.4 Booking Request Workflow
| ID | Requirement | Demo Verification |
|----|-------------|-------------------|
| FR-15 | User submits booking request: date range, time slot, purpose statement, acknowledgement of usage conditions | Request appears in owner's queue |
| FR-16 | System auto-checks eligibility rules against user's current badge set and trust score before allowing submission | Ineligible user → cannot submit; specific missing requirements displayed |
| FR-17 | Owner reviews request with full user profile, badge display, purpose, and past booking history on same screen | Owner approves/rejects from single view |
| FR-18 | Owner can approve, reject (with reason), or explicitly waitlist (with position shown to user) | User receives notification with outcome and reason |
| FR-19 | Competing requests for same slot: first-in-time wins by default; owner may manually override with justification | Conflicting request → second requester auto-waitlisted with position |
| FR-20 | Scheduling conflict detection: system prevents overlapping confirmed bookings automatically | Overlap attempt → system blocks with "Slot unavailable" message |

### 6.5 Digital Contract System
| ID | Requirement | Demo Verification |
|----|-------------|-------------------|
| FR-21 | Upon approval, system auto-generates a contract PDF using resource details, booking dates, user details, fee, deposit, usage conditions, and damage liability clause | Contract generated within 10 seconds of approval |
| FR-22 | Both owner and user receive a notification to review and sign the contract within the platform | Both parties see "Awaiting your signature" prompt |
| FR-23 | In-platform signature: user draws or types signature on canvas; system records signature image, timestamp, IP address, and user ID | Signature recorded with metadata |
| FR-24 | Booking status moves to CONFIRMED only after both parties have signed | Unsigned → booking stays AWAITING_SIGNATURES; no check-in allowed |
| FR-25 | Signed contract stored as PDF with SHA-256 hash; hash stored in DB for tamper-evidence verification | Contract viewable and hash verifiable in booking history |

### 6.6 Payment and Escrow
| ID | Requirement | Demo Verification |
|----|-------------|-------------------|
| FR-26 | Upon booking confirmation (both signatures), user is prompted to pay: usage fee + refundable deposit | Payment prompt appears post-signature |
| FR-27 | Payment held in escrow (Razorpay Order with capture_on_hold) until return confirmed | Payment shown as "held" in booking detail |
| FR-28 | Deposit auto-released to user within 24h of clean return confirmation | Damage-free return → release timer shown |
| FR-29 | If AI damage detection flags issues: escrow split between repair deduction and user refund, or fully withheld pending dispute resolution | Damage flag → escrow held, both parties notified |
| FR-30 | User cannot cancel after check-in without triggering the damage report flow | Post-check-in cancel attempt → redirected to damage flow |
| FR-31 | Refund policy enforced automatically: full/partial/none based on cancellation timing vs policy window | Cancel inside window → automatic partial refund |

### 6.7 Check-In and Condition Reporting
| ID | Requirement | Demo Verification |
|----|-------------|-------------------|
| FR-32 | Check-in requires user to upload exactly 6 photos in defined orientations: Front, Back, Left Side, Right Side, Top, Bottom | System enforces all 6 before check-in can be submitted |
| FR-33 | Each photo is uploaded to Cloudinary with client-side EXIF extraction; server validates: timestamp within ±30 min of booking start, GPS coordinates within 500m of resource location (if enabled) | Out-of-range photo rejected with specific error |
| FR-34 | Owner receives check-in notification with all 6 photos and can add a comment or flag a concern within 2h | Owner comment attached to condition report |
| FR-35 | Check-out mirrors check-in: same 6 orientations captured at same location | Check-out photos required before return can be submitted |

### 6.8 AI Damage Detection
| ID | Requirement | Demo Verification |
|----|-------------|-------------------|
| FR-36 | Gemini Vision receives before/after pairs for each of the 6 orientations and returns: damage_detected (bool), damage_description (string), confidence_score (0.0–1.0), suspicious_regions (list of bounding descriptions) | AI result visible within 30s of check-out submission |
| FR-37 | If any orientation has confidence_score > 0.6 and damage_detected = true, system requests a close-up photo of the flagged region before finalising | Close-up prompt appears with description of suspicious area |
| FR-38 | Final damage report aggregates all orientation results into an overall severity: NONE / MINOR / MODERATE / SEVERE | Severity badge shown on booking summary |
| FR-39 | Damage report is stored immutably and shared with both parties and admin | Both parties see identical report; no edit possible post-generation |

### 6.9 Dispute and Incident Management
| ID | Requirement | Demo Verification |
|----|-------------|-------------------|
| FR-40 | Either party can raise a dispute within 48h of return confirmation | Dispute button visible in booking history |
| FR-41 | Dispute triggers escrow freeze and admin notification | Escrow status changes to FROZEN |
| FR-42 | Admin reviews damage photos, AI report, chat history, and contract, then issues a resolution: release to owner, return to user, or split | Resolution recorded in audit log; escrow action executed |
| FR-43 | Overdue returns (booking end time + 1h grace) trigger automatic owner notification and system incident flag | Overdue flag visible in admin panel |
| FR-44 | Repeat violations (e.g. 2+ overdue returns, 1 confirmed damage) reduce user trust score, which blocks access to restricted resources | Trust score shown on user profile; reduced score gates high-risk resources |

### 6.10 In-Platform Chat
| ID | Requirement | Demo Verification |
|----|-------------|-------------------|
| FR-45 | Owner and user can exchange messages within a booking's chat thread, accessible from the booking detail view | Message sent → received in real time without page refresh |
| FR-46 | System auto-posts status messages into the chat thread: "Booking approved by [owner]", "Contract signed", "Check-in recorded", "Return confirmed" | Status messages visible alongside manual messages |
| FR-47 | Image attachments allowed within chat (for sharing instructions, additional condition photos) | Image preview in chat |
| FR-48 | Chat thread becomes read-only after booking reaches COMPLETED or CANCELLED state | Send button hidden post-completion |
| FR-49 | Chat history stored and accessible in booking audit view | Admin can view full chat thread |

### 6.11 Notifications
| ID | Requirement | Demo Verification |
|----|-------------|-------------------|
| FR-50 | Real-time in-app notifications via WebSocket for: new request, approval/rejection, signature required, payment required, check-in confirmed, return due, overdue return, damage report, dispute raised, dispute resolved | Notification bell shows count; popover lists items |
| FR-51 | Email notifications for high-priority events (approval, damage report, dispute) using SMTP / Resend free tier | Email sent within 60s of trigger event |
| FR-52 | Booking reminders: 24h before booking start, 1h before return due | Notifications appear at correct times |

### 6.12 Audit and History
| ID | Requirement | Demo Verification |
|----|-------------|-------------------|
| FR-53 | Every state change in a booking is recorded in audit_logs: actor, action, from_state, to_state, timestamp, metadata | Audit log visible on booking detail |
| FR-54 | Resource owners can view full history of all bookings per resource, including condition reports and damage flags | Resource history page shows complete timeline |
| FR-55 | Admin can export audit logs for a booking or resource as JSON | Export button produces downloadable file |

---

## §7 — Non-Functional Requirements

| Category | Requirement | Target |
|----------|-------------|--------|
| Performance | API response (non-AI) | < 200ms p95 |
| Performance | AI damage analysis (6 photos) | < 30 seconds |
| Performance | Contract PDF generation | < 10 seconds |
| Performance | WebSocket message delivery | < 500ms |
| Availability | Demo uptime | 99.9% |
| Security | All endpoints authenticated | JWT (access: 15m, refresh: 7d) |
| Security | Payment data | Never touches our server — Razorpay handles card data |
| Security | Uploaded documents (verification) | Encrypted at rest in Cloudinary; access via signed URLs only |
| Scalability | Designed for | 100 concurrent users (demo) |
| Auditability | Every state change | Immutable audit log entry |
| Privacy | PII handling | User documents stored in private Cloudinary folder; signed URL expires in 1h |
| Fairness | Allocation transparency | Every waitlist position, rejection reason, and fair-usage block includes a plain-language explanation |

---

## §8 — Feature Scope

### In Scope (MVP)
- Resource listing with photos, availability, eligibility rules, fair-usage caps
- Full-text search + category/date/badge filtering
- Eligibility gate on booking UI
- AI-assisted resource matching (Gemini text)
- Verification badge flow: submission → Gemini pre-screen → admin review → badge assignment
- Booking request → approve/reject/waitlist workflow
- Digital contract: auto-generation → dual canvas signature → PDF storage with SHA-256 hash
- Razorpay test-mode payment with escrow simulation
- 6-direction photo check-in and check-out
- AI damage detection (Gemini Vision) with close-up request
- Damage report + dispute flow
- Real-time in-platform chat (WebSocket)
- In-app notifications (WebSocket) + Email (Resend)
- Fair-usage enforcement (booking limits per user per resource)
- Waitlist with transparent position
- Audit log on every booking
- Role-based access: User, Owner, Admin
- Trust score system (auto-updated on violations)

### Out of Scope (Hackathon)
- Native mobile app (responsive web only)
- Production payment (live Razorpay keys)
- Video call / screen share
- Multi-language support
- Advanced analytics / utilisation dashboards
- Public API for third-party integrations
- SMS notifications

### Future Roadmap
| Feature | Why Later |
|---------|-----------|
| Blockchain-anchored contract hashes | Smart contract deployment complexity |
| IoT lock integration (NFC check-in) | Hardware dependency |
| Insurance product integration | Partner/legal agreements required |
| AI-powered pricing suggestions | Requires booking history dataset |
| Credit-based resource exchange (no-cash sharing) | Currency design complexity |
| ABAC (Attribute-Based Access Control) per resource | Extends RBAC — post-MVP |

---

## §9 — Role-Based Access Matrix

| Action | Unverified User | Verified User | Owner | Admin |
|--------|----------------|--------------|-------|-------|
| Browse resources | ✓ | ✓ | ✓ | ✓ |
| View resource detail | ✓ | ✓ | ✓ | ✓ |
| Submit booking request | — | ✓ (if eligible) | — | ✓ |
| List a resource | — | ✓ | ✓ | ✓ |
| Approve/reject booking | — | — | ✓ (own) | ✓ |
| Sign contract | ✓ (own booking) | ✓ (own booking) | ✓ (own resource) | ✓ |
| Upload condition photos | — | ✓ (own booking) | — | ✓ |
| View damage report | ✓ (own) | ✓ (own) | ✓ (own) | ✓ |
| Raise dispute | ✓ (own) | ✓ (own) | ✓ (own) | ✓ |
| Resolve dispute | — | — | — | ✓ |
| Approve verification badges | — | — | — | ✓ |
| View all bookings | — | — | ✓ (own resources) | ✓ |
| Export audit log | — | — | ✓ (own resources) | ✓ |
| Manage fair-usage rules | — | — | ✓ (own resources) | ✓ |

---

## §10 — Success Metrics

| Metric | Without Availo | With Availo | Demo Show |
|--------|---------------|------------|-----------|
| Trust gap resolution | Email + verbal → unenforceable | Contract + escrow → legally backed | Show signed contract + escrow status |
| Damage dispute resolution | Days/weeks, no evidence | < 48h with AI photo evidence | Show AI damage report in 30s |
| Credential verification | Manual, days | AI pre-screen + admin in < 24h | Show badge granted in demo |
| Equipment utilisation | 20–35% | Targeted towards 60–70% (visible availability) | Show calendar availability |
| Booking abandonment | High (trust fear) | Low (escrow + contract reassures both sides) | Show end-to-end flow confidence |

---

## §11 — Booking State Machine

```
DRAFT → PENDING_APPROVAL → [APPROVED / REJECTED / WAITLISTED]
APPROVED → AWAITING_SIGNATURES → AWAITING_PAYMENT
AWAITING_PAYMENT → CONFIRMED
CONFIRMED → CHECKED_IN
CHECKED_IN → RETURN_SUBMITTED
RETURN_SUBMITTED → [DAMAGE_REVIEW / COMPLETED]
DAMAGE_REVIEW → [DISPUTE_OPEN / COMPLETED]
DISPUTE_OPEN → [RESOLVED_OWNER / RESOLVED_USER / RESOLVED_SPLIT]

At any state before CHECKED_IN:
CONFIRMED / AWAITING_SIGNATURES → CANCELLED (with refund policy applied)
```

---

## §12 — Dependencies

| Dependency | Type | Risk if Unavailable | Mitigation |
|------------|------|---------------------|------------|
| Gemini 2.0 Flash (Vision + Text) | AI | Damage detection fails; matching fails | Pre-run damage analysis on demo photos; cache result; mock fallback label "AI Review Pending" |
| Razorpay Test Mode | Payment | Escrow simulation fails | Pre-confirm a test payment; store mock order ID in seed data |
| Cloudinary (Free Tier) | Image Storage | Photo upload fails | Pre-upload demo photos; serve from DB as base64 for demo fallback |
| Supabase PostgreSQL | Database | All data operations fail | SQLite fallback for demo; UptimeRobot ping every 6 days |
| Upstash Redis | Cache | Slower responses | In-memory dict fallback for session duration |
| Resend (Email) | Notifications | Email delivery fails | In-app WebSocket notifications remain functional; email is supplementary |
| Railway | Backend Hosting | API unreachable | Deploy 24h before demo; UptimeRobot ping; test on prod URL T-30 min |

---

## §13 — Risk Register

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Gemini Vision slow on 6 photos | Medium | High | Batch all 6 pairs into one API call with structured prompt; pre-cache demo result |
| Razorpay webhook not reachable | Medium | Medium | Demo uses polling to check order status; webhook is nice-to-have |
| Supabase instance paused | High | High | UptimeRobot; test T-30 min; SQLite fallback if needed |
| Contract PDF generation slow | Low | Medium | Pre-generate demo contract; serve cached PDF |
| Signature canvas not rendering on judge's device | Low | High | Test on Chrome, Safari, Firefox; have mobile fallback |
| Cloudinary upload times out | Low | High | Pre-upload all 12 demo photos (6 before + 6 after); store in Cloudinary; reference by URL |

---

## §14 — Hackathon Criteria Alignment

| Criterion | How Availo Addresses It |
|-----------|------------------------|
| **Innovation** | AI damage detection via 6-direction photo pairs is unique; digital contracts generated and signed in-platform without third-party service; escrow without a payment processor building custom logic |
| **Technical Execution** | FastAPI + Next.js 15 + PostgreSQL + Gemini Vision + Razorpay + Cloudinary + WebSocket; full booking lifecycle operational end-to-end |
| **Problem–Solution Fit** | Directly maps to every line of the hackathon problem statement; 10-step lifecycle demonstrated live |
| **Design / UX** | Booking state machine displayed visually; eligibility shown inline; damage report with photo comparison side-by-side; chat embedded in booking |
| **Completeness** | Judge can complete a full resource-sharing journey — list, discover, request, approve, sign, pay, check in, return, damage review — without team intervention |

---

## §15 — Glossary

| Term | Definition |
|------|------------|
| Verification Badge | A profile credential granted after admin review of uploaded qualification documents |
| Escrow | Payment held by the platform until return is confirmed; neither party controls it during the booking |
| Condition Report | The six-direction photo set captured at check-in and check-out |
| Damage Confidence Score | Gemini Vision's 0.0–1.0 score for each photo pair indicating likelihood of damage |
| Fair-Usage Limit | Owner-defined cap on how many times or how long a single user can book a resource in a period |
| Trust Score | A user-level score (0–100) that decays on violations and gates access to high-trust resources |
| Waitlist | A transparent, position-numbered queue for users requesting an already-booked resource slot |
| Audit Log | An immutable append-only record of every state change in a booking |
| Digital Contract | Auto-generated booking agreement signed in-platform; stored with a SHA-256 tamper-evidence hash |
| Check-In | The act of taking and uploading 6-direction photos at the start of resource use, confirming initial condition |
| Check-Out | The act of taking and uploading 6-direction photos at resource return, enabling damage comparison |
