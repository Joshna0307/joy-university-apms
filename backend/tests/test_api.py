import os

os.environ["DATABASE_URL"] = "sqlite://"
os.environ["SECRET_KEY"] = "apms-test-secret-key"
os.environ["FLASK_ENV"] = "testing"

import pytest

from app import create_app, db
from datetime import datetime

from app.models import Assignment, AssignmentSubmission, Course, Department, Enrollment, Faculty, Semester, Student, User


@pytest.fixture()
def app():
    application = create_app()
    application.config.update(TESTING=True)
    with application.app_context():
        db.drop_all()
        db.create_all()
    yield application
    with application.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


def make_user(name, email, role, password="TestPassword123!"):
    user = User(name=name, email=email, role=role, active=True)
    user.set_password(password)
    db.session.add(user)
    db.session.flush()
    return user


def test_student_registration_requires_admin_approval(client, app):
    response = client.post("/api/auth/register", json={
        "name": "Test Student",
        "email": "teststudent@joyuniversity.edu.in",
        "register_number": "JU-TEST-001",
        "password": "StrongPassword123!",
    })
    assert response.status_code == 202

    blocked = client.post("/api/auth/login", json={
        "email": "teststudent@joyuniversity.edu.in",
        "password": "StrongPassword123!",
    })
    assert blocked.status_code == 403

    with app.app_context():
        make_user("Admin", "admin@joyuniversity.edu.in", "admin")
        db.session.commit()
        pending_user_id = User.query.filter_by(email="teststudent@joyuniversity.edu.in").first().id
    assert client.post("/api/auth/login", json={
        "email": "admin@joyuniversity.edu.in",
        "password": "TestPassword123!",
    }).status_code == 200

    approved = client.post(f"/api/admin/pending-registrations/{pending_user_id}/approve")
    assert approved.status_code == 200
    assert client.post("/api/auth/logout").status_code == 200
    active = client.post("/api/auth/login", json={
        "email": "teststudent@joyuniversity.edu.in",
        "password": "StrongPassword123!",
    })
    assert active.status_code == 200


def test_student_registration_rejects_non_university_email(client):
    response = client.post("/api/auth/register", json={
        "name": "Test Student",
        "email": "outside@example.com",
        "register_number": "JU-TEST-002",
        "password": "StrongPassword123!",
    })
    assert response.status_code == 400


def test_admin_routes_require_admin_role(client, app):
    with app.app_context():
        user = make_user("Student", "student@joyuniversity.edu.in", "student")
        Student(user_id=user.id, register_number="JU-TEST-003")
        db.session.commit()
    assert client.post("/api/auth/login", json={
        "email": "student@joyuniversity.edu.in",
        "password": "TestPassword123!",
    }).status_code == 200
    response = client.get("/api/admin/departments")
    assert response.status_code == 403


def test_qr_attendance_checkin_and_duplicate_prevention(client, app):
    with app.app_context():
        faculty_user = make_user("Faculty", "faculty@joyuniversity.edu.in", "faculty")
        faculty = Faculty(user_id=faculty_user.id, employee_number="FAC-001")
        student_user = make_user("Student", "student@joyuniversity.edu.in", "student")
        student = Student(user_id=student_user.id, register_number="JU-TEST-004")
        course = Course(code="CS101", title="Computer Science", credits=3)
        semester = Semester(name="Semester 1", academic_year="2026-2027", number=1)
        db.session.add_all([faculty, student, course, semester])
        db.session.flush()
        db.session.add(Enrollment(
            student_id=student.id, course_id=course.id,
            semester_id=semester.id, faculty_id=faculty.id,
        ))
        db.session.commit()
        course_id = course.id
        faculty_id = faculty.id

    assert client.post("/api/auth/login", json={
        "email": "faculty@joyuniversity.edu.in",
        "password": "TestPassword123!",
    }).status_code == 200
    created = client.post("/api/attendance/sessions", json={"course_id": course_id})
    assert created.status_code == 201
    payload = created.get_json()
    token = payload["qr_payload"]
    session_id = payload["session_id"]

    client.post("/api/auth/logout")
    assert client.post("/api/auth/login", json={
        "email": "student@joyuniversity.edu.in",
        "password": "TestPassword123!",
    }).status_code == 200
    first = client.post("/api/attendance/check-in", json={"token": token})
    assert first.status_code == 201
    duplicate = client.post("/api/attendance/check-in", json={"token": token})
    assert duplicate.status_code == 409

    client.post("/api/auth/logout")
    client.post("/api/auth/login", json={
        "email": "faculty@joyuniversity.edu.in",
        "password": "TestPassword123!",
    })
    feed = client.get(f"/api/attendance/sessions/{session_id}/feed")
    assert feed.status_code == 200
    assert feed.get_json()["total_checked_in"] == 1
    assert feed.get_json()["check_ins"][0]["register_number"] == "JU-TEST-004"


