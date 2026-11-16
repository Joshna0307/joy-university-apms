import secrets
from datetime import datetime
from decimal import Decimal, InvalidOperation

from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required
from sqlalchemy.exc import IntegrityError

from app import db
from app.authz import roles_required
from app.models import (
    Assignment, AssignmentSubmission, Assessment, Course, Enrollment,
    Faculty, FacultyFeedback, Mark, PTMMeeting, Semester, Student, TranscriptVerification, User
)

academics_bp = Blueprint("academics", __name__)


def _profiles():
    student = Student.query.filter_by(user_id=current_user.id).first() if current_user.role == "student" else None
    faculty = Faculty.query.filter_by(user_id=current_user.id).first() if current_user.role == "faculty" else None
    return student, faculty


def _faculty_owns_course(faculty_id, course_id):
    return Enrollment.query.filter_by(faculty_id=faculty_id, course_id=course_id).first() is not None


@academics_bp.get("/assignments")
@login_required
@roles_required("admin", "faculty", "student")
def list_assignments():
    query = Assignment.query
    if current_user.role == "faculty":
        profile = Faculty.query.filter_by(user_id=current_user.id).first()
        if not profile:
            return jsonify({"error": "Faculty profile has not been created"}), 404
        query = query.filter_by(faculty_id=profile.id)
    elif current_user.role == "student":
        profile = Student.query.filter_by(user_id=current_user.id).first()
        if not profile:
            return jsonify({"error": "Student profile has not been created"}), 404
        course_ids = db.session.query(Enrollment.course_id).filter_by(student_id=profile.id)
        query = query.filter(Assignment.course_id.in_(course_ids))
    rows = query.order_by(Assignment.due_at.asc()).all()
    return jsonify({"assignments": [{
        "id": x.id, "course_id": x.course_id, "course": db.session.get(Course, x.course_id).code,
        "title": x.title, "instructions": x.instructions, "due_at": x.due_at.isoformat() + "Z",
        "faculty_id": x.faculty_id,
    } for x in rows]})


@academics_bp.post("/assignments")
@login_required
@roles_required("faculty")
def create_assignment():
    profile = Faculty.query.filter_by(user_id=current_user.id).first()
    if not profile:
        return jsonify({"error": "Faculty profile has not been created"}), 404
    data = request.get_json(silent=True) or {}
    try:
        course_id = int(data.get("course_id"))
        title = str(data.get("title") or "").strip()
        due_at = datetime.fromisoformat(str(data.get("due_at") or "").replace("Z", "+00:00")).replace(tzinfo=None)
        if not title:
            raise ValueError
    except (TypeError, ValueError):
        return jsonify({"error": "Provide a valid course, title and due date"}), 400
    if not _faculty_owns_course(profile.id, course_id):
        return jsonify({"error": "You are not assigned to this course"}), 403
    row = Assignment(course_id=course_id, faculty_id=profile.id, title=title, instructions=(data.get("instructions") or "").strip(), due_at=due_at)
    db.session.add(row)
    db.session.commit()
    return jsonify({"assignment_id": row.id, "message": "Assignment created"}), 201


@academics_bp.get("/assignments/<int:assignment_id>/submissions")
@login_required
@roles_required("faculty")
def assignment_submissions(assignment_id):
    faculty = Faculty.query.filter_by(user_id=current_user.id).first()
    assignment = db.session.get(Assignment, assignment_id)
    if not faculty or not assignment or assignment.faculty_id != faculty.id:
        return jsonify({"error": "Assignment not found"}), 404
    rows = (
        db.session.query(AssignmentSubmission, Student, User)
        .join(Student, Student.id == AssignmentSubmission.student_id)
        .join(User, User.id == Student.user_id)
        .filter(AssignmentSubmission.assignment_id == assignment.id)
        .order_by(AssignmentSubmission.submitted_at.desc())
        .all()
    )
    return jsonify({"submissions": [{
        "student": user.name, "register_number": student.register_number,
        "file_url": submission.file_url,
        "submitted_at": submission.submitted_at.isoformat() + "Z",
        "score": float(submission.score) if submission.score is not None else None,
        "feedback": submission.feedback,
    } for submission, student, user in rows]})


