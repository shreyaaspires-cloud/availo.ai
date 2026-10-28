# Tech Stack — Availo
## Trusted Resource Sharing Platform for Institutions and Communities
> Version 1.0 | All versions locked | Free-tier limits documented

---

## §1 — Stack Summary

| Layer | Technology | Version | Why This |
|-------|------------|---------|----------|
| **Backend Framework** | **FastAPI** | **0.115.x** | Async-first, Pydantic v2 built-in, auto-docs at /docs, ideal for file-upload + AI pipelines |
| **Language (Backend)** | Python | **3.12.x** | Best ecosystem for AI/ML, image processing (PIL, OpenCV), PDF generation |
| **Validation (Backend)** | Pydantic | **v2.x** | Type-safe request/response models across complex booking/approval flows |
| **Frontend Framework** | Next.js | **15.x** | App Router, RSC, Vercel-optimized. ⚠️ params/cookies/searchParams are async in v15 |
| **Language (Frontend)** | TypeScript | **5.5.x** | Type safety; strict mode required |
| **Styling** | Tailwind CSS | **3.4.x** | Utility-first; design tokens for role-based UI colour schemes |
| **State — Server** | TanStack Query | **5.x** | Caching, background refetch; booking status polling |
| **State — Client** | Zustand | **4.x** | Auth store + role store (User / Owner / Manager / Admin) |
| **Real-time** | WebSocket (FastAPI native) | — | Live approval notifications, chat messages, booking status updates |
| **Database** | **PostgreSQL via Supabase** | 15.x | ACID; JSONB for condition reports; row-level security for role isolation |
| **ORM** | SQLAlchemy (async) | **2.x** + Alembic | Type-safe queries; async engine; schema migrations |
| **File Storage** | **Supabase Storage** | — | Free 1 GB; stores condition photos (6-angle before/after), verification docs, contract PDFs |
| **Cache** | Redis via **Upstash** | SDK 1.x | Free: 10,000 cmd/day; approval-queue caching, notification dedup, rate-limit counters |
| **Auth** | JWT + passlib/bcrypt | python-jose **3.x**, passlib **1.7.x** | Stateless; role-based claims in JWT payload |
| **AI — Damage Detection** | **Google Gemini 2.0 Flash** | `google-generativeai 0.8.x` | Free: 15 RPM, 1M TPM; vision API for before/after image comparison |
| **AI — Contract Generation** | **Google Gemini 2.0 Flash** | same | Generates plain-language rental contracts from booking terms |
| **AI — Verification Badge** | **Google Gemini 2.0 Flash** | same | Classifies uploaded credential docs for profession verification |
| **Image Processing** | Pillow + OpenCV | **10.x / 4.x** | EXIF timestamp extraction, image fingerprinting, tamper detection pre-AI |
| **PDF Generation** | WeasyPrint | **62.x** | Renders HTML→PDF contracts; no headless Chrome dependency |
| **E-Signature** | Custom (canvas-based) | — | Inline HTML5 canvas signature capture; stored as PNG + embedded in contract PDF |
| **Task Queue** | asyncio + FastAPI BackgroundTasks | — | Async damage analysis, contract generation, notification dispatch |
| **Email Notifications** | **Resend** | SDK 0.7.x | Free: 100 emails/day; approval, reminder, overdue, damage alerts |
| **Hosting — Backend** | **Railway** | — | $5/month free credit; no cold start; deploy from GitHub |
| **Hosting — Frontend** | **Vercel** | — | Free; auto-deploy; 100 GB bandwidth/month |
| **Icons** | Lucide React | **0.460.x** | Resource, booking, damage, contract icons |
| **Charts** | Recharts | **2.x** | Utilisation timelines, fair-use histograms, wait-time trends |
| **Maps** | Leaflet + React-Leaflet | **1.9.x** | Resource location display; no API key needed |

---

## §2 — Free Tier Limits (Demo Day Critical)

