import { useEffect, useState } from "react";
import { QRCodeSVG } from "qrcode.react";
import { Html5QrcodeScanner } from "html5-qrcode";
import { api } from "../services/api";

function formatTime(value) {
  if (!value) return "—";
  return new Date(value).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
}

export default function AttendancePanel({ role }) {
  const [courses, setCourses] = useState([]);
  const [courseId, setCourseId] = useState("");
  const [session, setSession] = useState(null);
  const [secondsLeft, setSecondsLeft] = useState(0);
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);
  const [feed, setFeed] = useState([]);
  const [feedCount, setFeedCount] = useState(0);
  const [feedError, setFeedError] = useState("");

  useEffect(() => {
    api("/attendance/courses")
      .then((data) => setCourses(data.courses || []))
      .catch((error) => setMessage(error.message));
  }, []);

  useEffect(() => {
    if (!session?.expires_at || session.expired) return undefined;
    const tick = () => {
      const remaining = Math.max(0, Math.ceil((new Date(session.expires_at).getTime() - Date.now()) / 1000));
      setSecondsLeft(remaining);
      if (remaining === 0) setSession((current) => current && !current.expired ? { ...current, expired: true } : current);
    };
    tick();
    const timer = window.setInterval(tick, 1000);
    return () => window.clearInterval(timer);
  }, [session?.expires_at, session?.expired]);

  useEffect(() => {
    if (role !== "student") return undefined;
    const scanner = new Html5QrcodeScanner("apms-qr-reader", { fps: 10, qrbox: { width: 230, height: 230 } }, false);
    scanner.render(async (decodedText) => {
      if (busy) return;
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
    return () => scanner.clear().catch(() => {});
  }, [role]);

  useEffect(() => {
    if (role !== "faculty" || !session?.session_id) return undefined;
    let cancelled = false;
    const refreshFeed = async () => {
      try {
        const data = await api(`/attendance/sessions/${session.session_id}/feed`);
        if (!cancelled) {
          setFeed(data.check_ins || []);
          setFeedCount(data.total_checked_in || 0);
          setFeedError("");
          if (!data.is_open) setSession((current) => current ? { ...current, expired: true } : current);
        }
      } catch (error) {
        if (!cancelled) setFeedError(error.message);
      }
    };
    refreshFeed();
    const timer = window.setInterval(refreshFeed, 3000);
    return () => {
      cancelled = true;
      window.clearInterval(timer);
    };
  }, [role, session?.session_id]);

  async function startSession() {
    if (!courseId) {
      setMessage("Choose a course first.");
      return;
    }
    setBusy(true);
    setMessage("");
    setFeed([]);
    setFeedCount(0);
    setFeedError("");
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
      setMessage("Attendance QR closed. The check-in list is saved.");
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
          {session && (
            <div className="faculty-attendance-layout">
              <div className="qr-result">
                {!session.expired && <QRCodeSVG value={session.qr_payload} size={220} level="M" includeMargin />}
                <b>{session.course.code} · {session.course.title}</b>
                {!session.expired ? <strong>{Math.floor(secondsLeft / 60)}:{String(secondsLeft % 60).padStart(2, "0")} remaining</strong> : <span className="muted">QR session closed or expired</span>}
                {!session.expired && <button className="secondary-button" onClick={closeSession}>Close QR now</button>}
              </div>
              <div className="checkin-feed">
                <div className="feed-heading"><div><b>Live check-ins</b><small>Refreshes automatically every 3 seconds</small></div><span>{feedCount}</span></div>
                {feedError && <p className="feed-error">{feedError}</p>}
                {feed.length ? (
                  <div className="feed-list">
                    {feed.map((item, index) => (
                      <div className="feed-row" key={item.register_number + item.checked_in_at}>
                        <span className="feed-number">{feedCount - index}</span>
                        <div><b>{item.name}</b><small>{item.register_number}</small></div>
                        <time>{formatTime(item.checked_in_at)}</time>
                      </div>
                    ))}
                  </div>
                ) : <p className="muted empty-feed">No students have checked in yet. Keep this screen open while students scan.</p>}
              </div>
            </div>
          )}
          {session?.expired && <p className="muted">This QR is no longer active. You can still review the check-in list above or generate a new QR.</p>}
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