def test_admin_can_edit_core_records_and_students_cannot(client, app):
    with app.app_context():
        admin = make_user("Admin", "admin-edit@joyuniversity.edu.in", "admin")
        student_user = make_user("Student", "student-edit@joyuniversity.edu.in", "student")
        student = Student(user_id=student_user.id, register_number="JU-EDIT-001")
        faculty_user = make_user("Faculty", "faculty-edit@joyuniversity.edu.in", "faculty")
        faculty = Faculty(user_id=faculty_user.id, employee_number="FAC-EDIT-001")
        department = Department(name="Computing", code="COMP")
        course = Course(code="CS100", title="Intro to Computing", credits=3)
        semester = Semester(name="Semester 1", academic_year="2026-2027", number=1)
        db.session.add_all([student, faculty, department, course, semester])
        db.session.commit()
        ids = {
            "student": student.id,
            "faculty": faculty.id,
            "department": department.id,
            "course": course.id,
            "semester": semester.id,
        }

    assert client.post("/api/auth/login", json={
        "email": "admin-edit@joyuniversity.edu.in",
        "password": "TestPassword123!",
    }).status_code == 200

    department_update = client.patch(f"/api/admin/departments/{ids['department']}", json={
        "name": "School of Computing", "code": "SOC",
    })
    assert department_update.status_code == 200
    assert department_update.get_json()["department"]["code"] == "SOC"

    course_update = client.patch(f"/api/admin/courses/{ids['course']}", json={
        "code": "CS101", "title": "Foundations of Computing", "credits": 4,
        "department_id": ids["department"],
    })
    assert course_update.status_code == 200
    assert course_update.get_json()["course"]["credits"] == 4.0

    student_update = client.patch(f"/api/admin/students/{ids['student']}", json={
        "name": "Updated Student", "register_number": "JU-EDIT-002",
        "semester": 2, "department_id": ids["department"],
    })
    assert student_update.status_code == 200
    assert student_update.get_json()["student"]["name"] == "Updated Student"

    faculty_update = client.patch(f"/api/admin/faculty/{ids['faculty']}", json={
        "name": "Updated Faculty", "employee_number": "FAC-EDIT-002",
        "department_id": ids["department"],
    })
    assert faculty_update.status_code == 200
    assert faculty_update.get_json()["faculty"]["employee_number"] == "FAC-EDIT-002"

    semester_update = client.patch(f"/api/admin/semesters/{ids['semester']}", json={
        "name": "Semester One", "academic_year": "2026-2027", "number": 2,
    })
    assert semester_update.status_code == 200
    assert semester_update.get_json()["semester"]["number"] == 2

    client.post("/api/auth/logout")
    assert client.post("/api/auth/login", json={
        "email": "student-edit@joyuniversity.edu.in",
        "password": "TestPassword123!",
    }).status_code == 200
    denied = client.patch(f"/api/admin/courses/{ids['course']}", json={"title": "Unauthorized"})
    assert denied.status_code == 403

