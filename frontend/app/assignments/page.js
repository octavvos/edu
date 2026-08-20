"use client";

import { useCallback, useEffect, useState } from "react";
import AppShell from "../../components/AppShell";
import {
  Check, Clock, FileText, Inbox, LinkIcon, MessageCircle, Upload,
} from "../../components/Icons";
import { useNotify } from "../../components/NotificationProvider";
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
  const notify = useNotify();
  const [rows, setRows] = useState([]);
  const [dataLoading, setDataLoading] = useState(true);

  const load = useCallback(() => {
    return studentApi
      .myAssignments()
      .then(({ data }) => setRows(data))
      .catch((err) => notify({ type: "danger", text: errorMessage(err) }))
      .finally(() => setDataLoading(false));
  }, [notify]);

  useEffect(() => {
    if (!loading) load();
  }, [loading, load]);

  if (loading) {
    return <div className="app-shell"><main><div className="skeleton" style={{ height: 200 }} /></main></div>;
  }

  const total = rows.length;
  const accepted = rows.filter((r) => r.submission?.status === "accepted").length;
  const pending = total - accepted;
  const scores = rows.filter((r) => r.submission?.grade).map((r) => r.submission.grade.score);
  const avgScore = scores.length ? Math.round(scores.reduce((a, b) => a + b, 0) / scores.length) : null;

  return (
    <AppShell user={user}>
      <div className="page-head">
        <div>
          <h1>Topshiriqlarim</h1>
          <p>Mentoringiz tomonidan yuborilgan vazifalar</p>
        </div>
      </div>

      {!dataLoading && total > 0 && (
        <div className="stats mb-3">
          <div className="stat">
            <div className="stat-label">Jami vazifa</div>
            <div className="stat-value">{total}</div>
          </div>
          <div className="stat">
            <div className="stat-label">Qabul qilingan</div>
            <div className="stat-value" style={{ color: accepted ? "var(--success)" : undefined }}>
              {accepted}
            </div>
          </div>
          <div className="stat">
            <div className="stat-label">Kutilmoqda</div>
            <div className="stat-value" style={{ color: pending ? "var(--warning)" : undefined }}>
              {pending}
            </div>
          </div>
          <div className="stat">
            <div className="stat-label">O&apos;rtacha ball</div>
            <div className="stat-value">{avgScore === null ? "—" : avgScore}</div>
          </div>
        </div>
      )}

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
            <AssignmentCard key={row.id} row={row} onChanged={load} onError={notify} />
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

  const rail =
    submission?.status === "accepted" ? "rail-card-success" :
    submission?.status === "needs_revision" ? "rail-card-warning" :
    overdue ? "rail-card-danger" :
    submission ? "rail-card-info" : "";

  return (
    <article className={`card card-hover rail-card ${rail} fade-in`} style={{ paddingLeft: 22 }}>
      <div className="row-between" style={{ alignItems: "flex-start", gap: 14 }}>
        <div style={{ minWidth: 0 }}>
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
            <div className="row mt-1" style={{ gap: 5 }}>
              <Clock width={12} height={12} className="dim" />
              <span className="small dim">
                Muddat: {new Date(row.deadline_at).toLocaleString("uz-UZ")}
              </span>
            </div>
          )}
        </div>

        {submission?.grade && (
          <div className="score-badge">
            <span className="score-badge-value">{submission.grade.score}</span>
            <span className="score-badge-max">/ {row.max_score}</span>
          </div>
        )}
      </div>

      <p className="mt-2" style={{ color: "var(--text-secondary)", lineHeight: 1.55 }}>
        {row.instructions}
      </p>

      {(row.material || row.presentation) && (
        <div className="row mt-2" style={{ gap: 8 }}>
          {row.material && (
            <a href={row.material.file} target="_blank" rel="noreferrer" className="pill-link">
              <FileText width={13} height={13} />
              <span>{row.material.title || row.material.original_filename}</span>
            </a>
          )}
          {row.presentation && (
            <a href={row.presentation.file} target="_blank" rel="noreferrer" className="pill-link">
              <FileText width={13} height={13} />
              <span>{row.presentation.title || row.presentation.original_filename}</span>
            </a>
          )}
        </div>
      )}

      {submission && (submission.file || submission.link || submission.text) && (
        <div className="mt-2 card-compact" style={{ background: "var(--bg-subtle)", border: "none", boxShadow: "none" }}>
          <div className="stat-label mb-1">
            Topshirganingiz · {new Date(submission.submitted_at).toLocaleString("uz-UZ")}
          </div>
          {submission.text && (
            <p className="small" style={{ color: "var(--text-secondary)", marginBottom: 8 }}>
              {submission.text}
            </p>
          )}
          <div className="row" style={{ gap: 8 }}>
            {submission.file && (
              <a href={submission.file} target="_blank" rel="noreferrer" className="pill-link">
                <FileText width={13} height={13} />
                <span>Yuklangan fayl</span>
              </a>
            )}
            {submission.link && (
              <a href={submission.link} target="_blank" rel="noreferrer" className="pill-link">
                <LinkIcon width={13} height={13} />
                <span>{submission.link.replace(/^https?:\/\//, "")}</span>
              </a>
            )}
          </div>
        </div>
      )}

      {submission?.grade?.feedback && (
        <div className="feedback-box mt-2">
          <MessageCircle width={16} height={16} className="feedback-box-icon" />
          <div>
            <div className="feedback-box-label">Mentor izohi</div>
            <p>{submission.grade.feedback}</p>
          </div>
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
  const [dragOver, setDragOver] = useState(false);
  const [saving, setSaving] = useState(false);

  function pickFile(f) {
    if (f) setFile(f);
  }

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
    <form onSubmit={submit} className="mt-3" style={{ borderTop: "1px solid var(--border)", paddingTop: 14 }}>
      <div
        className={`dropzone ${dragOver ? "dropzone-active" : ""}`}
        onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
        onDragLeave={() => setDragOver(false)}
        onDrop={(e) => { e.preventDefault(); setDragOver(false); pickFile(e.dataTransfer.files?.[0]); }}
      >
        <div className="dropzone-icon"><Upload width={16} height={16} /></div>
        {file ? (
          <p className="small strong" style={{ margin: 0 }}>{file.name}</p>
        ) : (
          <p className="small muted" style={{ margin: 0 }}>ZIP yoki PDF faylni shu yerga tashlang</p>
        )}
        <label className="btn btn-ghost btn-sm mt-2" style={{ cursor: "pointer" }}>
          {file ? "Boshqa fayl tanlash" : "Fayl tanlash"}
          <input
            type="file"
            accept=".zip,.pdf"
            onChange={(e) => { pickFile(e.target.files?.[0]); e.target.value = ""; }}
            style={{ display: "none" }}
          />
        </label>
      </div>

      <div className="field-row mt-2">
        <div className="field" style={{ marginBottom: 0 }}>
          <label>GitHub havolasi (ixtiyoriy)</label>
          <input
            type="url"
            value={link}
            onChange={(e) => setLink(e.target.value)}
            placeholder="https://github.com/..."
          />
        </div>
        <div className="field" style={{ marginBottom: 0 }}>
          <label>Izoh (ixtiyoriy)</label>
          <input
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="Qo'shimcha izoh…"
          />
        </div>
      </div>

      <button className="btn btn-sm mt-2" type="submit" disabled={saving}>
        {saving ? <span className="spinner" /> : <Check width={14} height={14} />}
        {submission ? "Qayta yuborish" : "Topshirish"}
      </button>
    </form>
  );
}
