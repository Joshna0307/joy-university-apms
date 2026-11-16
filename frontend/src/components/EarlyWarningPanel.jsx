import { useEffect, useState } from "react";
import { api } from "../services/api";

export default function EarlyWarningPanel() {
  const [warnings, setWarnings] = useState([]);
  const [plans, setPlans] = useState([]);
  const [notes, setNotes] = useState({});
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);

  async function load() {
    setError("");
    try {
      const [warningData, planData] = await Promise.all([api("/admin/early-warnings"), api("/admin/remediations")]);
      setWarnings(warningData.warnings || []);
      setPlans(planData.remediations || []);
    } catch (e) { setError(e.message); }
  }
  useEffect(() => { load(); }, []);

  async function createPlan(item) {
    setBusy(true); setError(""); setMessage("");
    try {
      const result = await api("/admin/remediations", { method: "POST", body: JSON.stringify({ student_id: item.student_id, course_id: item.course_id, reason: item.reasons.join("; "), notes: notes[item.student_id] || "" }) });
      setMessage(result.message);
      await load();
    } catch (e) { setError(e.message); }
    finally { setBusy(false); }
  }

  async function updatePlan(id, status) {
    setBusy(true); setError("");
    try {
      await api(`/admin/remediations/${id}`, { method: "PATCH", body: JSON.stringify({ status }) });
      setMessage("Remediation status updated.");
      await load();
    } catch (e) { setError(e.message); }
    finally { setBusy(false); }
  }

  return <section className="admin-panel">
    <div className="admin-panel-heading"><p className="eyebrow">STUDENT SUPPORT</p><h3>Early warnings & remediation</h3><p className="muted">Flags students with attendance below 75% or recorded assessment scores below 50%.</p></div>
    {error&&<p className="admin-error">{error}</p>}{message&&<p className="admin-notice">{message}</p>}
    <div className="warning-list"><h4>Students needing attention ({warnings.length})</h4>
      {warnings.length?warnings.map((w)=><article className="warning-item" key={w.student_id+"-"+w.course_id}><div><b>{w.name} · {w.register_number}</b><small>{w.course} · Attendance: {w.attendance_percentage===null?"Not recorded":w.attendance_percentage+"%"} · Marks: {w.academic_percentage===null?"Not recorded":w.academic_percentage+"%"}</small><p>{w.reasons.join(" · ")}</p></div><div className="warning-action"><input placeholder="Support plan notes (optional)" value={notes[w.student_id]||""} onChange={e=>setNotes(v=>({...v,[w.student_id]:e.target.value}))}/><button disabled={busy} onClick={()=>createPlan(w)}>Create plan</button></div></article>):<p className="muted">No students currently meet the warning conditions, or no attendance/marks have been recorded yet.</p>}
    </div>
    <div className="warning-list"><h4>Remediation plans ({plans.length})</h4>{plans.length?plans.map(p=><article className="warning-item" key={p.id}><div><b>{p.student} · {p.course}</b><small>{p.reason}</small>{p.notes&&<p>{p.notes}</p>}</div><select value={p.status} disabled={busy} onChange={e=>updatePlan(p.id,e.target.value)}><option>Open</option><option>In Progress</option><option>Completed</option></select></article>):<p className="muted">No remediation plans created.</p>}</div>
  </section>;
}
