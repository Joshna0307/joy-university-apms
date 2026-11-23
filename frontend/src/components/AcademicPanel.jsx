import { useEffect, useState } from "react";
import { api } from "../services/api";
import { QRCodeSVG } from "qrcode.react";

function dateLabel(value) {
  return value ? new Date(value).toLocaleString([], { dateStyle: "medium", timeStyle: "short" }) : "Not scheduled";
}

export default function AcademicPanel({ role }) {
  const [tab, setTab] = useState("assignments");
  const [courses, setCourses] = useState([]);
  const [assignments, setAssignments] = useState([]);
  const [assessments, setAssessments] = useState([]);
  const [ptm, setPtm] = useState([]);
  const [facultyList, setFacultyList] = useState([]);
  const [form, setForm] = useState({});
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [transcript, setTranscript] = useState(null);
  const [activeAssessment, setActiveAssessment] = useState(null);
  const [roster, setRoster] = useState([]);
  const [submissionList, setSubmissionList] = useState([]);
  const [activeAssignment, setActiveAssignment] = useState(null);

  async function load() {
    setError("");
    try {
      const [courseData, assignmentData, assessmentData, ptmData] = await Promise.all([
        api("/attendance/courses"), api("/academics/assignments"), api("/academics/assessments"), api("/academics/ptm")
      ]);
      setCourses(courseData.courses || []);
      setAssignments(assignmentData.assignments || []);
      setAssessments(assessmentData.assessments || []);
      setPtm(ptmData.meetings || []);
      if (role === "student") { const facultyData = await api("/academics/faculty-directory"); setFacultyList(facultyData.faculty || []); }
    } catch (e) { setError(e.message); }
  }

  useEffect(() => { load(); }, [role]);

  async function act(path, method, payload) {
    setBusy(true); setError(""); setMessage("");
    try {
      const result = await api(path, { method, body: JSON.stringify(payload) });
      setMessage(result.message || "Saved successfully.");
      setForm({});
      await load();
      return result;
    } catch (e) { setError(e.message); return null; }
    finally { setBusy(false); }
  }

  async function loadSubmissions(assignment) {
    setBusy(true); setError(""); setActiveAssignment(assignment);
    try { const data = await api(`/academics/assignments/${assignment.id}/submissions`); setSubmissionList(data.submissions || []); }
    catch (e) { setError(e.message); setSubmissionList([]); }
    finally { setBusy(false); }
  }

  async function loadRoster(assessment) {
    setBusy(true); setError(""); setActiveAssessment(assessment);
    try {
      const data = await api(`/academics/assessments/${assessment.id}/students`);
      setRoster(data.students || []);
    } catch (e) { setError(e.message); setRoster([]); }
    finally { setBusy(false); }
  }

  async function saveMark(assessmentId, studentId, score) {
    await act(`/academics/assessments/${assessmentId}/marks`, "POST", { student_id: studentId, score: Number(score) });
    if (activeAssessment) await loadRoster(activeAssessment);
  }

  async function openTranscript() {
    setBusy(true); setError("");
    try {
      setTranscript(await api("/academics/transcript"));
      setTab("transcript");
    } catch (e) { setError(e.message); }
    finally { setBusy(false); }
  }

  const tabs = role === "faculty" ? [["assignments","Assignments"],["assessments","Assessments"],["ptm","PTM"]] : [["assignments","Assignments"],["results","My results"],["ptm","PTM"],["feedback","Feedback"],["transcript","Transcript"]];
  return (
    <section className="academic-panel">
      <div className="academic-heading"><div><p className="eyebrow">TEACHING & LEARNING</p><h3>Academic workspace</h3></div><button className="refresh-button" onClick={load}>Refresh</button></div>
      <div className="academic-tabs">{tabs.map(([key,label]) => <button type="button" key={key} className={tab===key?"selected":""} onClick={() => key==="transcript" && role==="student" ? openTranscript() : setTab(key)}>{label}</button>)}</div>
      {error && <p className="academic-error" role="alert">{error}</p>}
      {message && <p className="academic-notice" role="status">{message}</p>}
      {tab==="assignments" && <div className="academic-grid">
        {role==="faculty" && <form className="academic-form" onSubmit={e=>{e.preventDefault();act("/academics/assignments","POST",{course_id:Number(form.course_id),title:form.title,instructions:form.instructions,due_at:form.due_at});}}>
          <h4>Create assignment</h4><label>Course<select required value={form.course_id||""} onChange={e=>setForm(v=>({...v,course_id:e.target.value}))}><option value="">Select course</option>{courses.map(c=><option key={c.id} value={c.id}>{c.code} — {c.title}</option>)}</select></label>
          <label>Title<input required value={form.title||""} onChange={e=>setForm(v=>({...v,title:e.target.value}))}/></label>
          <label>Instructions<textarea value={form.instructions||""} onChange={e=>setForm(v=>({...v,instructions:e.target.value}))}/></label>
          <label>Due date & time<input required type="datetime-local" value={form.due_at||""} onChange={e=>setForm(v=>({...v,due_at:e.target.value}))}/></label><button disabled={busy}>Publish assignment</button>
        </form>}
        <div className="academic-list"><h4>{role==="faculty"?"Published assignments":"Assignments for your courses"}</h4>{assignments.length?assignments.map(a=><article className="academic-item" key={a.id}><div><b>{a.title}</b><small>{a.course} · Due {dateLabel(a.due_at)}</small>{a.instructions&&<p>{a.instructions}</p>}</div>{role==="student"&&a.submission&&<div className="submission-status"><small>Submitted {dateLabel(a.submission.submitted_at)} · {a.submission.score===null?"Awaiting grade":`Score ${a.submission.score}/100`}</small>{a.submission.feedback&&<p>{a.submission.feedback}</p>}{a.submission.file_url&&<a href={a.submission.file_url} target="_blank" rel="noreferrer">View submitted link ↗</a>}</div>}{role==="student"&&<form onSubmit={e=>{e.preventDefault();act(`/academics/assignments/${a.id}/submit`,"POST",{file_url:form[`url_${a.id}`]});}}><input type="url" required placeholder="Paste your submission link" value={form[`url_${a.id}`]||a.submission?.file_url||""} onChange={e=>setForm(v=>({...v,[`url_${a.id}`]:e.target.value}))}/><button disabled={busy}>Submit link</button></form>}{role==="faculty"&&<button type="button" onClick={()=>loadSubmissions(a)}>View submissions</button>}</article>):<p className="muted">No assignments available yet.</p>}{role==="faculty"&&activeAssignment&&<div className="mark-roster"><h4>Submissions: {activeAssignment.title}</h4>{submissionList.length?submissionList.map((s,i)=><div className="mark-row" key={s.student_id||s.register_number||i}><div><b>{s.student}</b><small>{s.register_number} · {dateLabel(s.submitted_at)} · {s.score===null?"Not graded":`Score ${s.score}/100`}</small>{s.feedback&&<p>{s.feedback}</p>}<a href={s.file_url} target="_blank" rel="noreferrer">Open submission ↗</a></div><form className="submission-grade-form" onSubmit={async e=>{e.preventDefault();const formElement=e.currentTarget;const result=await act(`/academics/assignments/${activeAssignment.id}/submissions/${s.student_id}`,"PATCH",{score:Number(formElement.elements.score.value),feedback:formElement.elements.feedback.value});if(result)await loadSubmissions(activeAssignment);}}><label>Score / 100<input name="score" type="number" min="0" max="100" step="0.01" required defaultValue={s.score??""}/></label><label>Feedback<textarea name="feedback" maxLength="3000" defaultValue={s.feedback||""}/></label><button disabled={busy}>Save grade</button></form></div>):<p className="muted">No submissions received yet.</p>}</div>}</div>
      </div>}
      {tab==="assessments"&&role==="faculty"&&<div className="academic-grid"><form className="academic-form" onSubmit={e=>{e.preventDefault();act("/academics/assessments","POST",{course_id:Number(form.course_id),semester_id:Number(form.semester_id),title:form.title,assessment_type:form.assessment_type||"internal",max_marks:Number(form.max_marks)});}}><h4>Create assessment</h4>
        <label>Course<select required value={form.course_id||""} onChange={e=>setForm(v=>({...v,course_id:e.target.value}))}><option value="">Select course</option>{courses.map(c=><option key={c.id} value={c.id}>{c.code} — {c.title}</option>)}</select></label>
        <label>Semester ID<input required type="number" min="1" value={form.semester_id||""} onChange={e=>setForm(v=>({...v,semester_id:e.target.value}))}/></label>
        <label>Assessment title<input required value={form.title||""} onChange={e=>setForm(v=>({...v,title:e.target.value}))}/></label>
        <label>Type<select value={form.assessment_type||"internal"} onChange={e=>setForm(v=>({...v,assessment_type:e.target.value}))}><option value="internal">Internal</option><option value="ia-1">IA-1</option><option value="ia-2">IA-2</option><option value="assignment">Assignment</option><option value="end-semester">End semester</option></select></label>
        <label>Maximum marks<input required type="number" min="1" step="0.5" value={form.max_marks||""} onChange={e=>setForm(v=>({...v,max_marks:e.target.value}))}/></label><button disabled={busy}>Create assessment</button></form>
        <div className="academic-list"><h4>Assessments</h4>{assessments.map(a=><article className="academic-item" key={a.id}><div><b>{a.title}</b><small>{a.course} · {a.assessment_type} · Max {a.max_marks}</small></div><button type="button" onClick={()=>loadRoster(a)}>Enter marks</button></article>)}{activeAssessment&&<div className="mark-roster"><h4>Marks: {activeAssessment.title}</h4>{roster.length?roster.map(s=><form className="mark-row" key={s.id} onSubmit={e=>{e.preventDefault();saveMark(activeAssessment.id,s.id,e.currentTarget.elements.score.value);}}><div><b>{s.name}</b><small>{s.register_number} · Current: {s.score??"Not entered"}</small></div><input name="score" type="number" min="0" max={activeAssessment.max_marks} step="0.01" required defaultValue={s.score??""} placeholder={`0–${activeAssessment.max_marks}`}/><button disabled={busy}>Save</button></form>):<p className="muted">No students are enrolled for this course and semester.</p>}</div>}</div></div>}
      {tab==="results"&&role==="student"&&<div className="academic-list"><h4>Recorded marks</h4>{assessments.length?assessments.map(a=><article className="academic-item" key={a.id}><div><b>{a.title}</b><small>{a.course} · {a.assessment_type}</small></div><strong>{a.score===null?"Pending":`${a.score} / ${a.max_marks}`}</strong></article>):<p className="muted">No marks have been published yet.</p>}</div>}
      {tab==="ptm"&&<div className="academic-list">{role==="student"&&<form className="ptm-request" onSubmit={e=>{e.preventDefault();act("/academics/ptm","POST",{faculty_id:Number(form.faculty_id),mode:form.mode||"in_person"});}}><h4>Request a meeting</h4><label>Faculty member<select required value={form.faculty_id||""} onChange={e=>setForm(v=>({...v,faculty_id:e.target.value}))}><option value="">Select faculty</option>{facultyList.map(f=><option key={f.id} value={f.id}>{f.name} · {f.employee_number}</option>)}</select></label><label>Meeting mode<select value={form.mode||"in_person"} onChange={e=>setForm(v=>({...v,mode:e.target.value}))}><option value="in_person">In person</option><option value="virtual">Virtual</option></select></label><button disabled={busy}>Send PTM request</button></form>}<h4>Parent–teacher meetings</h4>{ptm.length?ptm.map(m=><article className="academic-item" key={m.id}><div><b>{role==="faculty"?m.student:m.faculty}</b><small>{m.register_number} · {m.mode.replace("_"," ")} · {m.status} · {dateLabel(m.scheduled_at)}</small>{m.meeting_minutes&&<p>{m.meeting_minutes}</p>}</div>{role==="faculty"&&m.status==="Requested"&&<form onSubmit={e=>{e.preventDefault();act(`/academics/ptm/${m.id}`,"PATCH",{status:"Scheduled",scheduled_at:form[`ptm_${m.id}`]});}}><input required type="datetime-local" value={form[`ptm_${m.id}`]||""} onChange={e=>setForm(v=>({...v,[`ptm_${m.id}`]:e.target.value}))}/><button disabled={busy}>Schedule</button></form>}{role==="faculty"&&m.status==="Scheduled"&&<form onSubmit={e=>{e.preventDefault();act(`/academics/ptm/${m.id}`,"PATCH",{status:"Completed",meeting_minutes:form[`minutes_${m.id}`]||""});}}><input placeholder="Meeting minutes (optional)" value={form[`minutes_${m.id}`]||""} onChange={e=>setForm(v=>({...v,[`minutes_${m.id}`]:e.target.value}))}/><button disabled={busy}>Mark completed</button></form>}</article>):<p className="muted">No PTM requests yet.</p>}</div>}
      {tab==="feedback"&&role==="student"&&<form className="academic-form feedback-form" onSubmit={e=>{e.preventDefault();act("/academics/feedback","POST",{faculty_id:Number(form.feedback_faculty_id),teaching_clarity:Number(form.teaching_clarity),punctuality_coverage:Number(form.punctuality_coverage),doubt_resolution:Number(form.doubt_resolution),practical_guidance:Number(form.practical_guidance),course_materials:Number(form.course_materials),comments:form.comments,is_anonymous:!!form.is_anonymous});}}><h4>Faculty feedback</h4><label>Faculty member<select required value={form.feedback_faculty_id||""} onChange={e=>setForm(v=>({...v,feedback_faculty_id:e.target.value}))}><option value="">Select faculty</option>{facultyList.map(f=><option key={f.id} value={f.id}>{f.name}</option>)}</select></label>{[["teaching_clarity","Teaching clarity"],["punctuality_coverage","Punctuality & syllabus coverage"],["doubt_resolution","Doubt resolution & mentorship"],["practical_guidance","Practical / lab guidance"],["course_materials","Course notes & materials"]].map(([key,label])=><label key={key}>{label}<select required value={form[key]||""} onChange={e=>setForm(v=>({...v,[key]:e.target.value}))}><option value="">Rate from 1 to 5</option>{[1,2,3,4,5].map(n=><option key={n} value={n}>{n} / 5</option>)}</select></label>)}<label>Comments<textarea value={form.comments||""} onChange={e=>setForm(v=>({...v,comments:e.target.value}))}/></label><label className="anonymous-check"><input type="checkbox" checked={!!form.is_anonymous} onChange={e=>setForm(v=>({...v,is_anonymous:e.target.checked}))}/> Submit anonymously</label><button disabled={busy}>Submit feedback</button></form>}
      {tab==="transcript"&&role==="student"&&<div className="transcript-area">{transcript?<><div className="transcript-paper"><div className="transcript-title"><p>JOY UNIVERSITY</p><h2>Academic Transcript</h2><small>Raja Nagar, Vadakangulam, Tirunelveli District, Tamil Nadu</small></div><div className="transcript-student"><b>{transcript.student.name}</b><span>Register No: {transcript.student.register_number}</span><span>Batch: {transcript.student.batch||"—"} · Semester: {transcript.student.semester||"—"}</span></div><table className="records-table"><thead><tr><th>Course</th><th>Credits</th><th>Marks</th><th>Percentage</th></tr></thead><tbody>{transcript.courses.map((c,i)=><tr key={i}><td>{c.course_code} — {c.course_title}</td><td>{c.credits}</td><td>{c.earned_marks}/{c.maximum_marks}</td><td>{c.percentage===null?"—":c.percentage+"%"}</td></tr>)}</tbody></table><h3>Estimated CGPA: {transcript.cgpa_estimate??"Pending"}</h3><p className="muted">{transcript.notice}</p><div className="transcript-verify"><QRCodeSVG value={`${(import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:5000/api").replace(/\/api\/?$/, "")}${transcript.verification_path}`} size={112} includeMargin/><small>Scan this QR code to verify the transcript. Code: {transcript.verification_code}</small></div></div><button className="print-button" onClick={()=>window.print()}>Print / Save as PDF</button></>:<button onClick={openTranscript} disabled={busy}>Load transcript</button>}</div>}
    </section>
  );
}
