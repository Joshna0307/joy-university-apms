import os

os.environ["DATABASE_URL"] = "sqlite://"
os.environ["SECRET_KEY"] = "apms-test-secret-key"
os.environ["FLASK_ENV"] = "testing"

import pytest

from app import create_app, db
from app.models import Course, Department, Enrollment, Faculty, Semester, Student, User


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
        admin = make_user("Admin", "admin@joyuniversity.edu.in", "admin")
        admin_id = admin.id
    assert client.post("/api/auth/login", json={
        "email": "admin@joyuniversity.edu.in",
        "password": "TestPassword123!",
    }).status_code == 200

    approved = client.post(f"/api/admin/pending-registrations/{1}/approve")
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