@academics_bp.post("/assignments/<int:assignment_id>/submit")
@login_required
@roles_required("student")
def submit_assignment(assignment_id):
    student = Student.query.filter_by(user_id=current_user.id).first()
    if not student:
        return jsonify({"error": "Student profile has not been created"}), 404
    assignment = db.session.get(Assignment, assignment_id)
    if not assignment:
        return jsonify({"error": "Assignment not found"}), 404
    enrolled = Enrollment.query.filter_by(student_id=student.id, course_id=assignment.course_id).first()
    if not enrolled:
        return jsonify({"error": "You are not enrolled in this course"}), 403
    data = request.get_json(silent=True) or {}
    file_url = str(data.get("file_url") or "").strip()
    if not file_url or len(file_url) > 2000:
        return jsonify({"error": "Provide a valid submission link"}), 400
    row = AssignmentSubmission.query.filter_by(assignment_id=assignment.id, student_id=student.id).first()
    if row is None:
        row = AssignmentSubmission(assignment_id=assignment.id, student_id=student.id, file_url=file_url)
        db.session.add(row)
    else:
        row.file_url = file_url
        row.submitted_at = datetime.utcnow()
    db.session.commit()
    return jsonify({"message": "Assignment submission saved", "submitted_at": row.submitted_at.isoformat() + "Z"}), 201


@academics_bp.get("/assessments")
@login_required
@roles_required("admin", "faculty", "student")
def list_assessments():
    query = Assessment.query
    student = Student.query.filter_by(user_id=current_user.id).first() if current_user.role == "student" else None
    faculty = Faculty.query.filter_by(user_id=current_user.id).first() if current_user.role == "faculty" else None
    if student:
        course_ids = db.session.query(Enrollment.course_id).filter_by(student_id=student.id)
        query = query.filter(Assessment.course_id.in_(course_ids))
    elif faculty:
        course_ids = db.session.query(Enrollment.course_id).filter_by(faculty_id=faculty.id)
        query = query.filter(Assessment.course_id.in_(course_ids))
    rows = query.order_by(Assessment.id.desc()).all()
    result = []
    for item in rows:
        mark = Mark.query.filter_by(assessment_id=item.id, student_id=student.id).first() if student else None
        result.append({
            "id": item.id, "course_id": item.course_id, "course": db.session.get(Course, item.course_id).code,
            "semester_id": item.semester_id, "title": item.title, "assessment_type": item.assessment_type,
            "max_marks": float(item.max_marks), "score": float(mark.score) if mark else None,
        })
    return jsonify({"assessments": result})


@academics_bp.post("/assessments")
@login_required
@roles_required("faculty")
def create_assessment():
    faculty = Faculty.query.filter_by(user_id=current_user.id).first()
    if not faculty:
        return jsonify({"error": "Faculty profile has not been created"}), 404
    data = request.get_json(silent=True) or {}
    try:
        course_id = int(data.get("course_id"))
        semester_id = int(data.get("semester_id"))
        title = str(data.get("title") or "").strip()
        assessment_type = str(data.get("assessment_type") or "internal").strip().lower()
        maximum = Decimal(str(data.get("max_marks")))
        if not title or not maximum.is_finite() or maximum <= 0:
            raise ValueError
    except (TypeError, ValueError, InvalidOperation):
        return jsonify({"error": "Enter a valid course, semester, title and maximum marks"}), 400
    if not _faculty_owns_course(faculty.id, course_id):
        return jsonify({"error": "You are not assigned to this course"}), 403
    if db.session.get(Semester, semester_id) is None:
        return jsonify({"error": "Selected semester was not found"}), 404
    row = Assessment(course_id=course_id, semester_id=semester_id, title=title, assessment_type=assessment_type, max_marks=maximum)
    db.session.add(row)
    db.session.commit()
    return jsonify({"assessment_id": row.id, "message": "Assessment created"}), 201


@academics_bp.get("/assessments/<int:assessment_id>/students")
@login_required
@roles_required("faculty")
def assessment_students(assessment_id):
    faculty = Faculty.query.filter_by(user_id=current_user.id).first()
    assessment = db.session.get(Assessment, assessment_id)
    if not faculty or not assessment or not _faculty_owns_course(faculty.id, assessment.course_id):
        return jsonify({"error": "Assessment not found or course not assigned"}), 404
    rows = (
        db.session.query(Student, User, Mark)
        .join(User, User.id == Student.user_id)
        .join(Enrollment, Enrollment.student_id == Student.id)
        .outerjoin(Mark, (Mark.student_id == Student.id) & (Mark.assessment_id == assessment.id))
        .filter(Enrollment.course_id == assessment.course_id, Enrollment.semester_id == assessment.semester_id)
        .order_by(Student.register_number)
        .all()
    )
    return jsonify({"students": [{
        "id": student.id, "name": user.name, "register_number": student.register_number,
        "score": float(mark.score) if mark else None,
    } for student, user, mark in rows]})


