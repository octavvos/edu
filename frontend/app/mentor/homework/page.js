"use client";

import { useCallback, useEffect, useState } from "react";
import AppShell from "../../../components/AppShell";
import { Check, Clock, Inbox, X } from "../../../components/Icons";
import { useNotify } from "../../../components/NotificationProvider";
import { errorMessage, mentorApi } from "../../../lib/api";
import { initials, useAuth } from "../../../lib/auth";

/** Backend `SubmissionStatus` bilan mos — H-03 oqimi. */
const STATUS_META = {
  submitted: { label: "Yuborilgan", badge: "info" },
  under_review: { label: "Tekshirilmoqda", badge: "warning" },
  needs_revision: { label: "Qayta ishlashga qaytarildi", badge: "danger" },
  accepted: { label: "Qabul qilindi", badge: "success" },
};

const FILTERS = [
  { value: "", label: "Tekshirilmaganlar" },
  { value: "submitted", label: "Yuborilgan" },
  { value: "under_review", label: "Tekshirilmoqda" },
  { value: "needs_revision", label: "Qayta ishlashda" },
  { value: "accepted", label: "Qabul qilingan" },
];

export default function MentorHomeworkPage() {
  const { user, loading } = useAuth({ roles: ["mentor"] });
  const notify = useNotify();
  const [filter, setFilter] = useState("");
  const [data, setData] = useState({ counts: {}, results: [] });
  const [dataLoading, setDataLoading] = useState(true);
  const [openId, setOpenId] = useState(null);

  const load = useCallback((status) => {
    setDataLoading(true);
    return mentorApi
      .submissions(status ? { status } : {})
      .then(({ data: payload }) => setData(payload))
      .catch((err) => notify({ type: "danger", text: errorMessage(err) }))
      .finally(() => setDataLoading(false));
  }, [notify]);

  useEffect(() => {
    if (!loading) load(filter);
  }, [loading, filter, load]);

  async function handleStatus(submission, status) {
    try {
      await mentorApi.setStatus(submission.id, status);
      notify({
        type: "info",
        text: `${submission.user_name}: ${STATUS_META[status]?.label}`,
      });
      await load(filter);
    } catch (err) {
      notify({ type: "danger", text: errorMessage(err) });
    }
  }

  async function handleGrade(submission, { score, feedback, needsRevision }) {
    try {
      await mentorApi.grade(submission.id, {
        score: Number(score),
        feedback,
        needs_revision: needsRevision,
      });
      notify({
        type: needsRevision ? "warning" : "success",
        text: needsRevision
          ? `${submission.user_name} qayta ishlashga qaytarildi (${score} ball)`
          : `${submission.user_name} qabul qilindi — ${score} ball`,
      });
      setOpenId(null);
      await load(filter);
    } catch (err) {
      notify({ type: "danger", text: errorMessage(err) });
    }
  }

  if (loading) {
    return <div className="app-shell"><main><div className="skeleton" style={{ height: 200 }} /></main></div>;
  }

  const lateCount = data.counts?.late || 0;

  return (
    <AppShell user={user}>
      <div className="page-head">
        <div>
          <h1>Uy vazifalari</h1>
          <p>Topshiriqlarni tekshiring, baho qo&apos;ying va izoh yozing</p>
        </div>
        {lateCount > 0 && (
          <span className="badge badge-danger">
            <Clock width={13} height={13} /> {lateCount} ta kechikkan
          </span>
        )}
      </div>

      <div className="row mb-3" style={{ gap: 8 }}>
        {FILTERS.map((f) => {
          const count = f.value ? data.counts?.[f.value] : undefined;
          return (
            <button
              key={f.value}
              className={`btn btn-sm ${filter === f.value ? "" : "btn-ghost"}`}
              onClick={() => setFilter(f.value)}
            >
              {f.label}
              {count > 0 && (
                <span className="badge badge-neutral" style={{ marginLeft: 4 }}>{count}</span>
              )}
            </button>
          );
        })}
      </div>

      {dataLoading ? (
        <div className="stack">
          <div className="skeleton" style={{ height: 96 }} />
          <div className="skeleton" style={{ height: 96 }} />
        </div>
      ) : data.results.length === 0 ? (
        <div className="card">
          <div className="empty">
            <div className="empty-icon"><Inbox /></div>
            <h3>Topshiriq yo&apos;q</h3>
            <p>Bu bo&apos;limda hozircha tekshiriladigan ish yo&apos;q.</p>
          </div>
        </div>
      ) : (
        <div className="stack">
          {data.results.map((s) => (
            <SubmissionCard
              key={s.id}
              submission={s}
              open={openId === s.id}
              onToggle={() => setOpenId(openId === s.id ? null : s.id)}
              onStatus={handleStatus}
              onGrade={handleGrade}
            />
          ))}
        </div>
      )}
    </AppShell>
  );
}