def test_admin_can_edit_enrollments_and_students_cannot(client, app):
    with app.app_context():
        admin_user = make_user("Admin", "admin-enrollment@joyuniversity.edu.in", "admin")
        student_one_user = make_user("Student One", "student-one-enrollment@joyuniversity.edu.in", "student")
        student_two_user = make_user("Student Two", "student-two-enrollment@joyuniversity.edu.in", "student")
        faculty_user = make_user("Faculty", "faculty-enrollment@joyuniversity.edu.in", "faculty")
        student_one = Student(user_id=student_one_user.id, register_number="JU-ENR-001")
        student_two = Student(user_id=student_two_user.id, register_number="JU-ENR-002")
        faculty = Faculty(user_id=faculty_user.id, employee_number="FAC-ENR-001")
        original_course = Course(code="ENR101", title="Original Course", credits=3)
        target_course = Course(code="ENR201", title="Target Course", credits=4)
        semester = Semester(name="Semester 1", academic_year="2026-2027", number=1)
        db.session.add_all([
            student_one, student_two, faculty, original_course, target_course, semester,
        ])
        db.session.flush()
        original = Enrollment(
            student_id=student_one.id,
            course_id=original_course.id,
            semester_id=semester.id,
        )
        duplicate_guard = Enrollment(
            student_id=student_two.id,
            course_id=target_course.id,
            semester_id=semester.id,
        )
        db.session.add_all([original, duplicate_guard])
        db.session.commit()
        enrollment_id = original.id
        student_two_id = student_two.id
        target_course_id = target_course.id
        faculty_id = faculty.id

    assert client.post("/api/auth/login", json={
        "email": "admin-enrollment@joyuniversity.edu.in",
        "password": "TestPassword123!",
    }).status_code == 200

    listed = client.get("/api/admin/enrollments")
    assert listed.status_code == 200
    enrollment = next(item for item in listed.get_json()["enrollments"] if item["id"] == enrollment_id)
    assert enrollment["course_id"] != target_course_id
    assert enrollment["faculty_id"] is None

    updated = client.patch(f"/api/admin/enrollments/{enrollment_id}", json={
        "course_id": target_course_id,
        "faculty_id": faculty_id,
    })
    assert updated.status_code == 200
    assert updated.get_json()["enrollment"]["course_id"] == target_course_id
    assert updated.get_json()["enrollment"]["faculty_id"] == faculty_id

    duplicate = client.patch(f"/api/admin/enrollments/{enrollment_id}", json={
        "student_id": student_two_id,
    })
    assert duplicate.status_code == 409

    client.post("/api/auth/logout")
    assert client.post("/api/auth/login", json={
        "email": "student-one-enrollment@joyuniversity.edu.in",
        "password": "TestPassword123!",
    }).status_code == 200
    denied = client.patch(f"/api/admin/enrollments/{enrollment_id}", json={
        "faculty_id": None,
    })
    assert denied.status_code == 403

def test_faculty_can_grade_assignment_submissions_and_students_cannot(client, app):
    with app.app_context():
        faculty_user = make_user("Faculty", "faculty-grade@joyuniversity.edu.in", "faculty")
        faculty = Faculty(user_id=faculty_user.id, employee_number="FAC-GRADE-001")
        student_user = make_user("Student", "student-grade@joyuniversity.edu.in", "student")
        student = Student(user_id=student_user.id, register_number="JU-GRADE-001")
        course = Course(code="GRADE101", title="Assessment Course", credits=3)
        semester = Semester(name="Semester 1", academic_year="2026-2027", number=1)
        db.session.add_all([faculty, student, course, semester])
        db.session.flush()
        db.session.add(Enrollment(
            student_id=student.id,
            course_id=course.id,
            semester_id=semester.id,
            faculty_id=faculty.id,
        ))
        assignment = Assignment(
            course_id=course.id,
            faculty_id=faculty.id,
            title="Lab report",
            instructions="Submit the report link",
            due_at=datetime(2026, 12, 1, 12, 0),
        )
        db.session.add(assignment)
        db.session.flush()
        submission = AssignmentSubmission(
            assignment_id=assignment.id,
            student_id=student.id,
            file_url="https://example.edu/submissions/lab-report",
        )
        db.session.add(submission)
        db.session.commit()
        assignment_id = assignment.id
        student_id = student.id

    assert client.post("/api/auth/login", json={
        "email": "faculty-grade@joyuniversity.edu.in",
        "password": "TestPassword123!",
    }).status_code == 200

    listed = client.get(f"/api/academics/assignments/{assignment_id}/submissions")
    assert listed.status_code == 200
    assert listed.get_json()["submissions"][0]["student_id"] == student_id

    graded = client.patch(
        f"/api/academics/assignments/{assignment_id}/submissions/{student_id}",
        json={"score": 87.5, "feedback": "Clear explanation and good analysis."},
    )
    assert graded.status_code == 200
    assert graded.get_json()["score"] == 87.5

    invalid = client.patch(
        f"/api/academics/assignments/{assignment_id}/submissions/{student_id}",
        json={"score": 101, "feedback": "Invalid score"},
    )
    assert invalid.status_code == 400

    client.post("/api/auth/logout")
    assert client.post("/api/auth/login", json={
        "email": "student-grade@joyuniversity.edu.in",
        "password": "TestPassword123!",
    }).status_code == 200
    student_assignments = client.get("/api/academics/assignments")
    assert student_assignments.status_code == 200
    visible = student_assignments.get_json()["assignments"][0]["submission"]
    assert visible["score"] == 87.5
    assert visible["feedback"] == "Clear explanation and good analysis."

    denied = client.patch(
        f"/api/academics/assignments/{assignment_id}/submissions/{student_id}",
        json={"score": 90},
    )
    assert denied.status_code == 403
