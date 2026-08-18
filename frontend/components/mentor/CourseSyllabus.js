"use client";

import { useCallback, useEffect, useState } from "react";
import {
  Check, ChevronDown, ChevronRight, FileText, HelpCircle, Plus, X,
} from "../Icons";
import { errorMessage, mentorApi } from "../../lib/api";
import MaterialUploadModal from "./MaterialUploadModal";

const LESSON_TYPES = [
  { value: "text", label: "Matnli dars" },
  { value: "video", label: "Video dars" },
  { value: "file", label: "Fayl / material" },
  { value: "quiz", label: "Test" },
  { value: "homework", label: "Uy vazifasi" },
];

const QUESTION_TYPES = [
  { value: "single_choice", label: "Bitta to'g'ri javob" },
  { value: "multiple_choice", label: "Bir nechta to'g'ri javob" },
  { value: "true_false", label: "To'g'ri / noto'g'ri" },
  { value: "short_text", label: "Qisqa matnli javob" },
];

/** Bitta kursning to'liq dars rejasi: modul/dars qo'shish, material, test. */
export default function CourseSyllabus({ course, onChanged, onError }) {
  const [addingModule, setAddingModule] = useState(false);

  return (
    <section className="card">
      <div className="card-head">
        <h2>{course.title}</h2>
        <button className="btn btn-sm" onClick={() => setAddingModule((v) => !v)}>
          {addingModule ? <X width={14} height={14} /> : <Plus width={14} height={14} />}
          Modul qo&apos;shish
        </button>
      </div>

      {addingModule && (
        <ModuleCreateForm
          courseId={course.id}
          onCreated={() => { setAddingModule(false); onChanged(); }}
          onError={(text) => onError({ type: "danger", text })}
        />
      )}

      {course.modules.length === 0 ? (
        <p className="small dim">Hali modul yo&apos;q.</p>
      ) : (
        <div className="stack" style={{ gap: 10 }}>
          {course.modules.map((module) => (
            <ModuleBlock key={module.id} module={module} onChanged={onChanged} onError={onError} />
          ))}
        </div>
      )}
    </section>
  );
}

function ModuleCreateForm({ courseId, onCreated, onError }) {
  const [title, setTitle] = useState("");
  const [saving, setSaving] = useState(false);

  async function submit(e) {
    e.preventDefault();
    if (!title.trim()) return;
    setSaving(true);
    try {
      await mentorApi.createModule(courseId, { uz: title.trim() });
      onCreated();
    } catch (err) {
      onError(errorMessage(err, "Modul yaratishda xatolik"));
    } finally {
      setSaving(false);
    }
  }

  return (
    <form className="row mb-2" onSubmit={submit} style={{ gap: 8 }}>
      <input
        value={title}
        onChange={(e) => setTitle(e.target.value)}
        placeholder="Modul nomi (masalan: 2-modul: Django)"
        style={{ flex: 1, marginBottom: 0 }}
        autoFocus
      />
      <button className="btn btn-sm" type="submit" disabled={saving}>
        {saving && <span className="spinner" />} Saqlash
      </button>
    </form>
  );
}

// ---------------------------------------------------------------------------

function ModuleBlock({ module, onChanged, onError }) {
  const [open, setOpen] = useState(false);
  const [addingLesson, setAddingLesson] = useState(false);

  return (
    <div style={{ border: "1px solid var(--border)", borderRadius: "var(--radius)", padding: 14 }}>
      <div className="row-between">
        <button
          className="row"
          style={{ background: "none", border: "none", cursor: "pointer", gap: 7, padding: 0 }}
          onClick={() => setOpen((v) => !v)}
        >
          {open ? <ChevronDown width={16} height={16} /> : <ChevronRight width={16} height={16} />}
          <strong>{module.title}</strong>
          <span className="chip">{module.lessons.length} ta dars</span>
        </button>
        <button className="btn btn-ghost btn-sm" onClick={() => setAddingLesson((v) => !v)}>
          {addingLesson ? <X width={14} height={14} /> : <Plus width={14} height={14} />}
          Dars qo&apos;shish
        </button>
      </div>

      {addingLesson && (
        <LessonCreateForm
          moduleId={module.id}
          onCreated={() => { setAddingLesson(false); onChanged(); }}
          onError={(text) => onError({ type: "danger", text })}
        />
      )}

      {open && (
        <div className="stack mt-2" style={{ gap: 8 }}>
          {module.lessons.map((lesson) => (
            <LessonRow key={lesson.id} lesson={lesson} onChanged={onChanged} onError={onError} />
          ))}
        </div>
      )}
    </div>
  );
}