@academics_bp.post("/assessments/<int:assessment_id>/marks")
@login_required
@roles_required("faculty")
def save_mark(assessment_id):
    faculty = Faculty.query.filter_by(user_id=current_user.id).first()
    assessment = db.session.get(Assessment, assessment_id)
    if not faculty or not assessment:
        return jsonify({"error": "Faculty or assessment record not found"}), 404
    if not _faculty_owns_course(faculty.id, assessment.course_id):
        return jsonify({"error": "You are not assigned to this course"}), 403
    data = request.get_json(silent=True) or {}
    try:
        student_id = int(data.get("student_id"))
        score = Decimal(str(data.get("score")))
        if not score.is_finite() or score < 0 or score > assessment.max_marks:
            raise ValueError
    except (TypeError, ValueError, InvalidOperation):
        return jsonify({"error": "Enter a valid student and score within the maximum marks"}), 400
    enrolled = Enrollment.query.filter_by(student_id=student_id, course_id=assessment.course_id).first()
    if not enrolled:
        return jsonify({"error": "Student is not enrolled in this course"}), 403
    row = Mark.query.filter_by(assessment_id=assessment.id, student_id=student_id).first()
    if row is None:
        row = Mark(assessment_id=assessment.id, student_id=student_id, score=score)
        db.session.add(row)
    else:
        row.score = score
    db.session.commit()
    return jsonify({"message": "Mark saved"})


@academics_bp.get("/faculty-directory")
@login_required
@roles_required("student")
def faculty_directory():
    student = Student.query.filter_by(user_id=current_user.id).first()
    if not student:
        return jsonify({"error": "Student profile has not been created"}), 404
    faculty_ids = db.session.query(Enrollment.faculty_id).filter(
        Enrollment.student_id == student.id, Enrollment.faculty_id.isnot(None)
    ).distinct()
    rows = Faculty.query.filter(Faculty.id.in_(faculty_ids)).order_by(Faculty.employee_number).all()
    return jsonify({"faculty": [{"id": x.id, "name": x.user.name, "employee_number": x.employee_number} for x in rows]})


@academics_bp.get("/ptm")
@login_required
@roles_required("admin", "faculty", "student")
def list_ptm():
    query = PTMMeeting.query
    student, faculty = _profiles()
    if student:
        query = query.filter_by(student_id=student.id)
    elif faculty:
        query = query.filter_by(faculty_id=faculty.id)
    rows = query.order_by(PTMMeeting.created_at.desc()).all()
    result = []
    for row in rows:
        student_profile = db.session.get(Student, row.student_id)
        faculty_profile = db.session.get(Faculty, row.faculty_id)
        result.append({
            "id": row.id, "student": student_profile.user.name if student_profile else "Student",
            "register_number": student_profile.register_number if student_profile else "",
            "faculty": faculty_profile.user.name if faculty_profile else "Faculty",
            "mode": row.mode, "scheduled_at": row.scheduled_at.isoformat() + "Z" if row.scheduled_at else None,
            "status": row.status, "meeting_minutes": row.meeting_minutes,
        })
    return jsonify({"meetings": result})


@academics_bp.post("/ptm")
@login_required
@roles_required("student")
def request_ptm():
    student = Student.query.filter_by(user_id=current_user.id).first()
    if not student:
        return jsonify({"error": "Student profile has not been created"}), 404
    data = request.get_json(silent=True) or {}
    try:
        faculty_id = int(data.get("faculty_id"))
        mode = str(data.get("mode") or "in_person").lower()
        if mode not in ("in_person", "virtual"):
            raise ValueError
    except (TypeError, ValueError):
        return jsonify({"error": "Choose a valid faculty member and meeting mode"}), 400
    faculty = db.session.get(Faculty, faculty_id)
    if not faculty:
        return jsonify({"error": "Faculty member not found"}), 404
    related = Enrollment.query.filter_by(student_id=student.id, faculty_id=faculty.id).first()
    if not related:
        return jsonify({"error": "You can request a meeting with faculty assigned to your courses"}), 403
    row = PTMMeeting(student_id=student.id, faculty_id=faculty.id, requested_by_user_id=current_user.id, mode=mode)
    db.session.add(row)
    db.session.commit()
    return jsonify({"meeting_id": row.id, "status": row.status, "message": "PTM request submitted"}), 201


@academics_bp.patch("/ptm/<int:meeting_id>")
@login_required
@roles_required("faculty")
def update_ptm(meeting_id):
    faculty = Faculty.query.filter_by(user_id=current_user.id).first()
    row = db.session.get(PTMMeeting, meeting_id)
    if not faculty or not row or row.faculty_id != faculty.id:
        return jsonify({"error": "Meeting not found"}), 404
    data = request.get_json(silent=True) or {}
    status = data.get("status")
    if status not in ("Scheduled", "Completed", "Cancelled"):
        return jsonify({"error": "Status must be Scheduled, Completed or Cancelled"}), 400
    if status == "Scheduled":
        try:
            row.scheduled_at = datetime.fromisoformat(str(data.get("scheduled_at") or "").replace("Z", "+00:00")).replace(tzinfo=None)
        except ValueError:
            return jsonify({"error": "A valid meeting date and time is required"}), 400
    if "meeting_minutes" in data:
        row.meeting_minutes = str(data.get("meeting_minutes") or "").strip()[:10000]
    row.status = status
    db.session.commit()
    return jsonify({"message": "PTM updated", "status": row.status})


