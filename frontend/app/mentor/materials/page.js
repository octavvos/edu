"use client";

import { useCallback, useEffect, useState } from "react";
import AppShell from "../../../components/AppShell";
import { Book, Check, ChevronDown, ChevronRight, FileText, X } from "../../../components/Icons";
import MaterialLink from "../../../components/mentor/MaterialLink";
import MaterialUploadModal from "../../../components/mentor/MaterialUploadModal";
import { useNotify } from "../../../components/NotificationProvider";
import { errorMessage, mentorApi } from "../../../lib/api";
import { MATERIAL_KIND_LABEL, MAX_MATERIAL_SIZE_MB, formatFileSize } from "../../../lib/materials";
import { useAuth } from "../../../lib/auth";

const LESSON_TYPE_LABEL = {
  text: "Matnli dars",
  video: "Video dars",
  file: "Fayl / material",
  quiz: "Test",
  homework: "Uy vazifasi",
};

/** Chap: ixcham dars ro'yxati. O'ng: tanlangan darsning materiallari doim ko'rinadi. */
export default function MentorMaterialsPage() {
  const { user, loading } = useAuth({ roles: ["mentor"] });
  const notify = useNotify();
  const [courses, setCourses] = useState([]);
  const [courseId, setCourseId] = useState(null);
  const [selectedId, setSelectedId] = useState(null);
  const [dataLoading, setDataLoading] = useState(true);

  const load = useCallback(() => {
    return mentorApi
      .courses()
      .then(({ data }) => {
        setCourses(data);
        setCourseId((prev) => prev || data[0]?.id || null);
      })
      .catch((err) => notify({ type: "danger", text: errorMessage(err) }))
      .finally(() => setDataLoading(false));
  }, [notify]);

  useEffect(() => {
    if (!loading) load();
  }, [loading, load]);

  if (loading) {
    return <div className="app-shell"><main><div className="skeleton" style={{ height: 200 }} /></main></div>;
  }

  const course = courses.find((c) => c.id === courseId);
  const allLessons = course?.modules.flatMap((m) => m.lessons.map((l) => ({ ...l, moduleTitle: m.title }))) || [];
  const totalLessons = allLessons.length;
  const uploadedCount = allLessons.filter((l) => l.materials?.length > 0).length;
  const selected = allLessons.find((l) => l.id === selectedId) || null;

  return (
    <AppShell user={user}>
      <div className="page-head">
        <div>
          <h1>Materiallar</h1>
          <p>Darsni tanlang — materialni o&apos;ng tomonda yuklaysiz</p>
        </div>
        {course && (
          <span className="badge badge-info">
            {uploadedCount} / {totalLessons} darsda material bor
          </span>
        )}
      </div>

      {dataLoading ? (
        <div className="skeleton" style={{ height: 320 }} />
      ) : courses.length === 0 ? (
        <div className="card">
          <div className="empty">
            <div className="empty-icon"><Book /></div>
            <h3>Sizga kurs biriktirilmagan</h3>
            <p>Manager sizni biror guruhga mentor qilib tayinlashi kerak.</p>
          </div>
        </div>
      ) : (
        <>
          {courses.length > 1 && (
            <div className="row mb-3" style={{ gap: 8 }}>
              {courses.map((c) => (
                <button
                  key={c.id}
                  className={`btn btn-sm ${c.id === courseId ? "" : "btn-ghost"}`}
                  onClick={() => { setCourseId(c.id); setSelectedId(null); }}
                >
                  {c.title}
                </button>
              ))}
            </div>
          )}

          {course && (
            <div className="materials-layout">
              <div className="materials-list-pane">
                {course.modules.map((module) => (
                  <ModuleList
                    key={module.id}
                    module={module}
                    selectedId={selectedId}
                    onSelect={setSelectedId}
                  />
                ))}
              </div>

              <div className="materials-detail-pane">
                {selected ? (
                  <MaterialPanel key={selected.id} lesson={selected} onChanged={load} onError={notify} />
                ) : (
                  <div className="card center" style={{ padding: 40 }}>
                    <div className="empty-icon" style={{ margin: "0 auto 12px" }}><FileText /></div>
                    <p className="muted">Chapdan darsni tanlang</p>
                  </div>
                )}
              </div>
            </div>
          )}
        </>
      )}

      <style jsx>{`
        .materials-layout {
          display: flex;
          gap: 16px;
          align-items: flex-start;
        }
        .materials-list-pane {
          flex: 0 0 320px;
          max-width: 320px;
          display: flex;
          flex-direction: column;
          gap: 8px;
        }
        .materials-detail-pane {
          flex: 1;
          min-width: 0;
          position: sticky;
          top: 80px;
        }
        @media (max-width: 800px) {
          .materials-layout { flex-direction: column; }
          .materials-list-pane { max-width: 100%; flex-basis: auto; }
          .materials-detail-pane { position: static; width: 100%; }
        }
      `}</style>
    </AppShell>
  );
}

// ---------------------------------------------------------------------------

