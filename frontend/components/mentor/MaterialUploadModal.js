"use client";

import { useState } from "react";
import { FileText, Upload, X } from "../Icons";
import { errorMessage, mentorApi } from "../../lib/api";
import { MATERIAL_ACCEPT, MATERIAL_KIND_OPTIONS, validateMaterialFile } from "../../lib/materials";

/**
 * Fayl tanlashdan oldin taqdimot/vazifa nomi va izohini so'raydigan forma.
 * Trigger sifatida `label` matnli tugma ko'rsatiladi; bosilganda modal ochiladi.
 */
export default function MaterialUploadModal({ lessonId, label = "Fayl tanlash", onUploaded }) {
  const [open, setOpen] = useState(false);
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [kind, setKind] = useState(null);
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [dragOver, setDragOver] = useState(false);
  const [error, setError] = useState(null);

  function reset() {
    setTitle("");
    setDescription("");
    setKind(null);
    setFile(null);
    setError(null);
    setDragOver(false);
  }

  function close() {
    if (uploading) return;
    setOpen(false);
    reset();
  }

  function pickFile(f) {
    if (!f) return;
    const problem = validateMaterialFile(f);
    if (problem) {
      setError(problem);
      return;
    }
    setError(null);
    setFile(f);
  }

  async function submit(e) {
    e.preventDefault();
    if (!title.trim()) {
      setError("Nomini kiriting");
      return;
    }
    if (!kind) {
      setError("Turini tanlang");
      return;
    }
    if (!file) {
      setError("Faylni tanlang");
      return;
    }
    setUploading(true);
    setError(null);
    try {
      await mentorApi.uploadMaterial(lessonId, file, { title: title.trim(), description: description.trim(), kind });
      onUploaded?.();
      setOpen(false);
      reset();
    } catch (err) {
      setError(errorMessage(err, "Fayl yuklashda xatolik"));
    } finally {
      setUploading(false);
    }
  }

  return (
    <>
      <button type="button" className="btn btn-ghost btn-sm" onClick={() => setOpen(true)}>
        <Upload width={14} height={14} />
        {label}
      </button>

      {open && (
        <div className="mum-overlay" onMouseDown={close}>
          <div className="card mum-modal" onMouseDown={(e) => e.stopPropagation()}>
            <div className="row-between">
              <h3 style={{ margin: 0 }}>Material yuklash</h3>
              <button type="button" className="btn btn-ghost btn-sm" onClick={close} disabled={uploading}>
                <X width={14} height={14} />
              </button>
            </div>

            <form onSubmit={submit} className="stack mt-3" style={{ gap: 10 }}>
              <div>
                <label className="small strong">Nomi (taqdimot yoki vazifa nomi)</label>
                <input
                  autoFocus
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="Masalan: 2-dars taqdimoti"
                  disabled={uploading}
                  style={{ marginTop: 4, marginBottom: 0 }}
                />
              </div>

              <div>
                <label className="small strong">Turi</label>
                <div className="row mt-1" style={{ gap: 6 }}>
                  {MATERIAL_KIND_OPTIONS.map((opt) => (
                    <button
                      key={opt.value}
                      type="button"
                      className={`btn btn-sm ${kind === opt.value ? "" : "btn-ghost"}`}
                      onClick={() => setKind(opt.value)}
                      disabled={uploading}
                    >
                      {opt.label}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="small strong">Izoh (ixtiyoriy)</label>
                <textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Material haqida qisqacha izoh"
                  rows={3}
                  disabled={uploading}
                  style={{ marginTop: 4, marginBottom: 0, resize: "vertical" }}
                />
              </div>

              <div>
                <label className="small strong">Fayl</label>
                <div
                  className="mt-1"
                  onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
                  onDragLeave={() => setDragOver(false)}
                  onDrop={(e) => { e.preventDefault(); setDragOver(false); pickFile(e.dataTransfer.files?.[0]); }}
                  style={{
                    border: `1.5px dashed ${dragOver ? "var(--primary)" : "var(--border-strong)"}`,
                    borderRadius: "var(--radius)",
                    padding: 16,
                    textAlign: "center",
                    background: dragOver ? "var(--primary-soft)" : "var(--bg-subtle)",
                  }}
                >
                  {file ? (
                    <div className="row" style={{ gap: 6, justifyContent: "center" }}>
                      <FileText width={15} height={15} />
                      <span className="small strong">{file.name}</span>
                    </div>
                  ) : (
                    <p className="small muted" style={{ margin: 0 }}>Faylni shu yerga tashlang yoki tanlang</p>
                  )}
                  <label className="btn btn-sm mt-2" style={{ cursor: "pointer" }}>
                    {file ? "Boshqa fayl tanlash" : "Fayl tanlash"}
                    <input
                      type="file"
                      accept={MATERIAL_ACCEPT}
                      onChange={(e) => { pickFile(e.target.files?.[0]); e.target.value = ""; }}
                      style={{ display: "none" }}
                      disabled={uploading}
                    />
                  </label>
                </div>
              </div>

              {error && <div className="alert alert-danger" style={{ marginBottom: 0 }}>{error}</div>}

              <div className="row" style={{ gap: 8, justifyContent: "flex-end" }}>
                <button type="button" className="btn btn-ghost btn-sm" onClick={close} disabled={uploading}>
                  Bekor qilish
                </button>
                <button type="submit" className="btn btn-sm" disabled={uploading}>
                  {uploading && <span className="spinner" />}
                  Yuklash
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      <style jsx>{`
        .mum-overlay {
          position: fixed;
          inset: 0;
          background: rgba(18, 20, 28, 0.45);
          display: flex;
          align-items: center;
          justify-content: center;
          z-index: 100;
          padding: 16px;
        }
        .mum-modal {
          width: 100%;
          max-width: 420px;
          max-height: 90vh;
          overflow-y: auto;
        }
      `}</style>
    </>
  );
}
