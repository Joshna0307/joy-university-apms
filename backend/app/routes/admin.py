from decimal import Decimal, InvalidOperation

from flask import Blueprint, jsonify, request
from flask_login import login_required
from sqlalchemy.exc import IntegrityError

from app import db
from app.authz import roles_required
from app.models import (AttendanceRecord, AttendanceSession, Assessment, Course, Department, Enrollment, Faculty, Mark, Remediation, Semester, Student, User)

admin_bp = Blueprint("admin", __name__)


def _required(data, key, label):
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} is required")
    return value.strip()


def _optional_int(value, label):
    if value in (None, ""):
        return None
    try:
        number = int(value)
        if number < 1:
            raise ValueError
        return number
    except (TypeError, ValueError):
        raise ValueError(f"{label} must be a positive whole number")


@admin_bp.get("/departments")
@login_required
@roles_required("admin")
def list_departments():
    rows = Department.query.order_by(Department.name).all()
    return jsonify({"departments": [{"id": x.id, "name": x.name, "code": x.code} for x in rows]})


@admin_bp.post("/departments")
@login_required
@roles_required("admin")
def create_department():
    data = request.get_json(silent=True) or {}
    try:
        row = Department(name=_required(data, "name", "Department name"), code=_required(data, "code", "Department code").upper())
        db.session.add(row)
        db.session.commit()
    except ValueError as error:
        return jsonify({"error": str(error)}), 400
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Department name or code already exists"}), 409
    return jsonify({"department": {"id": row.id, "name": row.name, "code": row.code}}), 201


@admin_bp.get("/courses")
@login_required
@roles_required("admin")
def list_courses():
    rows = Course.query.order_by(Course.code).all()
    return jsonify({"courses": [{"id": x.id, "code": x.code, "title": x.title, "credits": float(x.credits), "department_id": x.department_id} for x in rows]})


@admin_bp.post("/courses")
@login_required
@roles_required("admin")
def create_course():
    data = request.get_json(silent=True) or {}
    try:
        code = _required(data, "code", "Course code").upper()
        title = _required(data, "title", "Course title")
        credits = Decimal(str(data.get("credits", "3")))
        if not credits.is_finite() or credits <= 0 or credits > 30:
            raise ValueError
        department_id = _optional_int(data.get("department_id"), "Department ID")
        if department_id and db.session.get(Department, department_id) is None:
            return jsonify({"error": "Selected department was not found"}), 404
        row = Course(code=code, title=title, credits=credits, department_id=department_id)
        db.session.add(row)
        db.session.commit()
    except (ValueError, InvalidOperation):
        db.session.rollback()
        return jsonify({"error": "Enter a valid course code, title and credits (greater than 0 and at most 30)"}), 400
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Course code already exists"}), 409
    return jsonify({"course": {"id": row.id, "code": row.code, "title": row.title, "credits": float(row.credits), "department_id": row.department_id}}), 201


@admin_bp.get("/students")
@login_required
@roles_required("admin")
def list_students():
    rows = Student.query.order_by(Student.register_number).all()
    return jsonify({"students": [{
        "id": x.id, "name": x.user.name, "email": x.user.email,
        "register_number": x.register_number, "department_id": x.department_id,
        "batch": x.batch, "semester": x.semester,
    } for x in rows]})


@admin_bp.post("/students")
@login_required
@roles_required("admin")
def create_student():
    data = request.get_json(silent=True) or {}
    try:
        name = _required(data, "name", "Student name")
        email = _required(data, "email", "University email").lower()
        password = _required(data, "password", "Initial password")
        register_number = _required(data, "register_number", "Register number").upper()
        if len(password) < 12:
            return jsonify({"error": "Initial password must contain at least 12 characters"}), 400
        department_id = _optional_int(data.get("department_id"), "Department ID")
        semester = _optional_int(data.get("semester"), "Semester")
        if department_id and db.session.get(Department, department_id) is None:
            return jsonify({"error": "Selected department was not found"}), 404
        user = User(name=name, email=email, role="student", active=True)
        user.set_password(password)
        db.session.add(user)
        db.session.flush()
        row = Student(user_id=user.id, register_number=register_number, department_id=department_id, batch=(data.get("batch") or "").strip() or None, semester=semester)
        db.session.add(row)
        db.session.commit()
    except ValueError as error:
        db.session.rollback()
        return jsonify({"error": str(error)}), 400
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Email or register number already exists"}), 409
    return jsonify({"student": {"id": row.id, "name": user.name, "email": user.email, "register_number": row.register_number}}), 201