function LessonCreateForm({ moduleId, onCreated, onError }) {
  const [type, setType] = useState("text");
  const [title, setTitle] = useState("");
  const [saving, setSaving] = useState(false);

  async function submit(e) {
    e.preventDefault();
    if (!title.trim()) return;
    setSaving(true);
    try {
      await mentorApi.createLesson(moduleId, { type, title: { uz: title.trim() } });
      onCreated();
    } catch (err) {
      onError(errorMessage(err, "Dars yaratishda xatolik"));
    } finally {
      setSaving(false);
    }
  }

  return (
    <form className="row mt-2" onSubmit={submit} style={{ gap: 8, flexWrap: "nowrap" }}>
      <select value={type} onChange={(e) => setType(e.target.value)} style={{ flex: "0 1 200px" }}>
        {LESSON_TYPES.map((t) => (
          <option key={t.value} value={t.value}>{t.label}</option>
        ))}
      </select>
      <input
        value={title}
        onChange={(e) => setTitle(e.target.value)}
        placeholder="Dars nomi"
        style={{ flex: 1, marginBottom: 0 }}
      />
      <button className="btn btn-sm" type="submit" disabled={saving}>
        {saving && <span className="spinner" />} Qo&apos;shish
      </button>
    </form>
  );
}

// ---------------------------------------------------------------------------

function LessonRow({ lesson, onChanged, onError }) {
  const [quizOpen, setQuizOpen] = useState(false);
  const [detailsOpen, setDetailsOpen] = useState(false);
  const [creatingQuiz, setCreatingQuiz] = useState(false);

  async function handleCreateQuiz() {
    setCreatingQuiz(true);
    try {
      await mentorApi.createQuiz(lesson.id, {});
      setQuizOpen(true);
      onChanged();
    } catch (err) {
      onError({ type: "danger", text: errorMessage(err, "Test ochishda xatolik") });
    } finally {
      setCreatingQuiz(false);
    }
  }

  return (
    <div className="card" style={{ padding: "11px 14px" }}>
      <div className="row-between">
        <button
          className="row"
          style={{ background: "none", border: "none", cursor: "pointer", gap: 9, padding: 0, textAlign: "left" }}
          onClick={() => setDetailsOpen((v) => !v)}
        >
          <span className="badge badge-neutral">{typeLabel(lesson.type)}</span>
          <span className="strong small">{lesson.title}</span>
        </button>

        <div className="row" style={{ gap: 6, flexWrap: "nowrap" }}>
          {lesson.type === "quiz" ? (
            lesson.quiz_id ? (
              <button className="btn btn-ghost btn-sm" onClick={() => setQuizOpen((v) => !v)}>
                <HelpCircle width={14} height={14} />
                {quizOpen ? "Yopish" : "Testni boshqarish"}
              </button>
            ) : (
              <button className="btn btn-sm" onClick={handleCreateQuiz} disabled={creatingQuiz}>
                {creatingQuiz ? <span className="spinner" /> : <Plus width={14} height={14} />}
                Test ochish
              </button>
            )
          ) : (
            <MaterialUploadModal
              lessonId={lesson.id}
              label={lesson.materials?.length > 0 ? "Yana fayl qo'shish" : "Material yuklash"}
              onUploaded={onChanged}
            />
          )}
        </div>
      </div>

      {detailsOpen && lesson.text_content && (
        <p className="small muted mt-2 fade-in">{lesson.text_content}</p>
      )}

      {lesson.materials?.length > 0 && (
        <div className="stack mt-2" style={{ gap: 4 }}>
          {lesson.materials.map((material) => (
            <a
              key={material.id}
              href={material.file}
              target="_blank"
              rel="noreferrer"
              className="row small"
              style={{ gap: 6, color: "var(--text-secondary)" }}
            >
              <FileText width={14} height={14} />
              {material.title || material.original_filename}
              <span className="dim">({formatSize(material.size_bytes)})</span>
            </a>
          ))}
        </div>
      )}

      {quizOpen && lesson.quiz_id && (
        <QuizBuilder quizId={lesson.quiz_id} onError={onError} />
      )}
    </div>
  );
}

function typeLabel(type) {
  return LESSON_TYPES.find((t) => t.value === type)?.label || type;
}

function formatSize(bytes) {
  if (!bytes) return "0 KB";
  if (bytes < 1024 * 1024) return `${Math.round(bytes / 1024)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

// ---------------------------------------------------------------------------
// Test (quiz) builder
// ---------------------------------------------------------------------------

function QuizBuilder({ quizId, onError }) {
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
