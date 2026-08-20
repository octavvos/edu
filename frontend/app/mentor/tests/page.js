"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import AppShell from "../../../components/AppShell";
import QuizBuilder from "../../../components/mentor/QuizBuilder";
import SendTestModal from "../../../components/mentor/SendTestModal";
import { ChevronDown, ChevronRight, HelpCircle, Plus, Search, X } from "../../../components/Icons";
import { useNotify } from "../../../components/NotificationProvider";
import { errorMessage, mentorApi } from "../../../lib/api";
import { useAuth } from "../../../lib/auth";

/** Mentorning barcha testlarini yaratish va boshqarish uchun alohida bo'lim. */
export default function MentorTestsPage() {
  const { user, loading } = useAuth({ roles: ["mentor"] });
  const notify = useNotify();
  const [courses, setCourses] = useState([]);
  const [dataLoading, setDataLoading] = useState(true);
  const [openLessonId, setOpenLessonId] = useState(null);
  const [query, setQuery] = useState("");

  const load = useCallback(() => {
    return mentorApi
      .courses()
      .then(({ data }) => setCourses(data))
      .catch((err) => notify({ type: "danger", text: errorMessage(err) }))
      .finally(() => setDataLoading(false));
  }, [notify]);

  useEffect(() => {
    if (!loading) load();
  }, [loading, load]);

  // Kurs -> faqat testli modullar -> shu moduldagi test darslari
  const courseGroups = useMemo(() => {
    return courses
      .map((course) => ({
        course,
        modules: course.modules
          .map((module) => ({
            module,
            lessons: module.lessons.filter((lesson) => lesson.type === "quiz"),
          }))
          .filter((m) => m.lessons.length > 0),
      }))
      .filter((c) => c.modules.length > 0);
  }, [courses]);

  const q = query.trim().toLowerCase();
  const filteredGroups = useMemo(() => {
    if (!q) return courseGroups;
    return courseGroups
      .map(({ course, modules }) => ({
        course,
        modules: modules
          .map((m) => ({ ...m, lessons: m.lessons.filter((l) => l.title.toLowerCase().includes(q)) }))
          .filter((m) => m.lessons.length > 0),
      }))
      .filter((c) => c.modules.length > 0);
  }, [courseGroups, q]);

  const totalTests = courseGroups.reduce((sum, c) => sum + c.modules.reduce((s, m) => s + m.lessons.length, 0), 0);
  const totalModules = courseGroups.reduce((sum, c) => sum + c.modules.length, 0);
  const unopened = courseGroups.reduce(
    (sum, c) => sum + c.modules.reduce((s, m) => s + m.lessons.filter((l) => !l.quiz_id).length, 0),
    0,
  );

  if (loading) {
    return <div className="app-shell"><main><div className="skeleton" style={{ height: 200 }} /></main></div>;
  }

  return (
    <AppShell user={user}>
      <div className="page-head">
        <div>
          <h1>Testlar</h1>
          <p>Yangi test yarating, savollarni va sozlamalarini shu yerda boshqaring</p>
        </div>
      </div>

      <TestCreateCard courses={courses} onCreated={(lessonId) => { load(); setOpenLessonId(lessonId); }} onError={notify} />

      {!dataLoading && totalTests > 0 && (
        <>
          <div className="stats mt-3">
            <div className="stat">
              <div className="stat-label">Jami test</div>
              <div className="stat-value">{totalTests}</div>
            </div>
            <div className="stat">
              <div className="stat-label">Bo&apos;limlar</div>
              <div className="stat-value">{totalModules}</div>
            </div>
            <div className="stat">
              <div className="stat-label">Ochilmagan</div>
              <div className="stat-value" style={{ color: unopened ? "var(--warning)" : undefined }}>
                {unopened}
              </div>
            </div>
          </div>

          <div className="field mt-3 mb-1" style={{ maxWidth: 340, position: "relative" }}>
            <Search width={15} height={15} className="dim" style={{ position: "absolute", left: 12, top: 12 }} />
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Test nomi bo'yicha qidirish…"
              style={{ paddingLeft: 34, paddingRight: query ? 34 : undefined, marginBottom: 0 }}
            />
            {query && (
              <button
                type="button"
                className="btn btn-ghost btn-sm"
                onClick={() => setQuery("")}
                style={{ position: "absolute", right: 3, top: 3, padding: 6 }}
                aria-label="Qidiruvni tozalash"
              >
                <X width={13} height={13} />
              </button>
            )}
          </div>
        </>
      )}

      {dataLoading ? (
        <div className="stack mt-3">
          <div className="skeleton" style={{ height: 90 }} />
          <div className="skeleton" style={{ height: 90 }} />
        </div>
      ) : totalTests === 0 ? (
        <div className="card mt-3">
          <div className="empty">
            <div className="empty-icon"><HelpCircle /></div>
            <h3>Hozircha test yo&apos;q</h3>
            <p>Yuqoridagi forma orqali birinchi testingizni yarating.</p>
          </div>
        </div>
      ) : filteredGroups.length === 0 ? (
        <p className="small dim mt-3">&quot;{query}&quot; bo&apos;yicha hech narsa topilmadi.</p>
      ) : (
        <div className="stack mt-2">
          {filteredGroups.map(({ course, modules }) => (
            <section key={course.id} className="card">
              <div className="card-head">
                <h2>{course.title}</h2>
              </div>
              <div className="stack" style={{ gap: 10 }}>
                {modules.map(({ module, lessons }) => (
                  <TestModuleBlock
                    key={module.id}
                    module={module}
                    lessons={lessons}
                    forceOpen={Boolean(q)}
                    openLessonId={openLessonId}
                    setOpenLessonId={setOpenLessonId}
                    onChanged={load}
                    onError={notify}
                  />
                ))}
              </div>
            </section>
          ))}
        </div>
      )}
    </AppShell>
  );
}

