"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import AppShell from "../../../../../../components/AppShell";
import { Check, ChevronDown, ChevronLeft, ChevronRight, HelpCircle, X } from "../../../../../../components/Icons";
import { useNotify } from "../../../../../../components/NotificationProvider";
import { errorMessage, mentorApi } from "../../../../../../lib/api";
import { useAuth } from "../../../../../../lib/auth";
import { formatDateTime, formatDuration } from "../../../../../../lib/format";

const STATUS_META = {
  passed: { label: "O'tdi", badge: "success" },
  failed: { label: "O'tmadi", badge: "danger" },
  not_started: { label: "Boshlamagan", badge: "neutral" },
};

/** Bitta o'quvchining shu guruhga yuborilgan har bir testdagi natijasi — savol-javob tahlili bilan. */
export default function StudentResultsPage() {
  const { groupId, studentId } = useParams();
  const { user, loading } = useAuth({ roles: ["mentor"] });
  const notify = useNotify();
  const [student, setStudent] = useState(null);
  const [rows, setRows] = useState([]);
  const [dataLoading, setDataLoading] = useState(true);
  const [openLessonId, setOpenLessonId] = useState(null);

  useEffect(() => {
    if (loading) return;
    Promise.all([mentorApi.quizResultLeaderboard(groupId), mentorApi.quizResultStudent(groupId, studentId)])
      .then(([leaderboardRes, resultsRes]) => {
        setStudent(leaderboardRes.data.find((r) => r.student_id === studentId) || null);
        setRows(resultsRes.data);
      })
      .catch((err) => notify({ type: "danger", text: errorMessage(err) }))
      .finally(() => setDataLoading(false));
  }, [loading, groupId, studentId, notify]);

  if (loading) {
    return <div className="app-shell"><main><div className="skeleton" style={{ height: 200 }} /></main></div>;
  }

  return (
    <AppShell user={user}>
      <Link href={`/mentor/results/${groupId}`} className="row small dim" style={{ gap: 4, textDecoration: "none", marginBottom: 10 }}>
        <ChevronLeft width={14} height={14} /> Reyting
      </Link>

      <div className="page-head">
        <div>
          <h1>{student?.display_name || "O'quvchi natijalari"}</h1>
          <p>{student ? `@${student.username} — har bir testdagi javoblar tahlili` : "Har bir testdagi javoblar tahlili"}</p>
        </div>
      </div>

      {dataLoading ? (
        <div className="stack mt-3">
          <div className="skeleton" style={{ height: 80 }} />
          <div className="skeleton" style={{ height: 80 }} />
        </div>
      ) : rows.length === 0 ? (
        <div className="card mt-3">
          <div className="empty">
            <div className="empty-icon"><HelpCircle /></div>
            <h3>Bu guruhga hali test yuborilmagan</h3>
          </div>
        </div>
      ) : (
        <div className="stack mt-3" style={{ gap: 8 }}>
          {rows.map((row) => (
            <StudentTestRow
              key={row.lesson_id}
              row={row}
              open={openLessonId === row.lesson_id}
              onToggle={() => setOpenLessonId(openLessonId === row.lesson_id ? null : row.lesson_id)}
              groupId={groupId}
              onError={notify}
            />
          ))}
        </div>
      )}
    </AppShell>
  );
}

