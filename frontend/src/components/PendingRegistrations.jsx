import { useEffect, useState } from "react";
import { api } from "../services/api";

export default function PendingRegistrations() {
  const [rows, setRows] = useState([]);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [busyId, setBusyId] = useState(null);
  async function load() {
    try { const data = await api("/admin/pending-registrations"); setRows(data.registrations || []); setError(""); }
    catch (e) { setError(e.message); }
  }
  useEffect(() => { load(); }, []);
  async function approve(id) {
    setBusyId(id); setError(""); setMessage("");
    try { const data = await api(`/admin/pending-registrations/${id}/approve`, { method: "POST" }); setMessage(data.message); await load(); }
    catch (e) { setError(e.message); }
    finally { setBusyId(null); }
  }
  return <section className="admin-panel">
    <div className="admin-panel-heading"><p className="eyebrow">ACCOUNT SECURITY</p><h3>Pending student registrations</h3><p className="muted">Check each register number against university records before approving access.</p></div>
    {error&&<p className="admin-error">{error}</p>}{message&&<p className="admin-notice">{message}</p>}
    {rows.length?rows.map(row=><article className="warning-item" key={row.user_id}><div><b>{row.name} · {row.register_number}</b><small>{row.email} · Submitted {new Date(row.submitted_at).toLocaleDateString()}</small></div><button disabled={busyId===row.user_id} onClick={()=>approve(row.user_id)}>{busyId===row.user_id?"Approving…":"Approve account"}</button></article>):<p className="muted">No registrations are waiting for approval.</p>}
  </section>;
}
