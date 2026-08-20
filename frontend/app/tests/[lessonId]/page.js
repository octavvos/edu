"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import AppShell from "../../../components/AppShell";
import { Check, ChevronLeft, Clock, HelpCircle, Trophy, X } from "../../../components/Icons";
import { useNotify } from "../../../components/NotificationProvider";
import { assessmentsApi, errorMessage } from "../../../lib/api";
import { useAuth } from "../../../lib/auth";

const CHOICE_TYPES = new Set(["single_choice", "true_false"]);

/** O'quvchi uchun bitta testni topshirish sahifasi: kirish -> yechish -> natija. */
export default function TakeTestPage() {
  const { lessonId } = useParams();
  const router = useRouter();
  const { user, loading } = useAuth();
  const notify = useNotify();

  const [phase, setPhase] = useState("loading"); // loading | intro | taking | result
  const [info, setInfo] = useState(null); // /assessments/mine/ dagi shu testga oid yozuv
  const [attempt, setAttempt] = useState(null);
  const [questions, setQuestions] = useState([]);
  const [answers, setAnswers] = useState({}); // questionId -> { selected_choice_ids, text_answer }
  const [starting, setStarting] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState(null);
  const attemptRef = useRef(null);

  const loadInfo = useCallback(async () => {
    const { data } = await assessmentsApi.mine();
    const row = data.find((t) => t.lesson_id === lessonId);
    if (!row) {
      notify({ type: "danger", text: "Test topilmadi" });
      router.replace("/tests");
      return null;
    }
    // Oldingi tugallanmagan urinish bo'lsa — jim tarzda yakunlab, holatni tozalaymiz
    if (row.has_in_progress && row.in_progress_attempt_id) {
      await assessmentsApi.submit(row.in_progress_attempt_id).catch(() => {});
      const refreshed = await assessmentsApi.mine();
      const fresh = refreshed.data.find((t) => t.lesson_id === lessonId);
      setInfo(fresh || row);
      return fresh || row;
    }
    setInfo(row);
    return row;
  }, [lessonId, notify, router]);

  useEffect(() => {
    if (loading) return;
    loadInfo()
      .then(() => setPhase("intro"))
      .catch((err) => notify({ type: "danger", text: errorMessage(err) }));
  }, [loading, loadInfo, notify]);

  // Sahifadan tasodifan chiqib ketishning oldini olish (urinish boshlangandan keyin)
  useEffect(() => {
    function onBeforeUnload(e) {
      if (phase === "taking") {
        e.preventDefault();
        e.returnValue = "";
      }
    }
    window.addEventListener("beforeunload", onBeforeUnload);
    return () => window.removeEventListener("beforeunload", onBeforeUnload);
  }, [phase]);

  // Komponent tark etilganda (ilova ichida navigatsiya) tugallanmagan urinishni yopamiz
  useEffect(() => {
    attemptRef.current = phase === "taking" ? attempt : null;
    return () => {
      if (attemptRef.current) {
        assessmentsApi.submit(attemptRef.current.id).catch(() => {});
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [phase, attempt]);

  async function handleStart() {
    setStarting(true);
    try {
      const { data } = await assessmentsApi.start(lessonId);
      setAttempt(data.attempt);
      setQuestions(data.questions);
      setAnswers({});
      setPhase("taking");
    } catch (err) {
      notify({ type: "danger", text: errorMessage(err, "Testni boshlashda xatolik") });
    } finally {
      setStarting(false);
    }
  }

  function updateAnswer(questionId, value) {
    setAnswers((prev) => ({ ...prev, [questionId]: value }));
    assessmentsApi.answer(attempt.id, { question_id: questionId, ...value }).catch((err) => {
      notify({ type: "danger", text: errorMessage(err, "Javobni saqlashda xatolik") });
    });
  }

  const handleSubmit = useCallback(async () => {
    if (!attempt) return;
    setSubmitting(true);
    attemptRef.current = null; // unmount-cleanup qayta yubormasin — o'zimiz yakunlaymiz
    try {
      const { data } = await assessmentsApi.submit(attempt.id);
      setResult(data);
      setPhase("result");
    } catch (err) {
      notify({ type: "danger", text: errorMessage(err, "Yakunlashda xatolik") });
    } finally {
      setSubmitting(false);
    }
  }, [attempt, notify]);

  function confirmSubmit() {
    const answered = Object.keys(answers).length;
    if (answered < questions.length) {
      const rest = questions.length - answered;
      if (!window.confirm(`${rest} ta savolga javob bermadingiz. Baribir yakunlansinmi?`)) return;
    }
    handleSubmit();
  }

  if (loading || phase === "loading") {
    return <div className="app-shell"><main><div className="skeleton" style={{ height: 240 }} /></main></div>;
  }

  return (
    <AppShell user={user}>
      <div className="row small mb-2" style={{ gap: 6 }}>
        <Link href="/tests" className="muted row" style={{ gap: 4 }}>
          <ChevronLeft width={13} height={13} /> Testlarim
        </Link>
      </div>

      {phase === "intro" && info && (
        <IntroCard info={info} starting={starting} onStart={handleStart} />
      )}

      {phase === "taking" && attempt && (
        <QuizForm
          attempt={attempt}
          questions={questions}
          answers={answers}
          onAnswer={updateAnswer}
          onSubmit={confirmSubmit}
          onExpire={handleSubmit}
          submitting={submitting}
        />
      )}

      {phase === "result" && result && (
        <ResultCard result={result} info={info} />
      )}
    </AppShell>
  );
}

// ---------------------------------------------------------------------------

function IntroCard({ info, starting, onStart }) {
  const minutes = info.time_limit_seconds ? Math.round(info.time_limit_seconds / 60) : null;
  const attemptsLeft = info.max_attempts - info.attempt_count;
  const canStart = attemptsLeft > 0;

  return (
    <div className="card fade-in">
      <div className="row" style={{ gap: 10 }}>
        <div className="empty-icon" style={{ width: 48, height: 48 }}><HelpCircle width={22} height={22} /></div>
        <div>
          <h2 style={{ margin: 0 }}>{info.title}</h2>
          <div className="small dim">{info.module_title} · {info.course_title}</div>
        </div>
      </div>

      <div className="stats mt-3">
        <div className="stat">
          <div className="stat-label">Savollar</div>
          <div className="stat-value">{info.question_count}</div>
        </div>
        {minutes && (
          <div className="stat">
            <div className="stat-label">Vaqt</div>
            <div className="stat-value">{minutes} <span style={{ fontSize: 14, fontWeight: 500 }}>daqiqa</span></div>
          </div>
        )}
        <div className="stat">
          <div className="stat-label">O&apos;tish balli</div>
          <div className="stat-value">{info.pass_percent}%</div>
        </div>
        <div className="stat">
          <div className="stat-label">Urinishlar</div>
          <div className="stat-value" style={{ color: canStart ? undefined : "var(--danger)" }}>
            {info.attempt_count}/{info.max_attempts}
          </div>
        </div>
      </div>

      {info.best_score !== null && (
        <div className="feedback-box mt-3">
          <Trophy width={16} height={16} className="feedback-box-icon" />
          <div>
            <div className="feedback-box-label">Eng yaxshi natijangiz</div>
            <p>{info.best_score}% {info.passed ? "— o'tdingiz" : "— o'tish balliga yetmadi"}</p>
          </div>
        </div>
      )}

      <div className="mt-3">
        {canStart ? (
          <button className="btn" onClick={onStart} disabled={starting}>
            {starting && <span className="spinner" />}
            {info.attempt_count > 0 ? "Qayta urinish" : "Testni boshlash"}
          </button>
        ) : (
          <p className="small dim">Urinishlar soni tugadi.</p>
        )}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------

function QuizForm({ attempt, questions, answers, onAnswer, onSubmit, onExpire, submitting }) {
  const answeredCount = Object.keys(answers).length;

  return (
    <div className="fade-in">
      <div className="card mb-3" style={{ position: "sticky", top: 12, zIndex: 5 }}>
        <div className="row-between">
          <span className="small strong">Javob berildi: {answeredCount}/{questions.length}</span>
          {attempt.expires_at && <Countdown expiresAt={attempt.expires_at} onExpire={onExpire} />}
        </div>
      </div>

      <div className="stack">
        {questions.map((q, i) => (
          <QuestionCard
            key={q.id}
            index={i + 1}
            question={q}
            value={answers[q.id]}
            onChange={(value) => onAnswer(q.id, value)}
          />
        ))}
      </div>

      <div className="row mt-3" style={{ justifyContent: "flex-end" }}>
        <button className="btn" onClick={onSubmit} disabled={submitting}>
          {submitting ? <span className="spinner" /> : <Check width={15} height={15} />}
          Yakunlash
        </button>
      </div>
    </div>
  );
}

function QuestionCard({ index, question, value, onChange }) {
  const isMulti = question.type === "multiple_choice";
  const selected = value?.selected_choice_ids || [];

  function toggleChoice(choiceId) {
    if (isMulti) {
      const next = selected.includes(choiceId)
        ? selected.filter((id) => id !== choiceId)
        : [...selected, choiceId];
      onChange({ selected_choice_ids: next, text_answer: "" });
    } else {
      onChange({ selected_choice_ids: [choiceId], text_answer: "" });
    }
  }

  return (
    <div className="card">
      <div className="row" style={{ gap: 8, alignItems: "flex-start" }}>
        <span className="chip" style={{ flexShrink: 0 }}>{index}</span>
        <p className="strong" style={{ margin: 0 }}>{question.text}</p>
      </div>

      {CHOICE_TYPES.has(question.type) || isMulti ? (
        <div className="stack mt-2" style={{ gap: 6 }}>
          {question.choices.map((c) => (
            <label
              key={c.id}
              className="row"
              style={{
                gap: 9, padding: "9px 12px", borderRadius: "var(--radius)",
                background: selected.includes(c.id) ? "var(--primary-soft)" : "var(--bg-subtle)",
                cursor: "pointer", flexWrap: "nowrap",
              }}
            >
              <input
                type={isMulti ? "checkbox" : "radio"}
                name={question.id}
                checked={selected.includes(c.id)}
                onChange={() => toggleChoice(c.id)}
                style={{ width: "auto", marginBottom: 0 }}
              />
              <span className="small">{c.text}</span>
            </label>
          ))}
        </div>
      ) : (
        <input
          className="mt-2"
          value={value?.text_answer || ""}
          onChange={(e) => onChange({ selected_choice_ids: [], text_answer: e.target.value })}
          placeholder="Javobingizni yozing…"
          style={{ marginBottom: 0 }}
        />
      )}
    </div>
  );
}

function Countdown({ expiresAt, onExpire }) {
  const target = useMemo(() => new Date(expiresAt).getTime(), [expiresAt]);
  const [remaining, setRemaining] = useState(() => Math.max(0, target - Date.now()));
  const firedRef = useRef(false);

  useEffect(() => {
    const id = setInterval(() => {
      const left = Math.max(0, target - Date.now());
      setRemaining(left);
      if (left <= 0 && !firedRef.current) {
        firedRef.current = true;
        clearInterval(id);
        onExpire();
      }
    }, 1000);
    return () => clearInterval(id);
  }, [target, onExpire]);

  const totalSec = Math.floor(remaining / 1000);
  const mm = String(Math.floor(totalSec / 60)).padStart(2, "0");
  const ss = String(totalSec % 60).padStart(2, "0");
  const low = totalSec <= 60;

  return (
    <span className={`badge badge-${low ? "danger" : "warning"}`}>
      <Clock width={12} height={12} /> {mm}:{ss}
    </span>
  );
}

// ---------------------------------------------------------------------------

function ResultCard({ result, info }) {
  const passed = result.passed;
  return (
    <div className={`card rail-card ${passed ? "rail-card-success" : "rail-card-danger"} fade-in`} style={{ paddingLeft: 22 }}>
      <div className="row" style={{ gap: 12 }}>
        <div className="empty-icon" style={{ width: 52, height: 52 }}>
          {passed ? <Trophy width={24} height={24} /> : <X width={24} height={24} />}
        </div>
        <div>
          <h2 style={{ margin: 0 }}>{passed ? "Tabriklaymiz, o'tdingiz!" : "O'tish balliga yetmadingiz"}</h2>
          {result.score_percent !== undefined && (
            <p className="dim" style={{ margin: "4px 0 0" }}>
              Natija: <strong>{result.score_percent}%</strong> (o&apos;tish balli: {info?.pass_percent}%)
            </p>
          )}
        </div>
      </div>
      <div className="row mt-3">
        <Link href="/tests" className="btn btn-ghost btn-sm">
          <ChevronLeft width={14} height={14} /> Testlarimga qaytish
        </Link>
      </div>
    </div>
  );
}
