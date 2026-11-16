# Database Design

The first backend version provides a `users` table. Introduce the remaining tables through versioned migrations as each feature is implemented.

| Table | Purpose |
|---|---|
| users | Login identity, role and account status |
| departments / programmes | Academic organization |
| students / faculty | Student and staff profiles |
| semesters / subjects | Term, course and credit catalog |
| course_offerings | Subject taught by faculty in a term/section |
| enrollments | Student registration in offerings |
| attendance_sessions | QR session, token hash and expiry |
| attendance_records | Student check-in; unique per session/student |
| assessments / marks | IA, assignment and end-semester evaluation |
| assignments / submissions | Assignment lifecycle |
| ptm_meetings | PTM mode, status and meeting minutes |
| faculty_evaluations | Dimension ratings and anonymity flag |
| remediation_plans | Follow-up for early-warning students |
| transcript_verifications | Random public verification identifier |
| audit_logs | Important administrative actions |

## Constraints
Use unique email and register/staff identifiers, foreign keys, role ownership checks and indexes on student/course/semester/timestamp fields. Store timestamps in UTC and render in the university timezone. Public transcript verification must not disclose private student information.