function ModuleList({ module, selectedId, onSelect }) {
  const [open, setOpen] = useState(false);
  const uploaded = module.lessons.filter((l) => l.materials?.length > 0).length;

  return (
    <div className="card" style={{ padding: 10 }}>
      <button
        className="row-between"
        style={{ width: "100%", background: "none", border: "none", cursor: "pointer", padding: "2px 4px", textAlign: "left" }}
        onClick={() => setOpen((v) => !v)}
      >
        <div className="row" style={{ gap: 6 }}>
          {open ? <ChevronDown width={14} height={14} /> : <ChevronRight width={14} height={14} />}
          <span className="small strong">{module.title}</span>
        </div>
        <span className="chip" style={{ fontSize: 11 }}>{uploaded}/{module.lessons.length}</span>
      </button>

      {open && (
        <div className="stack mt-1" style={{ gap: 2 }}>
          {module.lessons.map((lesson) => {
            const active = lesson.id === selectedId;
            const count = lesson.materials?.length || 0;
            return (
              <button
                key={lesson.id}
                onClick={() => onSelect(lesson.id)}
                className="row-between"
                style={{
                  width: "100%", textAlign: "left", padding: "7px 8px", borderRadius: "var(--radius-sm)",
                  border: "none", cursor: "pointer", gap: 6,
                  background: active ? "var(--primary-soft)" : "transparent",
                  color: active ? "var(--primary)" : "var(--text)",
                }}
              >
                <span className="row small" style={{ gap: 5, minWidth: 0, overflow: "hidden" }}>
                  <span className="dim" style={{ flexShrink: 0 }}>{lesson.order}.</span>
                  <span style={{
                    overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap",
                    fontWeight: active ? 600 : 400,
                  }}>
                    {lesson.title}
                  </span>
                </span>
                {count > 0 && (
                  <span className="row" style={{ gap: 3, flexShrink: 0, color: "var(--success)" }}>
                    <Check width={13} height={13} />
                    {count > 1 && <span className="small">{count}</span>}
                  </span>
                )}
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------

function MaterialPanel({ lesson, onChanged, onError }) {
  const [deletingId, setDeletingId] = useState(null);
  const materials = lesson.materials || [];

  async function handleDelete(material) {
    if (!window.confirm(`"${material.title || material.original_filename}" o'chirilsinmi?`)) return;
    setDeletingId(material.id);
    try {
      await mentorApi.deleteMaterial(material.id);
      onChanged();
    } catch (err) {
      onError({ type: "danger", text: errorMessage(err, "O'chirishda xatolik") });
    } finally {
      setDeletingId(null);
    }
  }

  return (
    <div className="card fade-in">
      <div className="row" style={{ gap: 8 }}>
        <span className="badge badge-neutral">{LESSON_TYPE_LABEL[lesson.type] || lesson.type}</span>
        <span className="chip">{lesson.moduleTitle}</span>
        <span className="chip">{lesson.order}-dars</span>
      </div>
      <h3 className="mt-2">{lesson.title}</h3>

      {lesson.text_content && <p className="small muted mt-2">{lesson.text_content}</p>}

      {materials.length > 0 && (
        <div className="stack mt-3" style={{ gap: 6 }}>
          {materials.map((material) => (
            <div
              key={material.id}
              className="row-between"
              style={{ padding: "9px 12px", background: "var(--bg-subtle)", borderRadius: "var(--radius)" }}
            >
              <MaterialLink
                material={material}
                className="row small"
                style={{ gap: 7, color: "var(--text)", minWidth: 0 }}
              >
                <FileText width={15} height={15} style={{ flexShrink: 0 }} />
                <span style={{ minWidth: 0, overflow: "hidden" }}>
                  <span className="row" style={{ gap: 6 }}>
                    <span className="strong" style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                      {material.title || material.original_filename}
                    </span>
                    <span className="chip" style={{ fontSize: 11, flexShrink: 0 }}>
                      {MATERIAL_KIND_LABEL[material.kind] || material.kind}
                    </span>
                  </span>
                  {material.description && (
                    <span className="dim" style={{ display: "block", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                      {material.description}
                    </span>
                  )}
                </span>
                <span className="dim" style={{ flexShrink: 0 }}>({formatFileSize(material.size_bytes)})</span>
              </MaterialLink>
              <button
                className="btn btn-danger-ghost btn-sm"
                onClick={() => handleDelete(material)}
                disabled={deletingId === material.id}
                title="O'chirish"
              >
                {deletingId === material.id ? <span className="spinner" /> : <X width={13} height={13} />}
              </button>
            </div>
          ))}
        </div>
      )}

      <div className="mt-3">
        <MaterialUploadModal
          lessonId={lesson.id}
          label={materials.length > 0 ? "Yana fayl qo'shish" : "Fayl tanlash"}
          onUploaded={onChanged}
        />
      </div>

      <div className="alert alert-info mt-3" style={{ marginBottom: 0 }}>
        Ruxsat etilgan: PDF, PPT(X), DOC(X), XLS(X), ZIP, rasm (PNG/JPG/GIF), TXT —
        max {MAX_MATERIAL_SIZE_MB} MB. Video darsni Bunny Stream orqali alohida yuklash tavsiya etiladi.
      </div>
    </div>
  );
}