// ---------------------------------------------------------------------------

function TestCreateCard({ courses, onCreated, onError }) {
  const [courseId, setCourseId] = useState("");
  const [moduleId, setModuleId] = useState("");
  const [title, setTitle] = useState("");
  const [saving, setSaving] = useState(false);

  const modules = courses.find((c) => c.id === courseId)?.modules || [];

  function selectCourse(id) {
    setCourseId(id);
    setModuleId("");
  }

  async function submit(e) {
    e.preventDefault();
    if (!moduleId || !title.trim()) return;
    setSaving(true);
    try {
      const { data: lesson } = await mentorApi.createLesson(moduleId, {
        type: "quiz",
        title: { uz: title.trim() },
      });
      await mentorApi.createQuiz(lesson.id, {});
      setTitle("");
      onCreated(lesson.id);
    } catch (err) {
      onError({ type: "danger", text: errorMessage(err, "Test yaratishda xatolik") });
    } finally {
      setSaving(false);
    }
  }

  if (courses.length === 0) {
    return (
      <div className="card">
        <p className="small dim">Test yaratish uchun avval sizga kurs biriktirilgan bo&apos;lishi kerak.</p>
      </div>
    );
  }

  return (
    <form className="card" onSubmit={submit}>
      <div className="card-head">
        <h2>Yangi test yaratish</h2>
      </div>
      <div className="row" style={{ gap: 10, flexWrap: "wrap", alignItems: "flex-end" }}>
        <div className="field" style={{ marginBottom: 0, flex: "0 1 220px" }}>
          <label>Kurs</label>
          <select value={courseId} onChange={(e) => selectCourse(e.target.value)}>
            <option value="">Tanlang…</option>
            {courses.map((c) => <option key={c.id} value={c.id}>{c.title}</option>)}
          </select>
        </div>
        <div className="field" style={{ marginBottom: 0, flex: "0 1 220px" }}>
          <label>Modul</label>
          <select value={moduleId} onChange={(e) => setModuleId(e.target.value)} disabled={!courseId}>
            <option value="">Tanlang…</option>
            {modules.map((m) => <option key={m.id} value={m.id}>{m.title}</option>)}
          </select>
        </div>
        <div className="field" style={{ marginBottom: 0, flex: "1 1 220px" }}>
          <label>Test nomi</label>
          <input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="masalan: 1-modul yakuniy testi" />
        </div>
        <button className="btn btn-sm" type="submit" disabled={saving || !moduleId || !title.trim()}>
          {saving ? <span className="spinner" /> : <Plus width={14} height={14} />}
          Yaratish
        </button>
      </div>
    </form>
  );
}

