# Availo Deployment Checklist (Railway + Vercel)

## Pre-Deploy (T-2 hours)
- [ ] Railway account created and CLI installed (`npm install -g @railway/cli`)
- [ ] `railway login && railway init` run inside `/backend`
- [ ] All environment variables set via `railway variables set KEY=VALUE`:
  - `APP_ENV=production`
  - `PORT=8000`
  - `FRONTEND_URL=https://availo.vercel.app`
  - `JWT_SECRET=...`
  - `DATABASE_URL=postgresql+asyncpg://...`
  - `SUPABASE_URL=...`
  - `SUPABASE_SERVICE_KEY=...`
  - `UPSTASH_REDIS_URL=...`
  - `UPSTASH_REDIS_TOKEN=...`
  - `GEMINI_API_KEY=...`
  - `RESEND_API_KEY=...`
- [ ] `railway up` — confirm deploy succeeds, note the Railway URL
- [ ] Test: `curl https://{railway-url}/docs` — FastAPI Swagger UI must load
- [ ] UptimeRobot ping set to Railway URL + Supabase URL every 5 minutes

## Database (T-1.5 hours)
- [ ] `alembic upgrade head` run against production `DATABASE_URL`
- [ ] `python scripts/seed.py` run — verify demo users created
- [ ] `python scripts/create_buckets.py` run — verify 3 Supabase Storage buckets created with correct policies
- [ ] Supabase project NOT paused (last activity check)

## AI Pre-Cache (T-1 hour)
- [ ] `python scripts/precache_demo.py` run — all 7 checks green
- [ ] Manually hit `GET /resources` once to warm Redis cache

## Frontend (T-45 min)
- [ ] `NEXT_PUBLIC_API_URL` set to Railway URL in Vercel environment
- [ ] `NEXT_PUBLIC_WS_URL` set to wss://Railway URL in Vercel environment
- [ ] `git push origin main` — Vercel auto-deploys
- [ ] Test on Vercel URL: login, browse resources, check booking flow

## T-15 Min Demo Checklist
- [ ] Open demo_user session in Chrome (incognito)
- [ ] Open demo_owner session in Firefox
- [ ] Open admin session in Safari / Edge
- [ ] Pre-navigate: user to `/resources`, owner to `/dashboard`, admin to `/admin`
- [ ] WebSocket connected (check browser console — no WS errors)
- [ ] Condition photos pre-uploaded (6 before + 6 after) — URLs noted
- [ ] Contract pre-generated — PDF link working

## Known Risks + Mitigations
| Risk | Signal | Mitigation |
|------|--------|------------|
| Supabase paused | 500 on any DB call | UptimeRobot; restart from Supabase dashboard |
| Gemini rate limit (15 RPM) | 429 response | Pre-cached result served from Redis |
| Railway cold start | First request takes 8–10s | Hit /docs 5 min before demo |
| WebSocket drops | Toast "Reconnecting..." visible | `ws.ts` auto-reconnect fires in < 5s |
| Contract PDF slow | > 10s on first generation | Pre-generated in `precache_demo.py` |
