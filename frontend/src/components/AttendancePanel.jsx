import { useEffect, useState } from "react";
import { QRCodeSVG } from "qrcode.react";
import { api } from "../services/api";

export default function AttendancePanel({ role }) {
  const [courses, setCourses] = useState([]);
  const [courseId, setCourseId] = useState("");
  const [session, setSession] = useState(null);
  const [secondsLeft, setSecondsLeft] = useState(0);
  const [checkIns, setCheckIns] = useState([]);
  const [checkInCount, setCheckInCount] = useState(0);
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    api("/attendance/courses")
      .then((data) => setCourses(data.courses || []))
      .catch((error) => setMessage(error.message));
  }, []);

  useEffect(() => {
    if (!session) return undefined;
    const tick = () => {
      const remaining = Math.max(0, Math.ceil((new Date(session.expires_at).getTime() - Date.now()) / 1000));
      setSecondsLeft(remaining);
      if (remaining === 0) setSession((current) => current && !current.expired ? { ...current, expired: true } : current);
    };
    tick();
    const timer = window.setInterval(tick, 1000);
    return () => window.clearInterval(timer);
  }, [session?.expires_at]);

  useEffect(() => {
    if (role !== "faculty" || !session?.session_id || session.expired) return undefined;
    let cancelled = false;
    const refresh = async () => {
      try {
        const data = await api(`/attendance/sessions/${session.session_id}/feed`);
        if (!cancelled) {
          setCheckIns(data.check_ins || []);
          setCheckInCount(data.total_checked_in || 0);
        }
      } catch (error) {
        if (!cancelled) setMessage(error.message);
      }
    };
    refresh();
    const timer = window.setInterval(refresh, 3000);
    return () => {
      cancelled = true;
      window.clearInterval(timer);
    };
  }, [role, session?.session_id, session?.expired]);

  useEffect(() => {
    if (role !== "student") return undefined;
    let scanner;
    let cancelled = false;
    import("html5-qrcode").then(({ Html5QrcodeScanner }) => {
      if (cancelled) return;
      scanner = new Html5QrcodeScanner("apms-qr-reader", { fps: 10, qrbox: { width: 230, height: 230 } }, false);
      scanner.render(async (decodedText) => {
        try {
          setBusy(true);
          const result = await api("/attendance/check-in", {
            method: "POST",
            body: JSON.stringify({ token: decodedText }),
          });
          setMessage(result.message + " — " + result.course);
          scanner.clear().catch(() => {});
        } catch (error) {
          setMessage(error.message);
        } finally {
          setBusy(false);
        }
      }, () => {});
    }).catch((error) => setMessage("Camera scanner could not load: " + error.message));
    return () => {
      cancelled = true;
      scanner?.clear().catch(() => {});
    };
  }, [role]);

  async function startSession() {
    if (!courseId) {
      setMessage("Choose a course first.");
      return;
    }
    setBusy(true);
    setMessage("");
    setCheckIns([]);
    setCheckInCount(0);
    try {
      const result = await api("/attendance/sessions", {
        method: "POST",
        body: JSON.stringify({ course_id: Number(courseId) }),
      });
      setSession(result);
      setMessage("Attendance QR is active for five minutes.");
    } catch (error) {
      setMessage(error.message);
    } finally {
      setBusy(false);
    }
  }

  async function closeSession() {
    if (!session?.session_id) return;
    try {
      await api(`/attendance/sessions/${session.session_id}/close`, { method: "POST" });
      setSession((current) => current ? { ...current, expired: true } : current);
      setMessage("Attendance QR closed.");
    } catch (error) {
      setMessage(error.message);
    }
  }

  return (
    <section className="attendance-panel">
      <div className="attendance-heading">
        <div><p className="eyebrow">LIVE CLASS TOOL</p><h3>QR attendance</h3></div>
        <span className="attendance-tag">{role === "faculty" ? "Faculty" : "Student"}</span>
      </div>
      {role === "faculty" ? (
        <div className="attendance-controls">
          <label htmlFor="attendance-course">Assigned course</label>
          <select id="attendance-course" value={courseId} onChange={(event) => setCourseId(event.target.value)}>
            <option value="">Select a course</option>
            {courses.map((course) => <option key={course.id} value={course.id}>{course.code} — {course.title}</option>)}
          </select>
          <button onClick={startSession} disabled={busy || !courses.length}>{busy ? "Please wait…" : "Generate 5-minute QR"}</button>
          {session && !session.expired && (
            <div className="qr-result">
              <QRCodeSVG value={session.qr_payload} size={220} level="M" includeMargin />
              <b>{session.course.code} · {session.course.title}</b>
              <strong>{Math.floor(secondsLeft / 60)}:{String(secondsLeft % 60).padStart(2, "0")} remaining</strong>
              <button className="secondary-button" onClick={closeSession}>Close QR now</button>
            </div>
          )}
          {session && (
            <div className="checkin-feed" aria-live="polite">
              <div className="feed-heading"><h4>Live check-ins</h4><strong>{checkInCount}</strong></div>
              {checkIns.length === 0 ? <p className="muted">No students have checked in yet. This list refreshes automatically.</p> : (
                <ul>{checkIns.map((entry, index) => (
                  <li key={entry.register_number || index}>
                    <span><b>{entry.name}</b><small>{entry.register_number || "Student"}</small></span>
                    <time>{new Date(entry.checked_in_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}</time>
                  </li>
                ))}</ul>
              )}
            </div>
          )}
          {session?.expired && <p className="muted">This QR has expired or was closed. Generate a new one for the next class.</p>}
        </div>
      ) : (
        <div className="student-scan">
          <p className="muted">Allow camera access and scan the QR displayed by your faculty member.</p>
          <div id="apms-qr-reader" />
          {busy && <p className="muted">Recording your attendance…</p>}
        </div>
      )}
      {message && <p className="attendance-message" role="status">{message}</p>}
    </section>
  );
}
