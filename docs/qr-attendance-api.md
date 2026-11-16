# QR attendance API

All endpoints require a signed-in session cookie.

## Faculty: list assigned courses
`GET /api/attendance/courses`
Returns courses assigned to the signed-in faculty member.

## Faculty: create a QR session
`POST /api/attendance/sessions`

Request:
```json
{"course_id": 12}
```

Response includes `session_id`, a one-time `qr_payload`, and an expiry timestamp five minutes after creation. Render `qr_payload` as a QR code. Do not log or persist the raw token in browser storage.

## Student: list enrolled courses
The same `GET /api/attendance/courses` endpoint returns only the signed-in student's enrolled courses.

## Student: check in
`POST /api/attendance/check-in`

Request:
```json
{"token": "raw-token-read-from-qr"}
```

The API verifies token hash, expiry, active state, and course enrollment. A unique database constraint prevents a second check-in for the same student and session.

## Faculty: live check-in feed
`GET /api/attendance/sessions/{session_id}/feed`

Returns check-in names, register numbers, timestamps, and current session state. Only the faculty member who created the session can view the feed.

## Faculty: close session
`POST /api/attendance/sessions/{session_id}/close`

Closes the QR immediately. Sessions also expire automatically after five minutes.

## Deployment note
The routes are committed but have not yet been exercised against a live Neon database. Existing production databases need a migration for the attendance tables; `db.create_all()` creates missing tables but does not alter existing tables.