function StudentTestRow({ row, open, onToggle, groupId, onError }) {
  const meta = STATUS_META[row.status];
  const canExpand = Boolean(row.attempt_id);

  return (
    <div className="card">
      <button
        type="button"
        className="row-between"
        style={{ background: "none", border: "none", cursor: canExpand ? "pointer" : "default", padding: 0, width: "100%", textAlign: "left" }}
        onClick={canExpand ? onToggle : undefined}
      >
        <div className="row" style={{ gap: 9 }}>
          {canExpand ? (
            open ? <ChevronDown width={15} height={15} /> : <ChevronRight width={15} height={15} />
          ) : (
            <HelpCircle width={15} height={15} className="dim" />
          )}
          <div>
            <div className="strong">{row.quiz_title}</div>
            <div className="small dim">{row.module_title}</div>
          </div>
        </div>
        <div className="row" style={{ gap: 18 }}>
          <span className="small dim">{row.attempt_count} urinish</span>
          {row.time_taken_seconds !== null && <span className="small dim">{formatDuration(row.time_taken_seconds)}</span>}
          {row.score_percent !== null && <span className="strong">{row.score_percent}%</span>}
          <span className={`badge badge-${meta.badge}`}>{meta.label}</span>
        </div>
      </button>

      {open && canExpand && <AttemptBreakdown groupId={groupId} attemptId={row.attempt_id} onError={onError} />}
    </div>
  );
}

function optionStyle(choice) {
  if (choice.is_selected && choice.is_correct) {
    return { background: "var(--success-soft)", border: "var(--success)" };
  }
  if (choice.is_selected && !choice.is_correct) {
    return { background: "var(--danger-soft)", border: "var(--danger)" };
  }
  if (!choice.is_selected && choice.is_correct) {
    return { background: "transparent", border: "var(--success)" };
  }
  return { background: "var(--bg-subtle)", border: "transparent" };
}

function AttemptBreakdown({ groupId, attemptId, onError }) {
  const [detail, setDetail] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    mentorApi
      .quizResultAttempt(groupId, attemptId)
      .then(({ data }) => setDetail(data))
      .catch((err) => onError({ type: "danger", text: errorMessage(err, "Tahlilni yuklashda xatolik") }))
      .finally(() => setLoading(false));
  }, [groupId, attemptId, onError]);

  if (loading) return <div className="skeleton mt-3" style={{ height: 100 }} />;
  if (!detail) return null;

  return (
    <div className="stack mt-3" style={{ gap: 8, borderTop: "1px solid var(--border)", paddingTop: 12 }}>
      {detail.answers.map((a, i) => (
        <div key={a.question_id} className="card-compact" style={{ background: "var(--bg-subtle)" }}>
          <div className="row-between" style={{ alignItems: "flex-start" }}>
            <span className="small strong">{i + 1}. {a.question_text}</span>
            {a.is_correct === null ? (
              <span className="badge badge-neutral">Javobsiz</span>
            ) : a.is_correct ? (
              <span className="badge badge-success"><Check width={12} height={12} /> To&apos;g&apos;ri</span>
            ) : (
              <span className="badge badge-danger"><X width={12} height={12} /> Noto&apos;g&apos;ri</span>
            )}
          </div>

          {a.question_type === "short_text" ? (
            <div className="small mt-1">
              <div>
                <span className="dim">Javobi: </span>
                {a.text_answer || <span className="dim">(bo&apos;sh)</span>}
              </div>
              {!a.is_correct && (
                <div>
                  <span className="dim">To&apos;g&apos;ri javob: </span>
                  {a.correct_text_answer}
                </div>
              )}
            </div>
          ) : (
            <div className="stack mt-2" style={{ gap: 5 }}>
              {a.choices.map((c) => {
                const style = optionStyle(c);
                return (
                  <div
                    key={c.id}
                    className="row"
                    style={{
                      gap: 9, padding: "8px 12px", borderRadius: "var(--radius)",
                      background: style.background, border: `1px solid ${style.border}`,
                    }}
                  >
                    <input
                      type={a.question_type === "multiple_choice" ? "checkbox" : "radio"}
                      checked={c.is_selected}
                      readOnly
                      style={{ width: "auto", marginBottom: 0 }}
                    />
                    <span className="small" style={{ flex: 1 }}>{c.text}</span>
                    {c.is_correct && <Check width={14} height={14} style={{ color: "var(--success)" }} />}
                    {c.is_selected && !c.is_correct && <X width={14} height={14} style={{ color: "var(--danger)" }} />}
                  </div>
                );
              })}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
