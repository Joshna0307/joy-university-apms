# APMS College Demo Guide

## Status and honesty
This repository contains selected working workflows and an academic portal foundation. It has not been build-tested or end-to-end tested in this environment, and no public production URL has been verified. Use a local test database and synthetic data for the college demonstration. Do not present unverified features as production-ready.

## What to demonstrate
1. Role-based sign-in for Admin, Faculty and Student.
2. Admin creates and lists departments, courses, student accounts and faculty accounts.
3. Faculty generates a five-minute QR for an assigned course.
4. Student scans the QR and checks in; the backend rejects duplicate check-ins.
5. Faculty sees the live check-in feed refresh automatically.
6. Academic workspace includes assignment, assessment, PTM, feedback and transcript prototype screens. Treat them as prototype/under-test until individually verified.

## Prepare a local demo on Windows

### 1. Clone and start the backend
```powershell
git clone https://github.com/Joshna0307/joy-university-apms.git
cd joy-university-apms
cd backend
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```
Edit `.env`: set a long random `SECRET_KEY`. Keep SQLite for a disposable local demo. Never commit `.env`.
Start the API:
```powershell
py run.py
```
Check `http://127.0.0.1:5000/api/health` returns JSON with status `ok`.

### 2. Start the frontend
Open another PowerShell window at the repository root:
```powershell
cd frontend
npm install
Copy-Item .env.example .env
npm run dev
```
Open the Vite URL printed in the terminal (usually `http://localhost:5173`).

### 3. Create synthetic demo records
1. In a third terminal, from the `backend` folder, run `py -m scripts.create_admin` and create an administrator using an official-format test email and a strong password. Keep the password private.
2. Sign in as Admin in the browser.
3. Create a department and one course.
4. Create one Faculty account and one Student account with synthetic names and test emails.
5. From the `backend` folder run `py -m scripts.link_demo_class`. Enter the faculty email, student email, course code, academic year and semester number. This links both accounts to the course so QR attendance can be tested.
6. Sign out and sign in as Faculty. Confirm the course appears in the QR Attendance course selector.

### 4. Demonstrate QR attendance
1. Keep Faculty signed in on the laptop and select the demo course.
2. Click **Generate 5-minute QR**.
3. On a second device or separate browser profile, sign in as Student.
4. Allow camera access and scan the QR shown on the laptop. Camera access requires a secure context; local browser support can vary. A deployed HTTPS site is best for a reliable camera demo.
5. Confirm the Student success message.
6. Return to the Faculty page and show the live check-in list updating.
7. Try scanning the same QR again and show the duplicate check-in rejection.
8. Close the QR session.

Use two devices or separate browser profiles; one browser session cannot conveniently stay signed in as both roles at once.

## Suggested 7-minute presentation
- 0:00–0:45 — Problem: academic information and attendance are scattered across processes.
- 0:45–1:30 — Proposed solution: a role-based academic monitoring portal.
- 1:30–2:30 — Admin creates department, course and synthetic test accounts.
- 2:30–4:45 — Faculty creates a time-limited QR; Student scans; Faculty sees the live check-in.
- 4:45–5:30 — Briefly introduce assignment, assessment, PTM, feedback and transcript prototype screens.
- 5:30–6:30 — Architecture: React frontend, Flask API, SQLAlchemy models, SQLite locally and Neon PostgreSQL intended for deployment.
- 6:30–7:00 — Explain remaining work: automated tests, production migrations, verified deployment, security review and university-approved academic rules.

## Demo-day checklist
- Charge laptop and phone; bring the charger.
- Test the app before class and keep both terminals running.
- Use only synthetic data.
- Keep demo credentials private.
- Take screenshots as backup in case of Wi-Fi or camera-permission problems.
- Do not claim the public website is deployed until frontend and backend production URLs and the backend health endpoint are verified.

## Repository
https://github.com/Joshna0307/joy-university-apms
