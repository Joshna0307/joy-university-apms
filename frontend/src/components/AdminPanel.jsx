import { useEffect, useMemo, useState } from "react";
import { api } from "../services/api";

const sections = {
  departments: { label: "Departments", endpoint: "/admin/departments", fields: [{ name: "name", label: "Department name" }, { name: "code", label: "Department code" }], columns: [["name", "Department"], ["code", "Code"]] },
  courses: { label: "Courses", endpoint: "/admin/courses", fields: [{ name: "code", label: "Course code" }, { name: "title", label: "Course title" }, { name: "credits", label: "Credits", type: "number" }, { name: "department_id", label: "Department", type: "department" }], columns: [["code", "Code"], ["title", "Course"], ["credits", "Credits"]] },
  students: { label: "Students", endpoint: "/admin/students", fields: [{ name: "name", label: "Full name" }, { name: "email", label: "University email", type: "email" }, { name: "register_number", label: "Register number" }, { name: "password", label: "Initial password (12+ characters)", type: "password" }, { name: "department_id", label: "Department", type: "department" }, { name: "batch", label: "Batch (e.g. 2026–2030)" }, { name: "semester", label: "Current semester", type: "number" }], columns: [["register_number", "Register no."], ["name", "Student"], ["email", "Email"], ["semester", "Semester"]] },
  faculty: { label: "Faculty", endpoint: "/admin/faculty", fields: [{ name: "name", label: "Full name" }, { name: "email", label: "University email", type: "email" }, { name: "employee_number", label: "Employee number" }, { name: "password", label: "Initial password (12+ characters)", type: "password" }, { name: "department_id", label: "Department", type: "department" }], columns: [["employee_number", "Employee no."], ["name", "Faculty"], ["email", "Email"]] },
  semesters: { label: "Semesters", endpoint: "/admin/semesters", fields: [{ name: "name", label: "Semester name" }, { name: "academic_year", label: "Academic year (e.g. 2026–2027)" }, { name: "number", label: "Semester number", type: "number" }], columns: [["name", "Semester"], ["academic_year", "Academic year"], ["number", "Number"]] },
  enrollments: { label: "Enrollments", endpoint: "/admin/enrollments", fields: [{ name: "student_id", label: "Student", type: "student" }, { name: "course_id", label: "Course", type: "course" }, { name: "semester_id", label: "Semester", type: "semester" }, { name: "faculty_id", label: "Assigned faculty (optional)", type: "faculty" }], columns: [["register_number", "Register no."], ["student", "Student"], ["course", "Course"], ["semester", "Semester"], ["faculty", "Faculty"]] },
};