// ---------------------------------------------------------------------------

function SubmissionCard({ submission, open, onToggle, onStatus, onGrade }) {
  const meta = STATUS_META[submission.status] || { label: submission.status, badge: "neutral" };
  const isAccepted = submission.status === "accepted";

  return (
    <article className="card card-hover fade-in">
      <div className="row-between" style={{ alignItems: "flex-start" }}>
        <div className="row" style={{ gap: 13, flexWrap: "nowrap" }}>
          <div className="avatar">{initials(submission)}</div>
          <div>
            <h3>{submission.user_name}</h3>
            <div className="small muted mt-1">
              @{submission.username} · {submission.lesson_title || "Uy vazifasi"}
            </div>
            <div className="row mt-2" style={{ gap: 7 }}>
              <span className={`badge badge-${meta.badge}`}>{meta.label}</span>
              {submission.is_late && (
                <span className="badge badge-danger">
                  <Clock width={12} height={12} /> Kechikkan
                </span>
              )}
              {submission.grade && (
                <span className="chip">
                  Ball: <strong>{submission.grade.score}</strong> / {submission.max_score || 100}
                </span>
              )}
              <span className="chip">
                {new Date(submission.submitted_at).toLocaleDateString("uz-UZ")}
              </span>
            </div>
          </div>
        </div>

        {!isAccepted && (
          <div className="row" style={{ flexWrap: "nowrap" }}>
            {submission.status === "submitted" && (
              <button
                className="btn btn-ghost btn-sm"
                onClick={() => onStatus(submission, "under_review")}
              >
                Tekshirishni boshlash
              </button>
            )}
            <button className="btn btn-sm" onClick={onToggle}>
              {open ? "Yopish" : "Baholash"}
            </button>
          </div>
        )}
      </div>

      {(submission.text || submission.link || submission.file) && (
        <div className="mt-2" style={{
          padding: "11px 13px", background: "var(--bg-subtle)",
          borderRadius: "var(--radius)", fontSize: 14,
        }}>
          {submission.text && <p>{submission.text}</p>}
          {submission.link && (
            <a href={submission.link} target="_blank" rel="noreferrer" className="small">
              {submission.link}
            </a>
          )}
          {submission.file && (
            <a href={submission.file} target="_blank" rel="noreferrer" className="small">
              Yuklangan fayl
            </a>
          )}
        </div>
      )}

      {submission.grade?.feedback && (
        <p className="small muted mt-2">
          <strong>Izoh:</strong> {submission.grade.feedback}
        </p>
      )}

      {open && !isAccepted && <GradeForm submission={submission} onGrade={onGrade} />}
    </article>
  );
}

// ---------------------------------------------------------------------------

function GradeForm({ submission, onGrade }) {
  const max = submission.max_score || 100;
  const [score, setScore] = useState(submission.grade?.score ?? "");
  const [feedback, setFeedback] = useState(submission.grade?.feedback ?? "");
  const [saving, setSaving] = useState(false);

  async function submit(needsRevision) {
    if (score === "" || Number(score) < 0 || Number(score) > 100) return;
    setSaving(true);
    await onGrade(submission, { score, feedback, needsRevision });
    setSaving(false);
  }

  return (
    <div className="mt-2 fade-in" style={{ borderTop: "1px solid var(--border)", paddingTop: 14 }}>
      <div className="field" style={{ maxWidth: 180 }}>
        <label htmlFor={`score-${submission.id}`}>Ball (0–100)</label>
        <input
          id={`score-${submission.id}`}
          type="number"
          min={0}
          max={100}
          value={score}
          onChange={(e) => setScore(e.target.value)}
          placeholder={`0 – ${max}`}
        />
      </div>

      <div className="field">
        <label htmlFor={`fb-${submission.id}`}>Izoh</label>
        <textarea
          id={`fb-${submission.id}`}
          rows={3}
          value={feedback}
          onChange={(e) => setFeedback(e.target.value)}
          placeholder="O'quvchiga izoh yozing…"
        />
      </div>

      <div className="row">
        <button className="btn btn-success btn-sm" disabled={saving} onClick={() => submit(false)}>
          {saving ? <span className="spinner" /> : <Check width={15} height={15} />}
          Qabul qilish
        </button>
        <button
          className="btn btn-danger-ghost btn-sm"
          disabled={saving}
          onClick={() => submit(true)}
        >
          <X width={15} height={15} />
          Qayta ishlashga qaytarish
        </button>
      </div>
    </div>
  );
}