| Service | Key Limit | Demo Usage | Risk |
|---------|-----------|-----------|------|
| Supabase PostgreSQL | 500 MB storage; **pauses after 7 days inactivity** | ~80 MB | ⚠️ PAUSE RISK — use UptimeRobot |
| Supabase Storage | 1 GB; 2 GB egress | ~200 MB demo photos | Low |
| Upstash Redis | 10,000 commands/day | ~800 for demo | Low |
| Gemini 2.0 Flash | 15 RPM, 1M TPM | ~10 RPM | Medium — pre-cache damage results |
| Resend | 100 emails/day | ~10 demo emails | Low |
| Vercel | 100 GB bandwidth/month | ~2 GB | Low |
| Railway | $5/month free credit | ~$0.50 for 24hr hack | Very Low |
| WeasyPrint | Open source; CPU rendering | ~2 sec/contract PDF | Low — pre-generate demo contracts |

---

## §3 — Hosting Decision

> ⚠️ Create Railway account and test deploy **before hackathon day**. Railway provision + DNS can take 10–15 minutes. Test Supabase Storage bucket permissions separately — public vs. signed URL policy matters for image display.

### Railway (Backend)
```bash
# Install Railway CLI
npm install -g @railway/cli

# Init and deploy
railway login
railway init
railway up

# Set env vars
railway variables set GEMINI_API_KEY=xxx SUPABASE_URL=xxx SUPABASE_SERVICE_KEY=xxx ...
```

### Vercel (Frontend)
```bash
# Automatic deploy from GitHub
# Set NEXT_PUBLIC_API_URL=https://your-backend.railway.app/api/v1
# Set NEXT_PUBLIC_WS_URL=wss://your-backend.railway.app
```

---

## §4 — Python Dependencies (requirements.txt)

```txt
# Web framework
fastapi==0.115.0
uvicorn[standard]==0.30.6
python-multipart==0.0.12   # required for file uploads

# Database
sqlalchemy[asyncio]==2.0.36
asyncpg==0.30.0
alembic==1.14.0

# Validation
pydantic==2.9.2
pydantic-settings==2.6.1

# Auth
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4

# Cache
upstash-redis==1.3.0

# Storage (Supabase)
supabase==2.9.1
storage3==0.8.1

# AI
google-generativeai==0.8.3

# Image processing
Pillow==10.4.0
opencv-python-headless==4.10.0.84  # headless — no GUI deps on Railway

# PDF generation
weasyprint==62.3

# Email
resend==0.7.0

# Rate limiting
slowapi==0.1.9

# Utilities
python-dotenv==1.0.1
httpx==0.27.2
websockets==13.1
python-dateutil==2.9.0
pytz==2024.2
```

---

## §5 — Node.js Dependencies (package.json — Frontend)

```json
{
  "dependencies": {
    "next": "15.0.3",
    "react": "19.0.0",
    "react-dom": "19.0.0",
    "typescript": "5.5.4",
    "@tanstack/react-query": "5.59.20",
    "zustand": "5.0.1",
    "tailwindcss": "3.4.14",
    "lucide-react": "0.460.0",
    "recharts": "2.13.3",
    "leaflet": "1.9.4",
    "react-leaflet": "4.2.1",
    "@types/leaflet": "1.9.14",
    "react-signature-canvas": "1.0.6",
    "date-fns": "4.1.0",
    "clsx": "2.1.1",
    "react-hot-toast": "2.4.1",
    "react-dropzone": "14.3.5"
  },
  "devDependencies": {
    "@types/react": "19.0.1",
    "@types/node": "22.9.0",
    "eslint": "9.14.0",
    "eslint-config-next": "15.0.3",
    "postcss": "8.4.47",
    "autoprefixer": "10.4.20"
  }
}
```

---

## §6 — Environment Variables

