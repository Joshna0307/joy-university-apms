# Backend security and academic data model

## Roles
Supported roles are `admin`, `faculty`, and `student`. Protect non-public API routes with `roles_required(...)` from `app.authz`. Authentication alone is not sufficient: faculty routes must verify course assignment, and student routes must scope records to the signed-in student's profile.

## First administrator
From the `backend` directory, configure `DATABASE_URL` and `SECRET_KEY`, install requirements, then run:

```powershell
python -m scripts.create_admin
```

The script prompts for the email, name, and password. It accepts only an official `@joyuniversity.edu.in` email and never stores a password in source code. Do not commit `.env` files or production credentials.

## Data model
SQLAlchemy models cover departments, students, faculty, courses, semesters, enrollments, QR attendance sessions and check-ins, assessments and marks, assignments and submissions, PTM meetings, faculty feedback, remediation actions, and transcript verification codes.

## Implementation safeguards
- Generate QR tokens using a cryptographically secure random generator; store only a hash and check expiry plus open state.
- A database uniqueness constraint prevents duplicate attendance for the same student/session.
- Calculate attendance percentage from enrolled sessions and present records; flag below 75%.
- Flag academic performance below 50% only after a valid assessment score exists.
- Anonymous feedback must not expose student identity in faculty-facing responses.
- Transcript verification must return minimal public data and reject revoked codes.
- These models are a foundation. Use Alembic/Flask-Migrate migrations for production schema changes instead of relying on `create_all()`.
