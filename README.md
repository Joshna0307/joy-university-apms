# Joy University — Academic Progress Monitoring System (APMS)

A role-based academic portal foundation for Joy University, built with React, Flask and PostgreSQL.

## Technology
- Frontend: React 18, Vite, Tailwind CSS, Lucide React
- Backend: Python Flask, Flask-Login, Flask-SQLAlchemy
- Database: Neon PostgreSQL for deployment; SQLite for local development
- Frontend hosting: Vercel
- Backend hosting: Render or another Python-compatible host

**Hosting note:** Vercel deploys the React frontend. The Flask API must be deployed separately. The frontend uses `VITE_API_BASE_URL` to reach the backend.

## Current implementation status
- Role-aware sign-in shell for Admin, Faculty and Student.
- Flask authentication and role-protected API foundation.
- Academic database models for students, faculty, courses, semesters, enrollments, attendance, assessments, assignments, PTM, feedback, remediation and transcript verification.
- Role-specific dashboard summary API.
- QR attendance: faculty creates a five-minute course QR; students scan and check in; backend checks enrollment, expiry and duplicate attendance; faculty dashboard shows a live check-in list that refreshes every three seconds.
- Deployment configuration templates for Vercel and Render.

**Not yet complete:** full admin CRUD screens, marks and assignment workflows, PTM screens, feedback workflows, transcript PDF/QR verification, early-warning management, production database migrations and end-to-end tests. Do not use this starter as a production university records system until these are completed and reviewed.

## Local setup (Windows PowerShell)

### 1. Backend
```powershell
cd backend
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
py run.py
```
The API runs at `http://127.0.0.1:5000`.

### 2. Frontend (open a second terminal)
```powershell
cd frontend
npm install
Copy-Item .env.example .env
npm run dev
```
Open the Vite URL shown in the terminal, usually `http://localhost:5173`.

## Deployment overview

### Neon PostgreSQL
1. Create a Neon project and database.
2. Copy the pooled connection string from Neon.
3. Add it to the backend host as `DATABASE_URL`; never put it in the frontend or commit it to GitHub.
4. Run the project's database migrations before using production data. `db.create_all()` creates missing tables but does not safely migrate existing tables.

### Render backend
1. Create a new **Web Service** from this GitHub repository.
2. Set **Root Directory** to `backend`.
3. Build command: `pip install -r requirements.txt`.
4. Start command: `gunicorn run:app`.
5. Set environment variables: `DATABASE_URL`, `SECRET_KEY` (a long random secret), `FLASK_ENV=production`, and `FRONTEND_ORIGIN` (your Vercel URL).
6. Deploy and confirm `https://YOUR-BACKEND-URL/api/health` returns healthy.

### Vercel frontend
1. Import this repository into Vercel.
2. Set **Root Directory** to `frontend`.
3. Build command: `npm run build`; output directory: `dist`.
4. Add `VITE_API_BASE_URL=https://YOUR-BACKEND-URL/api`.
5. Deploy, then update backend `FRONTEND_ORIGIN` with the Vercel production URL.

The camera scanner requires HTTPS and browser camera permission.

## Initial administrator
Use the secure bootstrap script from the backend environment after the database is configured:
```powershell
py -m scripts.create_admin
```
It prompts for the official university email, name and a strong password. Do not commit credentials or share the password in chat.

## Important production checks
- Configure CORS for the exact frontend origin and secure session cookies.
- Run reviewed database migrations; do not rely on `create_all()` for schema changes.
- Verify authentication, role permissions, record ownership, backups and audit requirements.
- Test all workflows with synthetic data before importing real student records.
- Confirm university-approved attendance thresholds, grading rules and transcript formats.

## Documentation
- [Architecture](docs/architecture.md)
- [Database design](docs/database-design.md)
- [API documentation](docs/api-documentation.md)
- [Security and data model](docs/security-and-data-model.md)
- [QR attendance API](docs/qr-attendance-api.md)