@academics_bp.post("/feedback")
@login_required
@roles_required("student")
def submit_feedback():
    student = Student.query.filter_by(user_id=current_user.id).first()
    if not student:
        return jsonify({"error": "Student profile has not been created"}), 404
    data = request.get_json(silent=True) or {}
    try:
        faculty_id = int(data.get("faculty_id"))
        fields = ["teaching_clarity", "punctuality_coverage", "doubt_resolution", "practical_guidance", "course_materials"]
        ratings = {key: int(data.get(key)) for key in fields}
        if any(value < 1 or value > 5 for value in ratings.values()):
            raise ValueError
    except (TypeError, ValueError):
        return jsonify({"error": "Choose a faculty member and rate all five areas from 1 to 5"}), 400
    faculty = db.session.get(Faculty, faculty_id)
    if not faculty or not Enrollment.query.filter_by(student_id=student.id, faculty_id=faculty.id).first():
        return jsonify({"error": "Feedback is available only for faculty teaching your courses"}), 403
    anonymous = bool(data.get("is_anonymous"))
    row = FacultyFeedback(student_id=None if anonymous else student.id, faculty_id=faculty.id, **ratings, comments=str(data.get("comments") or "").strip()[:3000], is_anonymous=anonymous)
    db.session.add(row)
    db.session.commit()
    return jsonify({"message": "Thank you. Your feedback was submitted."}), 201


@academics_bp.get("/transcript")
@login_required
@roles_required("admin", "student")
def transcript():
    student_id = request.args.get("student_id", type=int)
    if current_user.role == "student":
        profile = Student.query.filter_by(user_id=current_user.id).first()
    else:
        profile = db.session.get(Student, student_id) if student_id else None
    if not profile:
        return jsonify({"error": "Student profile not found"}), 404
    verification = TranscriptVerification.query.filter_by(student_id=profile.id, revoked=False).first()
    if verification is None:
        verification = TranscriptVerification(student_id=profile.id, verification_code=secrets.token_urlsafe(24))
        db.session.add(verification)
        db.session.commit()
    enrollments = Enrollment.query.filter_by(student_id=profile.id).all()
    course_rows = []
    total_points = 0.0
    total_credits = 0.0
    for enrollment in enrollments:
        course = db.session.get(Course, enrollment.course_id)
        marks = db.session.query(Mark, Assessment).join(Assessment, Assessment.id == Mark.assessment_id).filter(Mark.student_id == profile.id, Assessment.course_id == enrollment.course_id).all()
        earned = sum(float(mark.score) for mark, _ in marks)
        maximum = sum(float(assessment.max_marks) for _, assessment in marks)
        percentage = round((earned / maximum) * 100, 2) if maximum else None
        credits = float(course.credits) if course else 0
        grade_point = min(10, percentage / 10) if percentage is not None else None
        if grade_point is not None:
            total_points += grade_point * credits
            total_credits += credits
        course_rows.append({"course_code": course.code if course else "", "course_title": course.title if course else "", "credits": credits, "earned_marks": earned, "maximum_marks": maximum, "percentage": percentage, "grade_point_estimate": round(grade_point, 2) if grade_point is not None else None})
    return jsonify({
        "student": {"name": profile.user.name, "email": profile.user.email, "register_number": profile.register_number, "batch": profile.batch, "semester": profile.semester},
        "courses": course_rows,
        "cgpa_estimate": round(total_points / total_credits, 2) if total_credits else None,
        "verification_code": verification.verification_code,
        "verification_path": f"/api/academics/transcript/verify/{verification.verification_code}",
        "notice": "Grade point and CGPA are estimates based on recorded marks; the university's approved grading rules remain authoritative.",
    })


@academics_bp.get("/transcript/verify/<string:code>")
def verify_transcript(code):
    row = TranscriptVerification.query.filter_by(verification_code=code, revoked=False).first()
    if not row:
        return jsonify({"valid": False, "message": "Transcript code is invalid or revoked"}), 404
    student = db.session.get(Student, row.student_id)
    if not student:
        return jsonify({"valid": False, "message": "Student record not found"}), 404
    return jsonify({"valid": True, "student_name": student.user.name, "register_number": student.register_number, "issued_at": row.issued_at.isoformat() + "Z"})
