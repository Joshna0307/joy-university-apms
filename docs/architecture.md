# APMS Architecture

## Overview
Joy University APMS connects a React role-aware web portal to a Flask REST API and Neon PostgreSQL database.

## Layers
1. React SPA: responsive Admin, Faculty and Student workspaces.
2. Flask API: session authentication, validation, authorization and business logic.
3. SQLAlchemy: database access and schema management.
4. Neon PostgreSQL: persistent production records; SQLite is available for local development.

## Roles
- Admin: institutional setup, users, courses, reporting and oversight.
- Faculty: assigned classes only; attendance, assessments, assignments, PTM and feedback.
- Student: own attendance, results, assignments, PTM requests, feedback and transcripts.

## Planned modules
- Academic setup: departments, programmes, semesters, subjects, offerings and enrollments.
- QR attendance: faculty creates a five-minute time-limited QR session; student scans using camera permission or enters a one-time token; reject duplicate check-ins; alert below 75% attendance.
- Assessments: IA-1, IA-2, assignments and end-semester marks.
- Progress analytics: attendance, SGPA/CGPA and trends, using university-approved grading rules.
- PTM: in-person/virtual requests, Requested/Scheduled/Completed status and meeting minutes.
- Feedback: five dimensions—teaching clarity, punctuality/syllabus coverage, doubt resolution/mentorship, practical/lab guidance, and notes/materials—with optional anonymity.
- Early warning: attendance below 75% or scores below 50% trigger a review and remediation workflow.
- Transcript: printable semester breakdown with QR verification identifier.

## Deployment
Deploy frontend to Vercel. Deploy Flask API separately on a Python-compatible host. Set frontend `VITE_API_BASE_URL` to the deployed API URL. Set `DATABASE_URL`, `SECRET_KEY` and `FRONTEND_ORIGIN` as backend-host environment variables. Never expose Neon credentials in browser code.