```bash
# ===== BACKEND (.env) =====
APP_ENV=development
PORT=8000
FRONTEND_URL=http://localhost:3000

# Auth
JWT_SECRET=your-jwt-secret-at-least-32-characters-long
JWT_ACCESS_EXPIRES_MINUTES=60
JWT_REFRESH_EXPIRES_DAYS=30

# Database (Supabase PostgreSQL)
DATABASE_URL=postgresql+asyncpg://postgres:[password]@[host]:5432/postgres
DIRECT_URL=postgresql://postgres:[password]@[host]:5432/postgres

# Supabase Storage
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_SERVICE_KEY=your-service-role-key   # NOT the anon key
SUPABASE_STORAGE_BUCKET_CONDITIONS=condition-photos
SUPABASE_STORAGE_BUCKET_DOCS=verification-docs
SUPABASE_STORAGE_BUCKET_CONTRACTS=contracts

# Cache (Upstash)
UPSTASH_REDIS_URL=https://xxx.upstash.io
UPSTASH_REDIS_TOKEN=your-token

# AI
GEMINI_API_KEY=your-gemini-api-key
GEMINI_MODEL=gemini-2.0-flash

# Email
RESEND_API_KEY=re_xxxx
RESEND_FROM_EMAIL=notifications@availo.app

# Fair-use policy
MAX_ACTIVE_BOOKINGS_PER_USER=3
MAX_BOOKINGS_PER_RESOURCE_PER_WEEK=2
WAITLIST_AUTO_PROMOTE_MINUTES=30

# Demo credentials (seeded)
DEMO_USER_PASSWORD=DemoUser@Availo
DEMO_OWNER_PASSWORD=DemoOwner@Availo
DEMO_ADMIN_PASSWORD=DemoAdmin@Availo


# ===== FRONTEND (.env.local) =====
# ⚠️ Must end WITHOUT trailing slash
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_WS_URL=ws://localhost:8000
NEXT_PUBLIC_APP_NAME=Availo
NEXT_PUBLIC_SUPABASE_URL=https://xxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
```

---

## §7 — Required TypeScript Configuration

```json
{
  "compilerOptions": {
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "target": "ES2022",
    "module": "ESNext",
    "moduleResolution": "bundler",
    "lib": ["ES2022", "DOM"],
    "jsx": "preserve",
    "esModuleInterop": true,
    "skipLibCheck": true,
    "noEmit": true,
    "paths": {
      "@/*": ["./src/*"]
    }
  }
}
```

---

## §8 — Next.js 15 Breaking Changes

```typescript
// ❌ v14 pattern — BREAKS in v15
export default function Page({ params }: { params: { id: string } }) {
  return <div>{params.id}</div>
}

// ✅ v15 pattern
export default async function Page({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params
  return <div>{id}</div>
}
// Same applies to cookies(), headers(), searchParams — all async in v15
```

---

## §9 — AI Integration Overview

### Gemini Vision — Damage Detection
```python
# Accepts 6 before-images + 6 after-images (same angles)
# Returns: match_status, anomalies[], confidence, requires_closeup (bool)
model = genai.GenerativeModel("gemini-2.0-flash")
response = model.generate_content([image_parts..., prompt])
# Prompt requests JSON: {"match": bool, "anomalies": [...], "confidence": 0.0-1.0, "closeup_required": bool}
```

### Gemini Text — Contract Generation
```python
# Input: booking_details + resource_terms + user/owner profiles
# Output: plain-language rental contract HTML → WeasyPrint → PDF
```

### Gemini Vision — Verification Badge
```python
# Input: uploaded qualification doc (degree, licence, certificate)
# Output: {"verified": bool, "profession": str, "badge_type": str, "confidence": float}
```

---

## §10 — Local Development Setup

```bash
# Clone and install backend
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # fill values

# Create Supabase storage buckets (run once)
python scripts/create_buckets.py

# Run DB migrations
alembic upgrade head

# Seed demo data
python scripts/seed.py

# Start backend
uvicorn app.main:app --reload --port 8000

# ---- separate terminal ----

# Install frontend
cd frontend
npm install
cp .env.example .env.local  # fill values

# Start frontend
npm run dev  # starts on port 3000
```

---

## §11 — Tech Choice Rationale (Judge Talking Points)

| Decision | Why We Made It |
|----------|----------------|
| FastAPI over Node/Express | Native async for concurrent booking requests; Python-native image processing and Gemini SDK |
| Supabase over Firebase | PostgreSQL gives us complex booking queries with JOINs; row-level security enforces owner-can-only-see-their-resources |
| Supabase Storage over S3 | Integrated with auth; signed URLs for private condition photos; free tier sufficient |
| Gemini Vision for damage | No labelled training data needed; zero-shot image comparison with a single prompt; free tier at 15 RPM |
| WeasyPrint over Puppeteer | No headless Chrome on Railway free tier; WeasyPrint is pure Python, renders HTML→PDF reliably |
| Redis for waitlist | O(1) queue position lookups; atomic increment for fair-use counters; 30-minute promotion TTL |
| WebSocket for notifications | Approval alerts must reach users in < 2 seconds; polling creates visible UX lag during demo |
| Leaflet (no API key) | Google Maps requires billing; Leaflet + OpenStreetMap tiles are free and work offline |
