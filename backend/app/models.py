from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, login_manager


class TimestampMixin:
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class User(UserMixin, TimestampMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, index=True)
    active = db.Column(db.Boolean, nullable=False, default=True)
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    def to_dict(self):
        return {"id": self.id, "name": self.name, "email": self.email, "role": self.role}


class Department(TimestampMixin, db.Model):
    __tablename__ = "departments"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)
    code = db.Column(db.String(20), unique=True, nullable=False)


class Student(TimestampMixin, db.Model):
    __tablename__ = "students"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), unique=True, nullable=False)
    register_number = db.Column(db.String(40), unique=True, nullable=False, index=True)
    department_id = db.Column(db.Integer, db.ForeignKey("departments.id"), nullable=True)
    batch = db.Column(db.String(20), nullable=True)
    semester = db.Column(db.Integer, nullable=True)
    user = db.relationship("User", backref=db.backref("student_profile", uselist=False))
    department = db.relationship("Department")


class Faculty(TimestampMixin, db.Model):
    __tablename__ = "faculty"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), unique=True, nullable=False)
    employee_number = db.Column(db.String(40), unique=True, nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey("departments.id"), nullable=True)
    user = db.relationship("User", backref=db.backref("faculty_profile", uselist=False))
    department = db.relationship("Department")


class Course(TimestampMixin, db.Model):
    __tablename__ = "courses"
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(30), unique=True, nullable=False)
    title = db.Column(db.String(180), nullable=False)
    credits = db.Column(db.Numeric(4, 1), nullable=False, default=3)
    department_id = db.Column(db.Integer, db.ForeignKey("departments.id"), nullable=True)


class Semester(TimestampMixin, db.Model):
    __tablename__ = "semesters"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(40), nullable=False)
    academic_year = db.Column(db.String(20), nullable=False)
    number = db.Column(db.Integer, nullable=False)


class Enrollment(TimestampMixin, db.Model):
    __tablename__ = "enrollments"
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey("courses.id"), nullable=False)
    semester_id = db.Column(db.Integer, db.ForeignKey("semesters.id"), nullable=False)
    faculty_id = db.Column(db.Integer, db.ForeignKey("faculty.id"), nullable=True)
    __table_args__ = (db.UniqueConstraint("student_id", "course_id", "semester_id"),)


class AttendanceSession(TimestampMixin, db.Model):
    __tablename__ = "attendance_sessions"
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey("courses.id"), nullable=False)
    faculty_id = db.Column(db.Integer, db.ForeignKey("faculty.id"), nullable=False)
    token_hash = db.Column(db.String(128), unique=True, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False, index=True)
    is_open = db.Column(db.Boolean, nullable=False, default=True)


class AttendanceRecord(TimestampMixin, db.Model):
    __tablename__ = "attendance_records"
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey("attendance_sessions.id"), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False)
    checked_in_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    __table_args__ = (db.UniqueConstraint("session_id", "student_id"),)


class Assessment(TimestampMixin, db.Model):
    __tablename__ = "assessments"
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey("courses.id"), nullable=False)
    semester_id = db.Column(db.Integer, db.ForeignKey("semesters.id"), nullable=False)
    title = db.Column(db.String(120), nullable=False)
    assessment_type = db.Column(db.String(30), nullable=False)
    max_marks = db.Column(db.Numeric(7, 2), nullable=False)


class Mark(TimestampMixin, db.Model):
    __tablename__ = "marks"
    id = db.Column(db.Integer, primary_key=True)
    assessment_id = db.Column(db.Integer, db.ForeignKey("assessments.id"), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False)
    score = db.Column(db.Numeric(7, 2), nullable=False)
    __table_args__ = (db.UniqueConstraint("assessment_id", "student_id"),)


class Assignment(TimestampMixin, db.Model):
    __tablename__ = "assignments"
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey("courses.id"), nullable=False)
    faculty_id = db.Column(db.Integer, db.ForeignKey("faculty.id"), nullable=False)
    title = db.Column(db.String(180), nullable=False)
    instructions = db.Column(db.Text, nullable=True)
    due_at = db.Column(db.DateTime, nullable=False)


class AssignmentSubmission(TimestampMixin, db.Model):
    __tablename__ = "assignment_submissions"
    id = db.Column(db.Integer, primary_key=True)
    assignment_id = db.Column(db.Integer, db.ForeignKey("assignments.id"), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False)
    file_url = db.Column(db.Text, nullable=True)
    submitted_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    score = db.Column(db.Numeric(7, 2), nullable=True)
    feedback = db.Column(db.Text, nullable=True)
    __table_args__ = (db.UniqueConstraint("assignment_id", "student_id"),)


class PTMMeeting(TimestampMixin, db.Model):
    __tablename__ = "ptm_meetings"
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False)
    faculty_id = db.Column(db.Integer, db.ForeignKey("faculty.id"), nullable=False)
    requested_by_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    mode = db.Column(db.String(20), nullable=False, default="in_person")
    scheduled_at = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(20), nullable=False, default="Requested")
    meeting_minutes = db.Column(db.Text, nullable=True)


class FacultyFeedback(TimestampMixin, db.Model):
    __tablename__ = "faculty_feedback"
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=True)
    faculty_id = db.Column(db.Integer, db.ForeignKey("faculty.id"), nullable=False)
    teaching_clarity = db.Column(db.Integer, nullable=False)
    punctuality_coverage = db.Column(db.Integer, nullable=False)
    doubt_resolution = db.Column(db.Integer, nullable=False)
    practical_guidance = db.Column(db.Integer, nullable=False)
    course_materials = db.Column(db.Integer, nullable=False)
    comments = db.Column(db.Text, nullable=True)
    is_anonymous = db.Column(db.Boolean, nullable=False, default=False)


class Remediation(TimestampMixin, db.Model):
    __tablename__ = "remediations"
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey("courses.id"), nullable=True)
    reason = db.Column(db.String(180), nullable=False)
    notes = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), nullable=False, default="Open")


class TranscriptVerification(TimestampMixin, db.Model):
    __tablename__ = "transcript_verifications"
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False)
    verification_code = db.Column(db.String(80), unique=True, nullable=False, index=True)
    issued_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    revoked = db.Column(db.Boolean, nullable=False, default=False)


@login_manager.user_loader
def load_user(user_id):
    try:
        return db.session.get(User, int(user_id))
    except (TypeError, ValueError):
        return None
