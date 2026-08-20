"use client";

import { useState } from "react";
import Link from "next/link";
import { ChevronDown, ChevronRight, FileText, Plus, X } from "../Icons";
import { errorMessage, mentorApi } from "../../lib/api";
import { MATERIAL_KIND_LABEL, formatFileSize } from "../../lib/materials";
import HomeworkSendModal from "./HomeworkSendModal";
import MaterialLink from "./MaterialLink";
import MaterialUploadModal from "./MaterialUploadModal";

const LESSON_TYPES = [
  { value: "text", label: "Matnli dars" },
  { value: "video", label: "Video dars" },
  { value: "file", label: "Fayl / material" },
  { value: "quiz", label: "Test" },
  { value: "homework", label: "Uy vazifasi" },
];

// Test turidagi darslar endi "Testlar" bo'limida yaratiladi — bu yerdan tanlab bo'lmaydi
const CREATABLE_LESSON_TYPES = LESSON_TYPES.filter((t) => t.value !== "quiz");

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
        {CREATABLE_LESSON_TYPES.map((t) => (
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
  const [detailsOpen, setDetailsOpen] = useState(false);

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
          {lesson.sent_to_groups?.map((g) => (
            <span key={g.id} className="badge badge-success">{g.name}</span>
          ))}
        </button>

        {/* Vazifa istalgan darsga jo'natilishi mumkin — dars turi bilan bog'liq emas */}
        <div className="row" style={{ gap: 6, flexWrap: "nowrap" }}>
          <HomeworkSendModal lesson={lesson} sentGroups={lesson.sent_to_groups || []} onSent={onChanged} />
          {lesson.type !== "quiz" && (
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
            <MaterialLink
              key={material.id}
              material={material}
              className="row small"
              style={{ gap: 6, color: "var(--text-secondary)" }}
            >
              <FileText width={14} height={14} />
              {material.title || material.original_filename}
              <span className="chip" style={{ fontSize: 11 }}>
                {MATERIAL_KIND_LABEL[material.kind] || material.kind}
              </span>
              <span className="dim">({formatFileSize(material.size_bytes)})</span>
            </MaterialLink>
          ))}
        </div>
      )}

      {lesson.type === "quiz" && (
        <p className="small dim mt-2">
          Bu test <Link href="/mentor/tests">Testlar</Link> bo&apos;limida boshqariladi.
        </p>
      )}
    </div>
  );
}

function typeLabel(type) {
  return LESSON_TYPES.find((t) => t.value === type)?.label || type;
}
