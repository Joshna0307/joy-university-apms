"""Link existing demo student and faculty accounts to a course.
Run from backend: py -m scripts.link_demo_class
Use only a local/test database and synthetic records.
"""
from app import create_app, db
from app.models import Course, Enrollment, Semester, User

app = create_app()
with app.app_context():
    faculty_email = input("Faculty account email: ").strip().lower()
    student_email = input("Student account email: ").strip().lower()
    course_code = input("Course code: ").strip().upper()
    academic_year = input("Academic year (e.g. 2026-2027): ").strip()
    semester_number = int(input("Semester number: ").strip())
    if not 1 <= semester_number <= 12:
        raise SystemExit("Semester must be between 1 and 12.")

    faculty_user = User.query.filter_by(email=faculty_email, role="faculty", active=True).first()
    student_user = User.query.filter_by(email=student_email, role="student", active=True).first()
    course = Course.query.filter_by(code=course_code).first()
    if not faculty_user or not faculty_user.faculty_profile:
        raise SystemExit("Faculty account/profile not found.")
    if not student_user or not student_user.student_profile:
        raise SystemExit("Student account/profile not found.")
    if not course:
        raise SystemExit("Course not found. Create it in Admin > Courses.")

    semester = Semester.query.filter_by(academic_year=academic_year, number=semester_number).first()
    if semester is None:
        semester = Semester(name=f"Semester {semester_number}", academic_year=academic_year, number=semester_number)
        db.session.add(semester)
        db.session.flush()

    student = student_user.student_profile
    faculty = faculty_user.faculty_profile
    enrollment = Enrollment.query.filter_by(student_id=student.id, course_id=course.id, semester_id=semester.id).first()
    if enrollment:
        enrollment.faculty_id = faculty.id
        print("Existing enrollment updated.")
    else:
        db.session.add(Enrollment(student_id=student.id, course_id=course.id, semester_id=semester.id, faculty_id=faculty.id))
        print("Demo enrollment created.")
    db.session.commit()
    print(f"Linked {student_user.name} to {course.code} with {faculty_user.name}.")