export default function AdminPanel() {
  const [active, setActive] = useState("students");
  const [records, setRecords] = useState([]);
  const [departments, setDepartments] = useState([]);
  const [lookups, setLookups] = useState({ students: [], faculty: [], courses: [], semesters: [] });
  const [values, setValues] = useState({});
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [loading, setLoading] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const config = sections[active];
  const listKey = active;
  const fields = useMemo(() => config.fields, [config]);
  const visibleFields = editingId === null ? fields : fields.filter((field) => field.name !== "password");
  const singularLabel = { departments: "department", courses: "course", students: "student", faculty: "faculty member", semesters: "semester", enrollments: "enrollment" }[active];

  async function load() {
    setLoading(true);
    setError("");
    try {
      const data = await api(config.endpoint);
      setRecords(data[listKey] || []);
      const [deptData, studentData, facultyData, courseData, semesterData] = await Promise.all([api("/admin/departments"), api("/admin/students"), api("/admin/faculty"), api("/admin/courses"), api("/admin/semesters")]);
      setDepartments(deptData.departments || []);
      setLookups({ students: studentData.students || [], faculty: facultyData.faculty || [], courses: courseData.courses || [], semesters: semesterData.semesters || [] });
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    setValues({});
    setEditingId(null);
    setNotice("");
    load();
  }, [active]);

  function beginEdit(row) {
    if (active === "enrollments") return;
    setEditingId(row.id);
    setValues(Object.fromEntries(fields.filter((field) => field.name !== "password").map((field) => [field.name, row[field.name] ?? ""])));
    setError("");
    setNotice("");
  }

  function cancelEdit() {
    setEditingId(null);
    setValues({});
  }

  async function submit(event) {
    event.preventDefault();
    const isEditing = editingId !== null;
    setLoading(true);
    setError("");
    setNotice("");
    const payload = { ...values };
    if (payload.department_id) payload.department_id = Number(payload.department_id);
    if (payload.semester) payload.semester = Number(payload.semester);
    ["student_id", "course_id", "semester_id", "faculty_id", "number"].forEach((key) => { if (payload[key]) payload[key] = Number(payload[key]); });
    if (payload.credits) payload.credits = Number(payload.credits);
    try {
      const path = isEditing ? `${config.endpoint}/${editingId}` : config.endpoint;
      await api(path, { method: isEditing ? "PATCH" : "POST", body: JSON.stringify(payload) });
      setValues({});
      setEditingId(null);
      setNotice(`${singularLabel} ${isEditing ? "updated" : "added"} successfully.`);
      await load();
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="admin-panel">
      <div className="admin-panel-heading"><div><p className="eyebrow">INSTITUTION MANAGEMENT</p><h3>Manage university records</h3><p className="muted">Add departments, courses, student accounts and faculty accounts.</p></div></div>
      <div className="admin-tabs" role="tablist" aria-label="Record type">
        {Object.entries(sections).map(([key, item]) => <button key={key} className={active === key ? "selected" : ""} onClick={() => setActive(key)} type="button">{item.label}</button>)}
      </div>
      <div className="admin-workspace">
        <form className="admin-form" onSubmit={submit}>
          <h4>{editingId === null ? `Add ${singularLabel}` : `Edit ${singularLabel}`}</h4>
          {visibleFields.map((field) => (
            <label key={field.name}>{field.label}
              {["department","student","faculty","course","semester"].includes(field.type) ? (
                <select value={values[field.name] || ""} onChange={(e) => setValues((v) => ({ ...v, [field.name]: e.target.value }))}>
                  <option value="">{field.type === "faculty" ? "No faculty selected" : `Select ${field.type}`}</option>
                  {(field.type === "department" ? departments : lookups[field.type] || []).map((d) => <option key={d.id} value={d.id}>{field.type === "department" ? `${d.code} — ${d.name}` : field.type === "student" ? `${d.register_number} — ${d.name}` : field.type === "faculty" ? `${d.employee_number} — ${d.name}` : field.type === "course" ? `${d.code} — ${d.title}` : `${d.name} (${d.academic_year})`}</option>)}
                </select>
              ) : (
                <input type={field.type || "text"} min={field.type === "number" ? "1" : undefined} step={field.name === "credits" ? "0.5" : undefined} required={!["department_id", "batch", "semester", "faculty_id"].includes(field.name)} minLength={field.name === "password" ? 12 : undefined} value={values[field.name] || ""} onChange={(e) => setValues((v) => ({ ...v, [field.name]: e.target.value }))} />
              )}
            </label>
          ))}
          <button disabled={loading}>{loading ? "Saving…" : editingId === null ? "Save record" : "Update record"}</button>
          {editingId !== null && <button type="button" className="refresh-button" onClick={cancelEdit} disabled={loading}>Cancel edit</button>}
          <small>Passwords are saved as secure hashes and are never displayed in the records table. Existing passwords cannot be viewed or edited here.</small>
        </form>
        <div className="admin-records">
          <div className="records-heading"><h4>{config.label}</h4><span>{records.length} records</span></div>
          {error && <p className="admin-error" role="alert">{error}</p>}
          {notice && <p className="admin-notice" role="status">{notice}</p>}
          {loading && !records.length ? <p className="muted">Loading records…</p> : records.length ? (
            <div className="records-table-wrap"><table className="records-table"><thead><tr>{config.columns.map(([, label]) => <th key={label}>{label}</th>)}{active !== "enrollments" && <th>Actions</th>}</tr></thead><tbody>{records.map((row) => <tr key={row.id}>{config.columns.map(([key]) => <td key={key}>{row[key] ?? "—"}</td>)}{active !== "enrollments" && <td><button type="button" className="refresh-button" onClick={() => beginEdit(row)}>Edit</button></td>}</tr>)}</tbody></table></div>
          ) : <p className="muted empty-records">No {config.label.toLowerCase()} added yet.</p>}
        </div>
      </div>
    </section>
  );
}