@admin_bp.get("/faculty")
@login_required
@roles_required("admin")
def list_faculty():
    rows = Faculty.query.order_by(Faculty.employee_number).all()
    return jsonify({"faculty": [{
        "id": x.id, "name": x.user.name, "email": x.user.email,
        "employee_number": x.employee_number, "department_id": x.department_id,
    } for x in rows]})


@admin_bp.post("/faculty")
@login_required
@roles_required("admin")
def create_faculty():
    data = request.get_json(silent=True) or {}
    try:
        name = _required(data, "name", "Faculty name")
        email = _required(data, "email", "University email").lower()
        password = _required(data, "password", "Initial password")
        employee_number = _required(data, "employee_number", "Employee number").upper()
        if len(password) < 12:
            return jsonify({"error": "Initial password must contain at least 12 characters"}), 400
        department_id = _optional_int(data.get("department_id"), "Department ID")
        if department_id and db.session.get(Department, department_id) is None:
            return jsonify({"error": "Selected department was not found"}), 404
        user = User(name=name, email=email, role="faculty", active=True)
        user.set_password(password)
        db.session.add(user)
        db.session.flush()
        row = Faculty(user_id=user.id, employee_number=employee_number, department_id=department_id)
        db.session.add(row)
        db.session.commit()
    except ValueError as error:
        db.session.rollback()
        return jsonify({"error": str(error)}), 400
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Email or employee number already exists"}), 409
    return jsonify({"faculty": {"id": row.id, "name": user.name, "email": user.email, "employee_number": row.employee_number}}), 201


@admin_bp.get("/semesters")
@login_required
@roles_required("admin")
def list_semesters():
    rows = Semester.query.order_by(Semester.academic_year, Semester.number).all()
    return jsonify({"semesters": [{"id": x.id, "name": x.name, "academic_year": x.academic_year, "number": x.number} for x in rows]})


@admin_bp.post("/semesters")
@login_required
@roles_required("admin")
def create_semester():
    data = request.get_json(silent=True) or {}
    try:
        name = _required(data, "name", "Semester name")
        academic_year = _required(data, "academic_year", "Academic year")
        number = int(data.get("number"))
        if number < 1 or number > 12:
            raise ValueError
        row = Semester(name=name, academic_year=academic_year, number=number)
        db.session.add(row)
        db.session.commit()
    except (ValueError, TypeError):
        db.session.rollback()
        return jsonify({"error": "Enter a valid semester name, academic year and semester number (1–12)"}), 400
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Could not create semester"}), 409
    return jsonify({"semester": {"id": row.id, "name": row.name, "academic_year": row.academic_year, "number": row.number}}), 201


@admin_bp.get("/enrollments")
@login_required
@roles_required("admin")
def list_enrollments():
    rows = Enrollment.query.order_by(Enrollment.id.desc()).all()
    result = []
    for row in rows:
        student = db.session.get(Student, row.student_id)
        course = db.session.get(Course, row.course_id)
        semester = db.session.get(Semester, row.semester_id)
        faculty = db.session.get(Faculty, row.faculty_id) if row.faculty_id else None
        result.append({
            "id": row.id,
            "student": student.user.name if student else "Student",
            "register_number": student.register_number if student else "",
            "course": course.code if course else "Course",
            "semester": semester.name if semester else "Semester",
            "faculty": faculty.user.name if faculty else "Not assigned",
        })
    return jsonify({"enrollments": result})


@admin_bp.post("/enrollments")
@login_required
@roles_required("admin")
def create_enrollment():
    data = request.get_json(silent=True) or {}
    try:
        student_id = int(data.get("student_id"))
        course_id = int(data.get("course_id"))
        semester_id = int(data.get("semester_id"))
        faculty_id = _optional_int(data.get("faculty_id"), "Faculty ID")
    except (TypeError, ValueError) as error:
        return jsonify({"error": str(error) or "Select a student, course and semester"}), 400
    student = db.session.get(Student, student_id)
    course = db.session.get(Course, course_id)
    semester = db.session.get(Semester, semester_id)
    faculty = db.session.get(Faculty, faculty_id) if faculty_id else None
    if not student or not course or not semester:
        return jsonify({"error": "Student, course or semester record was not found"}), 404
    if faculty_id and not faculty:
        return jsonify({"error": "Faculty record was not found"}), 404
    row = Enrollment(student_id=student_id, course_id=course_id, semester_id=semester_id, faculty_id=faculty_id)
    db.session.add(row)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "This student is already enrolled in this course for the selected semester"}), 409
    return jsonify({"enrollment_id": row.id, "message": "Student enrollment created"}), 201


