import hashlib
import secrets
from datetime import datetime, timedelta

from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required
from sqlalchemy.exc import IntegrityError

from app import db
from app.authz import roles_required
from app.models import (
    AttendanceRecord, AttendanceSession, Course, Enrollment, Faculty, Student, User
)

attendance_bp = Blueprint("attendance", __name__)
SESSION_MINUTES = 5


def _token_digest(token):
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _faculty_profile():
    return Faculty.query.filter_by(user_id=current_user.id).first()


@attendance_bp.post("/sessions")
@login_required
@roles_required("faculty")
def create_session():
    data = request.get_json(silent=True) or {}
    course_id = data.get("course_id")
    if not isinstance(course_id, int):
        return jsonify({"error": "A valid course_id is required"}), 400

    faculty = _faculty_profile()
    if faculty is None:
        return jsonify({"error": "Faculty profile has not been created"}), 404

    assigned = Enrollment.query.filter_by(
        faculty_id=faculty.id, course_id=course_id
    ).first()
    if assigned is None:
        return jsonify({"error": "You are not assigned to this course"}), 403

    course = db.session.get(Course, course_id)
    if course is None:
        return jsonify({"error": "Course not found"}), 404

    # Close any previous open QR session for this faculty/course.
    now = datetime.utcnow()
    AttendanceSession.query.filter_by(
        faculty_id=faculty.id, course_id=course_id, is_open=True
    ).update({"is_open": False}, synchronize_session=False)

    raw_token = secrets.token_urlsafe(32)
    session = AttendanceSession(
        course_id=course_id,
        faculty_id=faculty.id,
        token_hash=_token_digest(raw_token),
        expires_at=now + timedelta(minutes=SESSION_MINUTES),
        is_open=True,
    )
    db.session.add(session)
    db.session.commit()

    return jsonify({
        "session_id": session.id,
        "course": {"id": course.id, "code": course.code, "title": course.title},
        "qr_payload": raw_token,
        "expires_at": session.expires_at.isoformat() + "Z",
        "duration_seconds": SESSION_MINUTES * 60,
    }), 201


@attendance_bp.post("/check-in")
@login_required
@roles_required("student")
def check_in():
    data = request.get_json(silent=True) or {}
    token = data.get("token")
    if not isinstance(token, str) or not token.strip() or len(token) > 256:
        return jsonify({"error": "A valid QR token is required"}), 400

    student = Student.query.filter_by(user_id=current_user.id).first()
    if student is None:
        return jsonify({"error": "Student profile has not been created"}), 404

    session = AttendanceSession.query.filter_by(
        token_hash=_token_digest(token.strip())
    ).first()
    now = datetime.utcnow()
    if session is None or not session.is_open or session.expires_at <= now:
        return jsonify({"error": "This attendance QR has expired or is no longer active"}), 410

    enrolled = Enrollment.query.filter_by(
        student_id=student.id, course_id=session.course_id
    ).first()
    if enrolled is None:
        return jsonify({"error": "You are not enrolled in this course"}), 403

    record = AttendanceRecord(
        session_id=session.id,
        student_id=student.id,
    )
    db.session.add(record)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Attendance has already been recorded for this QR session"}), 409

    course = db.session.get(Course, session.course_id)
    return jsonify({
        "message": "Attendance recorded successfully",
        "course": course.title if course else "Course",
        "checked_in_at": record.checked_in_at.isoformat() + "Z",
    }), 201


@attendance_bp.get("/sessions/<int:session_id>/feed")
@login_required
@roles_required("faculty")
def session_feed(session_id):
    faculty = _faculty_profile()
    if faculty is None:
        return jsonify({"error": "Faculty profile has not been created"}), 404
    session = db.session.get(AttendanceSession, session_id)
    if session is None or session.faculty_id != faculty.id:
        return jsonify({"error": "Attendance session not found"}), 404

    rows = (
        db.session.query(AttendanceRecord, Student, User)
        .join(Student, Student.id == AttendanceRecord.student_id)
        .join(User, User.id == Student.user_id)
        .filter(AttendanceRecord.session_id == session.id)
        .order_by(AttendanceRecord.checked_in_at.desc())
        .all()
    )
    return jsonify({
        "session_id": session.id,
        "is_open": session.is_open and session.expires_at > datetime.utcnow(),
        "expires_at": session.expires_at.isoformat() + "Z",
        "total_checked_in": len(rows),
        "check_ins": [{
            "name": user.name,
            "register_number": student.register_number,
            "checked_in_at": record.checked_in_at.isoformat() + "Z",
        } for record, student, user in rows],
    })


@attendance_bp.post("/sessions/<int:session_id>/close")
@login_required
@roles_required("faculty")
def close_session(session_id):
    faculty = _faculty_profile()
    if faculty is None:
        return jsonify({"error": "Faculty profile has not been created"}), 404
    session = db.session.get(AttendanceSession, session_id)
    if session is None or session.faculty_id != faculty.id:
        return jsonify({"error": "Attendance session not found"}), 404
    session.is_open = False
    db.session.commit()
    return jsonify({"message": "Attendance QR session closed"})
