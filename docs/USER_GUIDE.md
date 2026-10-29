# AVAILO — USER GUIDE & RUNBOOK

## Running Locally

### Backend (FastAPI)
```bash
cd backend
.\venv\Scripts\python.exe -m uvicorn app.main:app --port 8000
```
- API Base: `http://localhost:8000`
- Swagger Docs: `http://localhost:8000/docs`
- Health Endpoint: `http://localhost:8000/health`

### Frontend (Next.js 15)
```bash
cd frontend
npm run dev -- -p 3000
```
- Web Application: `http://localhost:3000`

---

## Demo Accounts

Login at `http://localhost:3000/login` with any of the seeded personas:

1. **Borrower / User**:
   - Email: `demo_user@availo.app`
   - Password: `DemoUser@Availo`
   - Capabilities: Browse resources, submit booking requests, upload 6-angle condition photos, sign contracts, and access live chat.

2. **Resource Owner**:
   - Email: `demo_owner@availo.app`
   - Password: `DemoOwner@Availo`
   - Capabilities: Approve or reject booking requests, inspect uploaded check-in/return photos, review damage assessments, and counter-sign agreements.

3. **Administrator**:
   - Email: `demo_admin@availo.app`
   - Password: `DemoAdmin@Availo`
   - Capabilities: View system audit logs, dispute cases, platform-wide trust scores, and manage user roles.