// ---------------------------------------------------------------------------

function TestModuleBlock({ module, lessons, forceOpen, openLessonId, setOpenLessonId, onChanged, onError }) {
  const [manualOpen, setManualOpen] = useState(false);
  const open = forceOpen || manualOpen;
  const missing = lessons.filter((l) => !l.quiz_id).length;

  return (
    <div style={{ border: "1px solid var(--border)", borderRadius: "var(--radius)", padding: 14 }}>
      <div className="row-between">
        <button
          className="row"
          style={{ background: "none", border: "none", cursor: "pointer", gap: 7, padding: 0, textAlign: "left" }}
          onClick={() => setManualOpen((v) => !v)}
        >
          {open ? <ChevronDown width={16} height={16} /> : <ChevronRight width={16} height={16} />}
          <strong>{module.title}</strong>
          <span className="chip">{lessons.length} ta test</span>
        </button>
        {missing > 0 && <span className="badge badge-warning">{missing} ochilmagan</span>}
      </div>

      {open && (
        <div className="stack mt-2" style={{ gap: 8 }}>
          {lessons.map((lesson) => (
            <TestLessonRow
              key={lesson.id}
              lesson={lesson}
              open={openLessonId === lesson.id}
              onToggle={() => setOpenLessonId(openLessonId === lesson.id ? null : lesson.id)}
              onChanged={onChanged}
              onError={onError}
            />
          ))}
        </div>
      )}
    </div>
  );
}

function TestLessonRow({ lesson, open, onToggle, onChanged, onError }) {
  const [creatingQuiz, setCreatingQuiz] = useState(false);

  async function handleCreateQuiz() {
    setCreatingQuiz(true);
    try {
      await mentorApi.createQuiz(lesson.id, {});
      onChanged();
      onToggle();
    } catch (err) {
      onError({ type: "danger", text: errorMessage(err, "Test ochishda xatolik") });
    } finally {
      setCreatingQuiz(false);
    }
  }

  const sentGroups = lesson.quiz_sent_groups || [];

  return (
    <div className="card-compact" style={{ background: "var(--bg-subtle)", border: "none", boxShadow: "none" }}>
      <div className="row-between">
        <div className="row" style={{ gap: 9, flexWrap: "wrap" }}>
          <HelpCircle width={15} height={15} className="dim" />
          <span className="strong small">{lesson.title}</span>
          {sentGroups.map((g) => (
            <span key={g.id} className="badge badge-success">{g.name}</span>
          ))}
        </div>

        <div className="row" style={{ gap: 6, flexWrap: "nowrap" }}>
          {lesson.quiz_id && (
            <SendTestModal lesson={lesson} sentGroups={sentGroups} onSent={onChanged} />
          )}
          {lesson.quiz_id ? (
            <button className="btn btn-ghost btn-sm" onClick={onToggle}>
              {open ? <ChevronDown width={14} height={14} /> : <ChevronRight width={14} height={14} />}
              {open ? "Yopish" : "Boshqarish"}
            </button>
          ) : (
            <button className="btn btn-sm" onClick={handleCreateQuiz} disabled={creatingQuiz}>
              {creatingQuiz ? <span className="spinner" /> : <Plus width={14} height={14} />}
              Test ochish
            </button>
          )}
        </div>
      </div>

      {open && lesson.quiz_id && <QuizBuilder quizId={lesson.quiz_id} onError={onError} />}
    </div>
  );
}
