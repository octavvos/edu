"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import AppShell from "../../../components/AppShell";
import QuizBuilder from "../../../components/mentor/QuizBuilder";
import { ChevronDown, ChevronRight, HelpCircle, Plus } from "../../../components/Icons";
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

  const quizGroups = useMemo(() => {
    return courses
      .map((course) => ({
        course,
        lessons: course.modules.flatMap((module) =>
          module.lessons
            .filter((lesson) => lesson.type === "quiz")
            .map((lesson) => ({ ...lesson, moduleTitle: module.title })),
        ),
      }))
      .filter((g) => g.lessons.length > 0);
  }, [courses]);

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

      {dataLoading ? (
        <div className="stack mt-3">
          <div className="skeleton" style={{ height: 90 }} />
          <div className="skeleton" style={{ height: 90 }} />
        </div>
      ) : quizGroups.length === 0 ? (
        <div className="card mt-3">
          <div className="empty">
            <div className="empty-icon"><HelpCircle /></div>
            <h3>Hozircha test yo&apos;q</h3>
            <p>Yuqoridagi forma orqali birinchi testingizni yarating.</p>
          </div>
        </div>
      ) : (
        <div className="stack mt-3">
          {quizGroups.map(({ course, lessons }) => (
            <section key={course.id} className="card">
              <div className="card-head">
                <h2>{course.title}</h2>
              </div>
              <div className="stack" style={{ gap: 8 }}>
                {lessons.map((lesson) => (
                  <TestLessonRow
                    key={lesson.id}
                    lesson={lesson}
                    open={openLessonId === lesson.id}
                    onToggle={() => setOpenLessonId(openLessonId === lesson.id ? null : lesson.id)}
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

  return (
    <div className="card" style={{ padding: "11px 14px" }}>
      <div className="row-between">
        <div className="row" style={{ gap: 9 }}>
          <HelpCircle width={15} height={15} className="dim" />
          <div>
            <div className="strong small">{lesson.title}</div>
            <div className="small dim">{lesson.moduleTitle}</div>
          </div>
        </div>

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

      {open && lesson.quiz_id && <QuizBuilder quizId={lesson.quiz_id} onError={onError} />}
    </div>
  );
}
