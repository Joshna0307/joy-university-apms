from flask import Blueprint, jsonify
from flask_login import current_user, login_required
from sqlalchemy import func
from app import db
from app.authz import roles_required
from app.models import (
    User, Student, Faculty, Department, Course, Enrollment,
    AttendanceSession, AttendanceRecord, Assignment, PTMMeeting,
    Assessment, Mark, Remediation
)

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.get("/admin")
@login_required
@roles_required("admin")
def admin_dashboard():
    return jsonify({
        "role": "admin",
        "counts": {
            "students": db.session.query(func.count(Student.id)).scalar() or 0,
            "faculty": db.session.query(func.count(Faculty.id)).scalar() or 0,
            "departments": db.session.query(func.count(Department.id)).scalar() or 0,
            "courses": db.session.query(func.count(Course.id)).scalar() or 0,
            "open_remediations": db.session.query(func.count(Remediation.id)).filter(Remediation.status == "Open").scalar() or 0,
            "pending_ptm": db.session.query(func.count(PTMMeeting.id)).filter(PTMMeeting.status == "Requested").scalar() or 0,
            "pending_registrations": db.session.query(func.count(User.id)).filter(User.role == "student", User.active.is_(False)).scalar() or 0,
        }
    })


@dashboard_bp.get("/faculty")
@login_required
@roles_required("faculty")
def faculty_dashboard():
    profile = Faculty.query.filter_by(user_id=current_user.id).first()
    if profile is None:
        return jsonify({"error": "Faculty profile has not been created"}), 404

    course_ids = db.session.query(Enrollment.course_id).filter(Enrollment.faculty_id == profile.id).distinct()
    student_count = db.session.query(func.count(func.distinct(Enrollment.student_id))).filter(
        Enrollment.faculty_id == profile.id
    ).scalar() or 0
    pending_ptm = PTMMeeting.query.filter_by(faculty_id=profile.id, status="Requested").count()
    return jsonify({
        "role": "faculty",
        "faculty": {"employee_number": profile.employee_number},
        "counts": {
            "assigned_courses": course_ids.count(),
            "students": student_count,
            "pending_ptm": pending_ptm,
        }
    })


@dashboard_bp.get("/student")
@login_required
@roles_required("student")
def student_dashboard():
    profile = Student.query.filter_by(user_id=current_user.id).first()
    if profile is None:
        return jsonify({"error": "Student profile has not been created"}), 404

    enrolled_course_ids = db.session.query(Enrollment.course_id).filter(Enrollment.student_id == profile.id)
    total_sessions = AttendanceSession.query.filter(
        AttendanceSession.course_id.in_(enrolled_course_ids)
    ).count()
    attended_sessions = db.session.query(func.count(func.distinct(AttendanceRecord.session_id))).filter(
        AttendanceRecord.student_id == profile.id
    ).scalar() or 0
    attendance_percent = round((attended_sessions / total_sessions) * 100, 1) if total_sessions else None

    assignment_count = Assignment.query.filter(
        Assignment.course_id.in_(enrolled_course_ids)
    ).count()
    marks_count = Mark.query.filter_by(student_id=profile.id).count()
    return jsonify({
        "role": "student",
        "student": {
            "register_number": profile.register_number,
            "semester": profile.semester,
            "batch": profile.batch,
        },
        "counts": {
            "enrolled_courses": enrolled_course_ids.count(),
            "assignments": assignment_count,
            "recorded_marks": marks_count,
        },
        "attendance_percentage": attendance_percent,
        "attendance_alert": attendance_percent is not None and attendance_percent < 75,
    })
