"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import AppShell from "../../../components/AppShell";
import EditQuizModal from "../../../components/mentor/EditQuizModal";
import SendTestModal from "../../../components/mentor/SendTestModal";
import { Book, Clock, HelpCircle, Plus, Search, Settings, X } from "../../../components/Icons";
import { useNotify } from "../../../components/NotificationProvider";
import { errorMessage, mentorApi } from "../../../lib/api";
import { useAuth } from "../../../lib/auth";
import { formatDuration } from "../../../lib/format";

/** Mentorning barcha testlarini yaratish va boshqarish uchun alohida bo'lim — karta-grid ko'rinishida. */
export default function MentorTestsPage() {
  const { user, loading } = useAuth({ roles: ["mentor"] });
  const notify = useNotify();
  const [courses, setCourses] = useState([]);
  const [dataLoading, setDataLoading] = useState(true);
  const [managingLesson, setManagingLesson] = useState(null);
  const [query, setQuery] = useState("");

  const load = useCallback(() => {
    return mentorApi
      .courses()
      .then(({ data }) => { setCourses(data); return data; })
      .catch((err) => { notify({ type: "danger", text: errorMessage(err) }); return []; })
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

  // Modal ochiq bo'lsa ham, orqa fonda ma'lumot yangilansa (masalan guruhga yuborilganda)
  // eng so'nggi lesson holatini ko'rsatish uchun
  const allLessons = useMemo(() => courses.flatMap((c) => c.modules).flatMap((m) => m.lessons), [courses]);
  const managingLive = managingLesson
    ? allLessons.find((l) => l.id === managingLesson.id) || managingLesson
    : null;

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

      <TestCreateCard courses={courses} onCreated={(lessonId) => load().then((data) => {
        const lesson = data.flatMap((c) => c.modules).flatMap((m) => m.lessons).find((l) => l.id === lessonId);
        if (lesson) setManagingLesson(lesson);
      })} onError={notify} />

      {!dataLoading && totalTests > 0 && (
        <>
          <div className="tg-kpis mt-3">
            <KpiCard icon={<HelpCircle width={17} height={17} />} value={totalTests} label="Jami test" tone="primary" />
            <KpiCard icon={<Book width={17} height={17} />} value={totalModules} label="Bo'limlar" tone="info" />
            <KpiCard icon={<Plus width={17} height={17} />} value={unopened} label="Ochilmagan" tone={unopened ? "warning" : "success"} />
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
        <div className="stack mt-3" style={{ gap: 26 }}>
          {filteredGroups.map(({ course, modules }) => (
            <section key={course.id}>
              <h2 className="tg-course-title">{course.title}</h2>
              <div className="stack" style={{ gap: 18 }}>
                {modules.map(({ module, lessons }) => (
                  <TestModuleBlock
                    key={module.id}
                    module={module}
                    lessons={lessons}
                    onManage={setManagingLesson}
                    onChanged={load}
                    onError={notify}
                  />
                ))}
              </div>
            </section>
          ))}
        </div>
      )}

      {managingLive && (
        <EditQuizModal
          lesson={managingLive}
          onClose={() => { setManagingLesson(null); load(); }}
          onError={notify}
        />
      )}

      <style jsx>{`
        .tg-kpis {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
          gap: 12px;
        }
        .tg-course-title {
          font-size: 15px;
          font-weight: 700;
          color: var(--text-secondary);
          text-transform: uppercase;
          letter-spacing: 0.03em;
          margin: 0 0 12px;
        }
      `}</style>
    </AppShell>
  );
}

// ---------------------------------------------------------------------------

function KpiCard({ icon, value, label, tone }) {
  return (
    <div className="card" style={{ display: "flex", alignItems: "center", gap: 12, padding: 16 }}>
      <div className={`tg-kpi-icon tg-kpi-${tone}`}>{icon}</div>
      <div>
        <div className="strong" style={{ fontSize: 20, lineHeight: 1.2 }}>{value}</div>
        <div className="small dim">{label}</div>
      </div>
      <style jsx>{`
        .tg-kpi-icon {
          width: 40px; height: 40px; min-width: 40px;
          border-radius: var(--radius);
          display: flex; align-items: center; justify-content: center;
        }
        .tg-kpi-primary { background: var(--primary-soft); color: var(--primary); }
        .tg-kpi-info { background: var(--info-soft); color: var(--info); }
        .tg-kpi-warning { background: var(--warning-soft); color: var(--warning); }
        .tg-kpi-success { background: var(--success-soft); color: var(--success); }
      `}</style>
    </div>
  );
}

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

function TestModuleBlock({ module, lessons, onManage, onChanged, onError }) {
  const missing = lessons.filter((l) => !l.quiz_id).length;
  const opened = lessons.length - missing;

  return (
    <div>
      <div className="row-between mb-2">
        <div className="row" style={{ gap: 8 }}>
          <strong className="small">{module.title}</strong>
          <span className="chip">{lessons.length} ta test</span>
        </div>
        <span className="small dim">
          {opened}/{lessons.length} ochilgan
          {missing > 0 && <span className="badge badge-warning" style={{ marginLeft: 8 }}>{missing} ochilmagan</span>}
        </span>
      </div>

      <div className="tg-grid">
        {lessons.map((lesson) => (
          <TestCard
            key={lesson.id}
            lesson={lesson}
            onManage={() => onManage(lesson)}
            onChanged={onChanged}
            onError={onError}
          />
        ))}
      </div>

      <style jsx>{`
        .tg-grid {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
          gap: 12px;
        }
      `}</style>
    </div>
  );
}

function TestCard({ lesson, onManage, onChanged, onError }) {
  const [creatingQuiz, setCreatingQuiz] = useState(false);
  const sentGroups = lesson.quiz_sent_groups || [];
  const isOpened = Boolean(lesson.quiz_id);
  const isSent = sentGroups.length > 0;

  async function handleCreateQuiz() {
    setCreatingQuiz(true);
    try {
      await mentorApi.createQuiz(lesson.id, {});
      await onChanged();
      onManage();
    } catch (err) {
      onError({ type: "danger", text: errorMessage(err, "Test ochishda xatolik") });
    } finally {
      setCreatingQuiz(false);
    }
  }

  const dotTone = !isOpened ? "neutral" : isSent ? "success" : "warning";

  return (
    <div className={`tc-card tc-${dotTone}`}>
      <div className="row-between">
        <div className={`tc-icon tc-icon-${dotTone}`}>
          <HelpCircle width={16} height={16} />
        </div>
        {isOpened ? (
          <button type="button" className="btn btn-ghost btn-sm" onClick={onManage} title="Boshqarish" aria-label="Boshqarish">
            <Settings width={14} height={14} />
          </button>
        ) : null}
      </div>

      <p className="tc-title" title={lesson.title}>{lesson.title}</p>

      {isOpened ? (
        <div className="row small dim" style={{ gap: 12, flexWrap: "wrap" }}>
          <span className="row" style={{ gap: 4 }}>
            <HelpCircle width={12} height={12} /> {lesson.quiz_question_count ?? 0} savol
          </span>
          {lesson.quiz_time_limit_seconds ? (
            <span className="row" style={{ gap: 4 }}>
              <Clock width={12} height={12} /> {formatDuration(lesson.quiz_time_limit_seconds)}
            </span>
          ) : null}
        </div>
      ) : (
        <p className="small dim" style={{ margin: 0 }}>Savollar hali qo&apos;shilmagan</p>
      )}

      {sentGroups.length > 0 && (
        <div className="row" style={{ gap: 5, flexWrap: "wrap", marginTop: 8 }}>
          {sentGroups.slice(0, 3).map((g) => (
            <span key={g.id} className="badge badge-success">{g.name}</span>
          ))}
          {sentGroups.length > 3 && <span className="badge badge-neutral">+{sentGroups.length - 3}</span>}
        </div>
      )}

      <div className="tc-footer">
        {isOpened ? (
          <SendTestModal lesson={lesson} sentGroups={sentGroups} onSent={onChanged} />
        ) : (
          <button className="btn btn-sm" style={{ width: "100%" }} onClick={handleCreateQuiz} disabled={creatingQuiz}>
            {creatingQuiz ? <span className="spinner" /> : <Plus width={14} height={14} />}
            Test ochish
          </button>
        )}
      </div>

      <style jsx>{`
        .tc-card {
          display: flex;
          flex-direction: column;
          background: var(--bg-elevated);
          border: 1px solid var(--border);
          border-radius: var(--radius);
          padding: 14px;
          box-shadow: var(--shadow-sm);
          transition: box-shadow 0.15s var(--ease), border-color 0.15s var(--ease), transform 0.15s var(--ease);
        }
        .tc-card:hover {
          box-shadow: var(--shadow);
          transform: translateY(-1px);
        }
        .tc-neutral { border-style: dashed; }
        .tc-icon {
          width: 30px; height: 30px;
          border-radius: var(--radius-sm);
          display: flex; align-items: center; justify-content: center;
        }
        .tc-icon-neutral { background: var(--bg-subtle); color: var(--text-muted); }
        .tc-icon-warning { background: var(--warning-soft); color: var(--warning); }
        .tc-icon-success { background: var(--success-soft); color: var(--success); }
        .tc-title {
          font-weight: 600;
          font-size: 13.5px;
          margin: 10px 0 6px;
          overflow: hidden;
          text-overflow: ellipsis;
          display: -webkit-box;
          -webkit-line-clamp: 2;
          -webkit-box-orient: vertical;
          min-height: 34px;
        }
        .tc-footer { margin-top: 12px; }
        .tc-footer > :global(button) { width: 100%; }
      `}</style>
    </div>
  );
}