@admin_bp.get("/early-warnings")
@login_required
@roles_required("admin")
def early_warnings():
    warnings = []
    students = Student.query.order_by(Student.register_number).all()
    for student in students:
        enrollments = Enrollment.query.filter_by(student_id=student.id).all()
        for enrollment in enrollments:
            course = db.session.get(Course, enrollment.course_id)
            total_sessions = AttendanceSession.query.filter_by(course_id=enrollment.course_id).count()
            attended = (
                db.session.query(AttendanceRecord.id)
                .join(AttendanceSession, AttendanceSession.id == AttendanceRecord.session_id)
                .filter(AttendanceRecord.student_id == student.id, AttendanceSession.course_id == enrollment.course_id)
                .count()
            )
            attendance_pct = round(attended * 100 / total_sessions, 1) if total_sessions else None
            mark_rows = (
                db.session.query(Mark.score, Assessment.max_marks)
                .join(Assessment, Assessment.id == Mark.assessment_id)
                .filter(Mark.student_id == student.id, Assessment.course_id == enrollment.course_id)
                .all()
            )
            total_score = sum(float(x.score) for x in mark_rows)
            total_max = sum(float(x.max_marks) for x in mark_rows)
            academic_pct = round(total_score * 100 / total_max, 1) if total_max else None
            reasons = []
            if attendance_pct is not None and attendance_pct < 75:
                reasons.append("Attendance below 75%")
            if academic_pct is not None and academic_pct < 50:
                reasons.append("Academic score below 50%")
            if reasons:
                warnings.append({
                    "student_id": student.id, "name": student.user.name,
                    "register_number": student.register_number,
                    "course_id": enrollment.course_id, "course": course.code if course else "",
                    "attendance_percentage": attendance_pct, "academic_percentage": academic_pct,
                    "reasons": reasons,
                    "remediation_status": (Remediation.query.filter_by(student_id=student.id, course_id=enrollment.course_id).order_by(Remediation.created_at.desc()).first().status
                        if Remediation.query.filter_by(student_id=student.id, course_id=enrollment.course_id).first() else None),
                })
    return jsonify({"warnings": warnings, "count": len(warnings)})


@admin_bp.get("/remediations")
@login_required
@roles_required("admin")
def list_remediations():
    rows = Remediation.query.order_by(Remediation.created_at.desc()).all()
    return jsonify({"remediations": [{
        "id": x.id, "student_id": x.student_id,
        "student": db.session.get(Student, x.student_id).user.name,
        "course_id": x.course_id,
        "course": db.session.get(Course, x.course_id).code if x.course_id else "General",
        "reason": x.reason, "notes": x.notes, "status": x.status,
    } for x in rows]})


@admin_bp.post("/remediations")
@login_required
@roles_required("admin")
def create_remediation():
    data = request.get_json(silent=True) or {}
    try:
        student_id = int(data.get("student_id"))
        course_id = _optional_int(data.get("course_id"), "Course ID")
        reason = _required(data, "reason", "Reason")
    except (TypeError, ValueError) as error:
        return jsonify({"error": str(error)}), 400
    if not db.session.get(Student, student_id):
        return jsonify({"error": "Student not found"}), 404
    if course_id and not db.session.get(Course, course_id):
        return jsonify({"error": "Course not found"}), 404
    row = Remediation(student_id=student_id, course_id=course_id, reason=reason, notes=str(data.get("notes") or "").strip())
    db.session.add(row)
    db.session.commit()
    return jsonify({"remediation_id": row.id, "message": "Remediation plan created"}), 201


@admin_bp.patch("/remediations/<int:remediation_id>")
@login_required
@roles_required("admin")
def update_remediation(remediation_id):
    row = db.session.get(Remediation, remediation_id)
    if not row:
        return jsonify({"error": "Remediation plan not found"}), 404
    data = request.get_json(silent=True) or {}
    status = data.get("status")
    if status not in ("Open", "In Progress", "Completed"):
        return jsonify({"error": "Status must be Open, In Progress or Completed"}), 400
    row.status = status
    if "notes" in data:
        row.notes = str(data.get("notes") or "").strip()[:10000]
    db.session.commit()
    return jsonify({"message": "Remediation updated", "status": row.status})
