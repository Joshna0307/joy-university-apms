# Joy University — Academic Progress Monitoring System (APMS)

A role-based academic portal for Joy University to manage student records, attendance, assessments, faculty workflows, parent–teacher meetings, feedback and academic progress analytics.

## Technology
- Frontend: React, Vite, Tailwind CSS, Lucide React
- Backend: Python Flask, Flask-Login, Flask-SQLAlchemy
- Database: Neon PostgreSQL (SQLite for local development)
- Frontend hosting: Vercel
- Backend hosting: a Python-compatible host (such as Render or Railway)

> Vercel hosts the React frontend. Deploy the Flask API separately and set `VITE_API_BASE_URL` to its public URL. Keep database credentials only in backend environment variables.

## Local setup (Windows PowerShell)

### Backend
```powershell
cd backend
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
py run.py
```
API: `http://127.0.0.1:5000`

### Frontend (open a second terminal)
```powershell
cd frontend
npm install
Copy-Item .env.example .env
npm run dev
```
Open the Vite URL printed in the terminal (usually `http://localhost:5173`).

## Roles
- **Admin:** institutional setup, users, academic oversight and analytics.
- **Faculty:** assigned classes, attendance, marks, assignments, PTM and feedback.
- **Student:** personal dashboard, attendance, marks, SGPA/CGPA, assignments, PTM and transcripts.

## Current implementation
The first commit establishes the React role-aware starter interface, Flask health endpoint, session login endpoints, and user model. QR attendance, academic records, PTM, feedback, early-warning analytics and QR-verifiable transcripts are described in `docs/` and remain planned implementation stages.

## Environment variables
See `backend/.env.example` and `frontend/.env.example`. Never commit real passwords, API keys or a Neon connection string. Configure `DATABASE_URL`, `SECRET_KEY` and `FRONTEND_ORIGIN` on the backend hosting provider.

## Security before production
Create the first administrator through a secure setup workflow, enforce role and record ownership checks on every protected route, configure HTTPS and production cookie/CORS settings, and use the university's approved grading and attendance rules.


## QR attendance module

The faculty dashboard can generate a five-minute course QR code. Students can scan it from the student dashboard using their device camera. The API checks session expiry, enrollment, and duplicate submissions. Camera scanning requires HTTPS in deployed environments and the user must grant camera permission.

After pulling the latest changes, install frontend packages with `npm install` inside `frontend`, then run `npm run build` to check the production bundle. The QR attendance API details are in [docs/qr-attendance-api.md](docs/qr-attendance-api.md).
