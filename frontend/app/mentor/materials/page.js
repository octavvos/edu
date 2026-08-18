"use client";

import { useCallback, useEffect, useState } from "react";
import AppShell from "../../../components/AppShell";
import { Book, ChevronDown, ChevronRight, FileText, Upload } from "../../../components/Icons";
import { errorMessage, mentorApi } from "../../../lib/api";
import { useAuth } from "../../../lib/auth";

const LESSON_TYPE_LABEL = {
  text: "Matnli dars",
  video: "Video dars",
  file: "Fayl / material",
  quiz: "Test",
  homework: "Uy vazifasi",
};

/** Barcha dars rejalar bittalab ro'yxatda — har biriga material yuklash tugmasi bilan. */
export default function MentorMaterialsPage() {
  const { user, loading } = useAuth({ roles: ["mentor"] });
  const [courses, setCourses] = useState([]);
  const [courseId, setCourseId] = useState(null);
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
  const totalLessons = course?.modules.reduce((sum, m) => sum + m.lessons.length, 0) || 0;
  const uploadedCount = course?.modules.reduce(
    (sum, m) => sum + m.lessons.filter((l) => l.file_asset).length, 0,
  ) || 0;

  return (
    <AppShell user={user}>
      <div className="page-head">
        <div>
          <h1>Materiallar</h1>
          <p>Har bir dars rejasiga fayl material yuklang</p>
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
                  onClick={() => setCourseId(c.id)}
                >
                  {c.title}
                </button>
              ))}
            </div>
          )}

          {course && (
            <div className="stack" style={{ gap: 10 }}>
              {course.modules.map((module) => (
                <ModuleMaterials key={module.id} module={module} onChanged={load} onError={setMessage} />
              ))}
            </div>
          )}
        </>
      )}
    </AppShell>
  );
}

function ModuleMaterials({ module, onChanged, onError }) {
  const [open, setOpen] = useState(true);
  const uploaded = module.lessons.filter((l) => l.file_asset).length;

  return (
    <section className="card">
      <button
        className="row-between"
        style={{ width: "100%", background: "none", border: "none", cursor: "pointer", padding: 0, textAlign: "left" }}
        onClick={() => setOpen((v) => !v)}
      >
        <div className="row" style={{ gap: 8 }}>
          {open ? <ChevronDown width={16} height={16} /> : <ChevronRight width={16} height={16} />}
          <strong>{module.title}</strong>
        </div>
        <span className="chip">{uploaded} / {module.lessons.length} darsda material</span>
      </button>

      {open && (
        <div className="stack mt-2" style={{ gap: 6 }}>
          {module.lessons.length === 0 ? (
            <p className="small dim">Bu bo&apos;limda dars yo&apos;q.</p>
          ) : (
            module.lessons.map((lesson) => (
              <MaterialRow key={lesson.id} lesson={lesson} onChanged={onChanged} onError={onError} />
            ))
          )}
        </div>
      )}
    </section>
  );
}

function MaterialRow({ lesson, onChanged, onError }) {
  const [uploading, setUploading] = useState(false);

  async function handleFileChange(e) {
    const file = e.target.files?.[0];
    e.target.value = "";
    if (!file) return;
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

  return (
    <div className="row-between" style={{
      padding: "10px 13px", background: "var(--bg-subtle)", borderRadius: "var(--radius)",
      gap: 10, flexWrap: "wrap",
    }}>
      <div style={{ minWidth: 0, flex: 1 }}>
        <div className="row" style={{ gap: 8 }}>
          <span className="badge badge-neutral">{LESSON_TYPE_LABEL[lesson.type] || lesson.type}</span>
          <span className="small strong">{lesson.title}</span>
        </div>
        {lesson.file_asset && (
          <a
            href={lesson.file_asset.file}
            target="_blank"
            rel="noreferrer"
            className="row mt-1 small"
            style={{ gap: 5, color: "var(--text-secondary)" }}
          >
            <FileText width={13} height={13} />
            {lesson.file_asset.original_filename}
            <span className="dim">({formatSize(lesson.file_asset.size_bytes)})</span>
          </a>
        )}
      </div>

      <label className={`btn btn-sm ${lesson.file_asset ? "btn-ghost" : ""}`} style={{ cursor: "pointer" }}>
        {uploading ? <span className="spinner" /> : <Upload width={14} height={14} />}
        {lesson.file_asset ? "Almashtirish" : "Material yuklash"}
        <input type="file" onChange={handleFileChange} style={{ display: "none" }} disabled={uploading} />
      </label>
    </div>
  );
}

function formatSize(bytes) {
  if (!bytes) return "0 KB";
  if (bytes < 1024 * 1024) return `${Math.round(bytes / 1024)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}
