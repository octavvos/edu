"use client";

import { useCallback, useEffect, useState } from "react";
import { Check, Plus, X } from "../Icons";
import { errorMessage, mentorApi } from "../../lib/api";

export const QUESTION_TYPES = [
  { value: "single_choice", label: "Bitta to'g'ri javob" },
  { value: "multiple_choice", label: "Bir nechta to'g'ri javob" },
  { value: "true_false", label: "To'g'ri / noto'g'ri" },
  { value: "short_text", label: "Qisqa matnli javob" },
];

/** Bitta testning sozlamalari va savollari — Testlar bo'limida ishlatiladi. */
export default function QuizBuilder({ quizId, onError }) {
  const [quiz, setQuiz] = useState(null);
  const [questions, setQuestions] = useState([]);
  const [loadingData, setLoadingData] = useState(true);
  const [addingQuestion, setAddingQuestion] = useState(false);
  const [editingId, setEditingId] = useState(null);

  const load = useCallback(() => {
    setLoadingData(true);
    return Promise.all([mentorApi.quizDetail(quizId), mentorApi.quizQuestions(quizId)])
      .then(([q, qs]) => { setQuiz(q.data); setQuestions(qs.data); })
      .catch((err) => onError({ type: "danger", text: errorMessage(err) }))
      .finally(() => setLoadingData(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [quizId]);

  useEffect(() => { load(); }, [load]);

  async function handleDelete(question) {
    if (!window.confirm(`"${question.text}" savoli o'chirilsinmi?`)) return;
    try {
      await mentorApi.deleteQuestion(question.id);
      await load();
    } catch (err) {
      onError({ type: "danger", text: errorMessage(err) });
    }
  }

  return (
    <div className="mt-2 fade-in" style={{ borderTop: "1px solid var(--border)", paddingTop: 12 }}>
      {loadingData ? (
        <div className="skeleton" style={{ height: 80 }} />
      ) : (
        <>
          <QuizSettingsForm
            quiz={quiz}
            onSaved={async (settings) => {
              try {
                await mentorApi.updateQuiz(quizId, settings);
                await load();
              } catch (err) {
                onError({ type: "danger", text: errorMessage(err) });
              }
            }}
          />

          <div className="row-between mt-2 mb-2">
            <span className="stat-label">Savollar ({questions.length})</span>
            <button className="btn btn-ghost btn-sm" onClick={() => setAddingQuestion((v) => !v)}>
              {addingQuestion ? <X width={13} height={13} /> : <Plus width={13} height={13} />}
              Savol qo&apos;shish
            </button>
          </div>

          {addingQuestion && (
            <QuestionForm
              onSubmit={async (payload) => {
                try {
                  await mentorApi.addQuestion(quizId, payload);
                  setAddingQuestion(false);
                  await load();
                } catch (err) {
                  onError({ type: "danger", text: errorMessage(err) });
                }
              }}
              onCancel={() => setAddingQuestion(false)}
            />
          )}

          {questions.length === 0 ? (
            <p className="small dim">Hali savol yo&apos;q.</p>
          ) : (
            <div className="stack" style={{ gap: 8 }}>
              {questions.map((q) => (
                <div key={q.id} style={{
                  background: "var(--bg-subtle)", borderRadius: "var(--radius)", padding: 11,
                }}>
                  {editingId === q.id ? (
                    <QuestionForm
                      initial={q}
                      onSubmit={async (payload) => {
                        try {
                          await mentorApi.updateQuestion(q.id, payload);
                          setEditingId(null);
                          await load();
                        } catch (err) {
                          onError({ type: "danger", text: errorMessage(err) });
                        }
                      }}
                      onCancel={() => setEditingId(null)}
                    />
                  ) : (
                    <div className="row-between" style={{ alignItems: "flex-start" }}>
                      <div>
                        <div className="row" style={{ gap: 7 }}>
                          <span className="badge badge-info">{questionTypeLabel(q.type)}</span>
                          <span className="chip">{q.points} ball</span>
                        </div>
                        <p className="small strong mt-1">{q.text}</p>
                        {q.choices?.length > 0 && (
                          <ul className="small muted" style={{ margin: "6px 0 0", paddingLeft: 18 }}>
                            {q.choices.map((c) => (
                              <li key={c.id} style={{ color: c.is_correct ? "var(--success)" : undefined }}>
                                {c.is_correct && <Check width={11} height={11} style={{ marginRight: 3 }} />}
                                {c.text}
                              </li>
                            ))}
                          </ul>
                        )}
                        {q.type === "short_text" && (
                          <p className="small dim mt-1">To&apos;g&apos;ri javob: {q.correct_text_pattern}</p>
                        )}
                      </div>
                      <div className="row" style={{ flexWrap: "nowrap" }}>
                        <button className="btn btn-ghost btn-sm" onClick={() => setEditingId(q.id)}>
                          Tahrirlash
                        </button>
                        <button className="btn btn-danger-ghost btn-sm" onClick={() => handleDelete(q)}>
                          <X width={13} height={13} />
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
}

function questionTypeLabel(type) {
  return QUESTION_TYPES.find((t) => t.value === type)?.label || type;
}

function QuizSettingsForm({ quiz, onSaved }) {
  const [form, setForm] = useState({
    pass_percent: quiz.pass_percent,
    max_attempts: quiz.max_attempts,
    time_limit_seconds: quiz.time_limit_seconds || "",
  });
  const [saving, setSaving] = useState(false);
  const [dirty, setDirty] = useState(false);

  function update(key, value) {
    setForm((prev) => ({ ...prev, [key]: value }));
    setDirty(true);
  }

  async function save() {
    setSaving(true);
    await onSaved({
      pass_percent: Number(form.pass_percent),
      max_attempts: Number(form.max_attempts),
      time_limit_seconds: form.time_limit_seconds ? Number(form.time_limit_seconds) : null,
    });
    setSaving(false);
    setDirty(false);
  }

  return (
    <div className="row" style={{ gap: 14, flexWrap: "wrap", alignItems: "flex-end" }}>
      <div className="field" style={{ marginBottom: 0, width: 130 }}>
        <label>O&apos;tish balli (%)</label>
        <input type="number" min={1} max={100} value={form.pass_percent}
          onChange={(e) => update("pass_percent", e.target.value)} />
      </div>
      <div className="field" style={{ marginBottom: 0, width: 130 }}>
        <label>Urinishlar soni</label>
        <input type="number" min={1} value={form.max_attempts}
          onChange={(e) => update("max_attempts", e.target.value)} />
      </div>
      <div className="field" style={{ marginBottom: 0, width: 160 }}>
        <label>Vaqt chegarasi (soniya)</label>
        <input type="number" min={0} placeholder="cheksiz" value={form.time_limit_seconds}
          onChange={(e) => update("time_limit_seconds", e.target.value)} />
      </div>
      {dirty && (
        <button className="btn btn-sm" onClick={save} disabled={saving}>
          {saving && <span className="spinner" />} Saqlash
        </button>
      )}
    </div>
  );
}

function QuestionForm({ initial, onSubmit, onCancel }) {
  const isChoiceType = (t) => ["single_choice", "multiple_choice", "true_false"].includes(t);

  const [type, setType] = useState(initial?.type || "single_choice");
  const [text, setText] = useState(initial?.text || "");
  const [points, setPoints] = useState(initial?.points || 1);
  const [pattern, setPattern] = useState(initial?.correct_text_pattern || "");
  const [choices, setChoices] = useState(
    initial?.choices?.length
      ? initial.choices.map((c) => ({ text: c.text, is_correct: c.is_correct }))
      : type === "true_false"
        ? [{ text: "To'g'ri", is_correct: true }, { text: "Noto'g'ri", is_correct: false }]
        : [{ text: "", is_correct: true }, { text: "", is_correct: false }],
  );
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  function changeType(newType) {
    setType(newType);
    if (newType === "true_false") {
      setChoices([{ text: "To'g'ri", is_correct: true }, { text: "Noto'g'ri", is_correct: false }]);
    } else if (isChoiceType(newType) && choices.length < 2) {
      setChoices([{ text: "", is_correct: true }, { text: "", is_correct: false }]);
    }
  }

  function updateChoice(i, key, value) {
    setChoices((prev) => prev.map((c, idx) => {
      if (idx !== i) {
        return key === "is_correct" && value && type === "single_choice"
          ? { ...c, is_correct: false }
          : c;
      }
      return { ...c, [key]: value };
    }));
  }

  async function submit(e) {
    e.preventDefault();
    setError("");
    if (!text.trim()) { setError("Savol matnini kiriting"); return; }
    if (type === "short_text" && !pattern.trim()) { setError("To'g'ri javob namunasini kiriting"); return; }

    const payload = {
      type, text: { uz: text.trim() }, points: Number(points),
      correct_text_pattern: pattern.trim(), is_regex: false,
      choices: isChoiceType(type) ? choices.map((c) => ({ text: { uz: c.text.trim() }, is_correct: c.is_correct })) : [],
    };

    setSaving(true);
    try {
      await onSubmit(payload);
    } finally {
      setSaving(false);
    }
  }

  return (
    <form className="card mb-2 fade-in" style={{ background: "var(--bg-elevated)" }} onSubmit={submit}>
      {error && <div className="alert alert-danger">{error}</div>}

      <div className="row" style={{ gap: 10 }}>
        <div className="field" style={{ flex: "0 1 220px" }}>
          <label>Savol turi</label>
          <select value={type} onChange={(e) => changeType(e.target.value)} disabled={Boolean(initial)}>
            {QUESTION_TYPES.map((t) => <option key={t.value} value={t.value}>{t.label}</option>)}
          </select>
        </div>
        <div className="field" style={{ flex: "0 1 100px" }}>
          <label>Ball</label>
          <input type="number" min={1} value={points} onChange={(e) => setPoints(e.target.value)} />
        </div>
      </div>

      <div className="field">
        <label>Savol matni</label>
        <input value={text} onChange={(e) => setText(e.target.value)} placeholder="Savolni yozing…" autoFocus />
      </div>

      {isChoiceType(type) ? (
        <div className="field">
          <label>Variantlar {type === "single_choice" || type === "true_false" ? "(bitta to'g'ri)" : "(kamida bitta to'g'ri)"}</label>
          <div className="stack" style={{ gap: 6 }}>
            {choices.map((c, i) => (
              <div key={i} className="row" style={{ gap: 8, flexWrap: "nowrap" }}>
                <input
                  type={type === "single_choice" || type === "true_false" ? "radio" : "checkbox"}
                  name="correct"
                  checked={c.is_correct}
                  onChange={(e) => updateChoice(i, "is_correct", e.target.checked)}
                  style={{ width: "auto" }}
                />
                <input
                  value={c.text}
                  onChange={(e) => updateChoice(i, "text", e.target.value)}
                  placeholder={`Variant ${i + 1}`}
                  disabled={type === "true_false"}
                  style={{ marginBottom: 0 }}
                />
                {choices.length > 2 && type !== "true_false" && (
                  <button
                    type="button"
                    className="btn btn-danger-ghost btn-sm"
                    onClick={() => setChoices((prev) => prev.filter((_, idx) => idx !== i))}
                  >
                    <X width={13} height={13} />
                  </button>
                )}
              </div>
            ))}
          </div>
          {type !== "true_false" && (
            <button
              type="button"
              className="btn btn-ghost btn-sm mt-2"
              onClick={() => setChoices((prev) => [...prev, { text: "", is_correct: false }])}
            >
              <Plus width={13} height={13} /> Variant qo&apos;shish
            </button>
          )}
        </div>
      ) : (
        <div className="field">
          <label>To&apos;g&apos;ri javob (aniq matn)</label>
          <input value={pattern} onChange={(e) => setPattern(e.target.value)} placeholder="masalan: python" />
        </div>
      )}

      <div className="row">
        <button className="btn btn-sm" type="submit" disabled={saving}>
          {saving && <span className="spinner" />} Saqlash
        </button>
        <button className="btn btn-ghost btn-sm" type="button" onClick={onCancel}>
          Bekor qilish
        </button>
      </div>
    </form>
  );
}
