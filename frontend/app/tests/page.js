"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import AppShell from "../../components/AppShell";
import { Check, ChevronDown, ChevronRight, Clock, HelpCircle, Search, X } from "../../components/Icons";
import { useNotify } from "../../components/NotificationProvider";
import { assessmentsApi, errorMessage } from "../../lib/api";
import { useAuth } from "../../lib/auth";

const STATUS_META = {
  new: { label: "Yangi", badge: "neutral" },
  in_progress: { label: "Jarayonda", badge: "warning" },
  passed: { label: "O'tildi", badge: "success" },
  failed: { label: "O'tilmadi", badge: "danger" },
};

function testStatus(t) {
  if (t.has_in_progress) return "in_progress";
  if (t.passed) return "passed";
  if (t.attempt_count > 0) return "failed";
  return "new";
}

/** O'quvchiga mavjud barcha testlar — kurs/modul bo'yicha guruhlangan, qidiruv bilan. */
export default function MyTestsPage() {
  const { user, loading } = useAuth();
  const notify = useNotify();
  const [tests, setTests] = useState([]);
  const [dataLoading, setDataLoading] = useState(true);
  const [query, setQuery] = useState("");

  const load = useCallback(() => {
    return assessmentsApi
      .mine()
      .then(({ data }) => setTests(data))
      .catch((err) => notify({ type: "danger", text: errorMessage(err) }))
      .finally(() => setDataLoading(false));
  }, [notify]);

  useEffect(() => {
    if (!loading) load();
  }, [loading, load]);

  const groups = useMemo(() => {
    const byCourse = new Map();
    for (const t of tests) {
      if (!byCourse.has(t.course_title)) byCourse.set(t.course_title, new Map());
      const byModule = byCourse.get(t.course_title);
      if (!byModule.has(t.module_title)) byModule.set(t.module_title, []);
      byModule.get(t.module_title).push(t);
    }
    return Array.from(byCourse.entries()).map(([courseTitle, byModule]) => ({
      courseTitle,
      modules: Array.from(byModule.entries()).map(([moduleTitle, lessons]) => ({ moduleTitle, lessons })),
    }));
  }, [tests]);

  const q = query.trim().toLowerCase();
  const filteredGroups = useMemo(() => {
    if (!q) return groups;
    return groups
      .map(({ courseTitle, modules }) => ({
        courseTitle,
        modules: modules
          .map((m) => ({ ...m, lessons: m.lessons.filter((l) => l.title.toLowerCase().includes(q)) }))
          .filter((m) => m.lessons.length > 0),
      }))
      .filter((c) => c.modules.length > 0);
  }, [groups, q]);

  const passedCount = tests.filter((t) => t.passed).length;
  const scored = tests.filter((t) => t.best_score !== null);
  const avgScore = scored.length
    ? Math.round(scored.reduce((sum, t) => sum + t.best_score, 0) / scored.length)
    : null;

  if (loading) {
    return <div className="app-shell"><main><div className="skeleton" style={{ height: 200 }} /></main></div>;
  }

  return (
    <AppShell user={user}>
      <div className="page-head">
        <div>
          <h1>Testlarim</h1>
          <p>Mavzular bo&apos;yicha testlarni yeching va natijangizni kuzating</p>
        </div>
      </div>

      {!dataLoading && tests.length > 0 && (
        <>
          <div className="stats">
            <div className="stat">
              <div className="stat-label">Jami test</div>
              <div className="stat-value">{tests.length}</div>
            </div>
            <div className="stat">
              <div className="stat-label">O&apos;tilgan</div>
              <div className="stat-value" style={{ color: passedCount ? "var(--success)" : undefined }}>
                {passedCount}
              </div>
            </div>
            <div className="stat">
              <div className="stat-label">O&apos;rtacha ball</div>
              <div className="stat-value">{avgScore === null ? "—" : `${avgScore}%`}</div>
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
      ) : tests.length === 0 ? (
        <div className="card mt-3">
          <div className="empty">
            <div className="empty-icon"><HelpCircle /></div>
            <h3>Hozircha test yo&apos;q</h3>
            <p>Mentoringiz test tayyorlagach shu yerda ko&apos;rinadi.</p>
          </div>
        </div>
      ) : filteredGroups.length === 0 ? (
        <p className="small dim mt-3">&quot;{query}&quot; bo&apos;yicha hech narsa topilmadi.</p>
      ) : (
        <div className="stack mt-2">
          {filteredGroups.map(({ courseTitle, modules }) => (
            <section key={courseTitle} className="card">
              <div className="card-head">
                <h2>{courseTitle}</h2>
              </div>
              <div className="stack" style={{ gap: 10 }}>
                {modules.map(({ moduleTitle, lessons }) => (
                  <ModuleGroup key={moduleTitle} moduleTitle={moduleTitle} lessons={lessons} forceOpen={Boolean(q)} />
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

function ModuleGroup({ moduleTitle, lessons, forceOpen }) {
  const [manualOpen, setManualOpen] = useState(false);
  const open = forceOpen || manualOpen;
  const passedCount = lessons.filter((l) => l.passed).length;

  return (
    <div style={{ border: "1px solid var(--border)", borderRadius: "var(--radius)", padding: 14 }}>
      <div className="row-between">
        <button
          className="row"
          style={{ background: "none", border: "none", cursor: "pointer", gap: 7, padding: 0, textAlign: "left" }}
          onClick={() => setManualOpen((v) => !v)}
        >
          {open ? <ChevronDown width={16} height={16} /> : <ChevronRight width={16} height={16} />}
          <strong>{moduleTitle}</strong>
          <span className="chip">{lessons.length} ta test</span>
        </button>
        {passedCount > 0 && (
          <span className="badge badge-success">
            <Check width={12} height={12} /> {passedCount}/{lessons.length}
          </span>
        )}
      </div>

      {open && (
        <div className="stack mt-2" style={{ gap: 8 }}>
          {lessons.map((lesson) => <TestRow key={lesson.lesson_id} test={lesson} />)}
        </div>
      )}
    </div>
  );
}

function TestRow({ test }) {
  const status = testStatus(test);
  const meta = STATUS_META[status];
  const minutes = test.time_limit_seconds ? Math.round(test.time_limit_seconds / 60) : null;

  return (
    <Link
      href={`/tests/${test.lesson_id}`}
      className="card card-hover card-compact"
      style={{ display: "block", color: "inherit", background: "var(--bg-subtle)", border: "none", boxShadow: "none" }}
    >
      <div className="row-between">
        <div className="row" style={{ gap: 9 }}>
          <HelpCircle width={15} height={15} className="dim" />
          <span className="strong small">{test.title}</span>
          <span className={`badge badge-${meta.badge}`}>{meta.label}</span>
        </div>
        <ChevronRight width={15} height={15} className="dim" />
      </div>
      <div className="row mt-1" style={{ gap: 10 }}>
        <span className="small dim">{test.question_count} ta savol</span>
        {minutes && (
          <span className="small dim row" style={{ gap: 3 }}>
            <Clock width={11} height={11} /> {minutes} daqiqa
          </span>
        )}
        {test.best_score !== null && (
          <span className="small dim">Eng yaxshi natija: <strong>{test.best_score}%</strong></span>
        )}
        <span className="small dim">Urinish: {test.attempt_count}/{test.max_attempts}</span>
      </div>
    </Link>
  );
}
