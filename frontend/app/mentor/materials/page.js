"use client";

import { useCallback, useEffect, useState } from "react";
import AppShell from "../../../components/AppShell";
import { Book, Check, ChevronDown, ChevronRight, FileText, Upload, X } from "../../../components/Icons";
import { errorMessage, mentorApi } from "../../../lib/api";
import { MATERIAL_ACCEPT, MAX_MATERIAL_SIZE_MB, validateMaterialFile } from "../../../lib/materials";
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
  const [courses, setCourses] = useState([]);
  const [courseId, setCourseId] = useState(null);
  const [selectedId, setSelectedId] = useState(null);
  const [dataLoading, setDataLoading] = useState(true);
  const [message, setMessage] = useState(null);

  const load = useCallback(() => {
    return mentorApi
      .courses()
      .then(({ data }) => {
        setCourses(data);
        setCourseId((prev) => prev || data[0]?.id || null);
      })
      .catch((err) => setMessage({ type: "danger", text: errorMessage(err) }))
      .finally(() => setDataLoading(false));
  }, []);

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

      {message && <div className={`alert alert-${message.type}`}>{message.text}</div>}

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
                  <MaterialPanel key={selected.id} lesson={selected} onChanged={load} onError={setMessage} />
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
                <span className="small" style={{
                  overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap",
                  fontWeight: active ? 600 : 400,
                }}>
                  {lesson.title}
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
  const [uploading, setUploading] = useState(false);
  const [dragOver, setDragOver] = useState(false);
  const [deletingId, setDeletingId] = useState(null);
  const materials = lesson.materials || [];

  async function upload(file) {
    if (!file) return;
    const problem = validateMaterialFile(file);
    if (problem) {
      onError({ type: "danger", text: problem });
      return;
    }
    setUploading(true);
    try {
      await mentorApi.uploadMaterial(lesson.id, file);
      onChanged();
    } catch (err) {
      onError({ type: "danger", text: errorMessage(err, "Fayl yuklashda xatolik") });
    } finally {
      setUploading(false);
    }
  }

  async function handleDelete(material) {
    if (!window.confirm(`"${material.original_filename}" o'chirilsinmi?`)) return;
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

  function handleDrop(e) {
    e.preventDefault();
    setDragOver(false);
    upload(e.dataTransfer.files?.[0]);
  }

  return (
    <div className="card fade-in">
      <div className="row" style={{ gap: 8 }}>
        <span className="badge badge-neutral">{LESSON_TYPE_LABEL[lesson.type] || lesson.type}</span>
        <span className="chip">{lesson.moduleTitle}</span>
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
              <a
                href={material.file}
                target="_blank"
                rel="noreferrer"
                className="row small"
                style={{ gap: 7, color: "var(--text)", minWidth: 0 }}
              >
                <FileText width={15} height={15} style={{ flexShrink: 0 }} />
                <span className="strong" style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                  {material.original_filename}
                </span>
                <span className="dim" style={{ flexShrink: 0 }}>({formatSize(material.size_bytes)})</span>
              </a>
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

      <div
        className="mt-3"
        onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleDrop}
        style={{
          border: `1.5px dashed ${dragOver ? "var(--primary)" : "var(--border-strong)"}`,
          borderRadius: "var(--radius)",
          padding: 20,
          textAlign: "center",
          background: dragOver ? "var(--primary-soft)" : "var(--bg-subtle)",
          transition: "border-color 0.15s, background 0.15s",
        }}
      >
        <Upload width={20} height={20} className="dim" style={{ marginBottom: 6 }} />
        <p className="small muted">Faylni shu yerga tashlang yoki tanlang</p>

        <label className="btn btn-sm mt-3" style={{ cursor: "pointer" }}>
          {uploading ? <span className="spinner" /> : <Upload width={14} height={14} />}
          {materials.length > 0 ? "Yana fayl qo'shish" : "Fayl tanlash"}
          <input
            type="file"
            accept={MATERIAL_ACCEPT}
            onChange={(e) => { upload(e.target.files?.[0]); e.target.value = ""; }}
            style={{ display: "none" }}
            disabled={uploading}
          />
        </label>
      </div>

      <div className="alert alert-info mt-3" style={{ marginBottom: 0 }}>
        Ruxsat etilgan: PDF, PPT(X), DOC(X), XLS(X), ZIP, rasm (PNG/JPG/GIF), TXT —
        max {MAX_MATERIAL_SIZE_MB} MB. Video darsni Bunny Stream orqali alohida yuklash tavsiya etiladi.
      </div>
    </div>
  );
}

function formatSize(bytes) {
  if (!bytes) return "0 KB";
  if (bytes < 1024 * 1024) return `${Math.round(bytes / 1024)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}
