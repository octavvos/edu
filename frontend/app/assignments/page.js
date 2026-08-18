"use client";

import { useCallback, useEffect, useState } from "react";
import AppShell from "../../components/AppShell";
import { Clock, FileText, Inbox, Upload } from "../../components/Icons";
import { errorMessage, studentApi } from "../../lib/api";
import { useAuth } from "../../lib/auth";

const STATUS_META = {
  submitted: { label: "Yuborilgan", badge: "info" },
  under_review: { label: "Tekshirilmoqda", badge: "warning" },
  needs_revision: { label: "Qayta ishlashga qaytarildi", badge: "danger" },
  accepted: { label: "Qabul qilindi", badge: "success" },
};

/** O'quvchiga mentor tomonidan yuborilgan vazifalar — topshirish va baho/izohni ko'rish. */
export default function AssignmentsPage() {
  const { user, loading } = useAuth();
  const [rows, setRows] = useState([]);
  const [dataLoading, setDataLoading] = useState(true);
  const [message, setMessage] = useState(null);

  const load = useCallback(() => {
    return studentApi
      .myAssignments()
      .then(({ data }) => setRows(data))
      .catch((err) => setMessage({ type: "danger", text: errorMessage(err) }))
      .finally(() => setDataLoading(false));
  }, []);

  useEffect(() => {
    if (!loading) load();
  }, [loading, load]);

  if (loading) {
    return <div className="app-shell"><main><div className="skeleton" style={{ height: 200 }} /></main></div>;
  }

  return (
    <AppShell user={user}>
      <div className="page-head">
        <div>
          <h1>Vazifalarim</h1>
          <p>Mentoringiz tomonidan yuborilgan vazifalar</p>
        </div>
      </div>

      {message && <div className={`alert alert-${message.type}`}>{message.text}</div>}

      {dataLoading ? (
        <div className="stack">
          <div className="skeleton" style={{ height: 150 }} />
          <div className="skeleton" style={{ height: 150 }} />
        </div>
      ) : rows.length === 0 ? (
        <div className="card">
          <div className="empty">
            <div className="empty-icon"><Inbox /></div>
            <h3>Hozircha vazifa yo&apos;q</h3>
            <p>Mentoringiz vazifa yuborgach shu yerda ko&apos;rinadi.</p>
          </div>
        </div>
      ) : (
        <div className="stack">
          {rows.map((row) => (
            <AssignmentCard key={row.id} row={row} onChanged={load} onError={setMessage} />
          ))}
        </div>
      )}
    </AppShell>
  );
}

// ---------------------------------------------------------------------------

function AssignmentCard({ row, onChanged, onError }) {
  const submission = row.submission;
  const meta = submission ? STATUS_META[submission.status] : null;
  const isAccepted = submission?.status === "accepted";
  const overdue = row.deadline_at && !isAccepted && new Date(row.deadline_at) < new Date();

  return (
    <article className="card fade-in">
      <div className="row-between" style={{ alignItems: "flex-start" }}>
        <div>
          <div className="row" style={{ gap: 7 }}>
            <h3 style={{ margin: 0 }}>{row.lesson_title}</h3>
            {meta && <span className={`badge badge-${meta.badge}`}>{meta.label}</span>}
            {overdue && (
              <span className="badge badge-danger">
                <Clock width={12} height={12} /> Muddati o&apos;tgan
              </span>
            )}
          </div>
          {row.deadline_at && (
            <p className="small muted mt-1">
              Muddat: {new Date(row.deadline_at).toLocaleString("uz-UZ")}
            </p>
          )}
        </div>
        {submission?.grade && (
          <span className="chip">
            Ball: <strong>{submission.grade.score}</strong> / {row.max_score}
          </span>
        )}
      </div>

      <p className="mt-2">{row.instructions}</p>

      {row.material && (
        <a
          href={row.material.file}
          target="_blank"
          rel="noreferrer"
          className="row small mt-2"
          style={{ gap: 6 }}
        >
          <FileText width={14} height={14} />
          {row.material.title || row.material.original_filename}
        </a>
      )}

      {submission && (submission.file || submission.link || submission.text) && (
        <div className="mt-2" style={{
          padding: "11px 13px", background: "var(--bg-subtle)",
          borderRadius: "var(--radius)", fontSize: 14,
        }}>
          <div className="stat-label mb-1">
            Topshirganingiz · {new Date(submission.submitted_at).toLocaleString("uz-UZ")}
          </div>
          {submission.text && <p>{submission.text}</p>}
          <div className="row" style={{ gap: 12 }}>
            {submission.file && (
              <a href={submission.file} target="_blank" rel="noreferrer" className="small">
                Yuklangan fayl
              </a>
            )}
            {submission.link && (
              <a href={submission.link} target="_blank" rel="noreferrer" className="small">
                {submission.link}
              </a>
            )}
          </div>
        </div>
      )}

      {submission?.grade?.feedback && (
        <div className="alert alert-info mt-2" style={{ marginBottom: 0 }}>
          <strong>Mentor izohi:</strong> {submission.grade.feedback}
        </div>
      )}

      {!isAccepted && (
        <SubmitForm lessonId={row.lesson} submission={submission} onChanged={onChanged} onError={onError} />
      )}
    </article>
  );
}

function SubmitForm({ lessonId, submission, onChanged, onError }) {
  const [file, setFile] = useState(null);
  const [link, setLink] = useState(submission?.link || "");
  const [text, setText] = useState(submission?.text || "");
  const [saving, setSaving] = useState(false);

  async function submit(e) {
    e.preventDefault();
    if (!file && !text.trim() && !link.trim()) {
      onError({ type: "danger", text: "Fayl, matn yoki havoladan kamida bittasini kiriting" });
      return;
    }
    setSaving(true);
    try {
      await studentApi.submitAssignment(lessonId, { file, text, link });
      setFile(null);
      onChanged();
    } catch (err) {
      onError({ type: "danger", text: errorMessage(err, "Yuborishda xatolik") });
    } finally {
      setSaving(false);
    }
  }

  return (
    <form onSubmit={submit} className="mt-3" style={{ borderTop: "1px solid var(--border)", paddingTop: 12 }}>
      <div className="field">
        <label>Fayl (ZIP yoki PDF)</label>
        <input type="file" accept=".zip,.pdf" onChange={(e) => setFile(e.target.files?.[0] || null)} />
      </div>
      <div className="field">
        <label>GitHub havolasi (ixtiyoriy)</label>
        <input
          type="url"
          value={link}
          onChange={(e) => setLink(e.target.value)}
          placeholder="https://github.com/..."
        />
      </div>
      <div className="field">
        <label>Izoh (ixtiyoriy)</label>
        <textarea
          rows={2}
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="Qo'shimcha izoh…"
        />
      </div>
      <button className="btn btn-sm" type="submit" disabled={saving}>
        {saving && <span className="spinner" />}
        <Upload width={14} height={14} />
        {submission ? "Qayta yuborish" : "Topshirish"}
      </button>
    </form>
  );
}
