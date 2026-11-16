# API Routes

Base URL prefix: `/api`.

## Implemented starter routes
| Method | Route | Description |
|---|---|---|
| GET | /health | API health check |
| POST | /auth/login | Authenticate email/password and create session |
| GET | /auth/me | Return current authenticated user |
| POST | /auth/logout | End current session |

## Planned feature routes
- `/admin/users`, `/admin/departments`, `/admin/programmes`, `/admin/reports`
- `/faculty/classes`, `/faculty/attendance/sessions`, `/faculty/assessments`, `/faculty/assignments`
- `/attendance/sessions/:id/check-in`, `/attendance/student/:id`
- `/student/dashboard`, `/student/results`, `/student/transcripts`
- `/ptm/requests`, `/ptm/meetings`, `/feedback/faculty`, `/analytics/early-warning`
- `/transcripts/:verification_code/verify`

All feature routes must enforce authentication, role permissions and record ownership on the server. Transcript verification should return only the minimum public verification fields.
