"use client";

import { useEffect, useState } from "react";
import { Send, X } from "../Icons";
import { errorMessage, mentorApi } from "../../lib/api";

/** Mentor darsga vazifa yuboradi: yo'riqnoma, muddat, ball va (ixtiyoriy) biriktirilgan material. */
export default function HomeworkSendModal({ lesson, sent, onSent }) {
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);

  const [instructions, setInstructions] = useState("");
  const [deadline, setDeadline] = useState("");
  const [maxScore, setMaxScore] = useState(100);
  const [materialId, setMaterialId] = useState("");

  useEffect(() => {
    if (!open || !sent) return;
    setLoading(true);
    mentorApi
      .homework(lesson.id)
      .then(({ data }) => {
        setInstructions(data.instructions || "");
        setDeadline(data.deadline_at ? data.deadline_at.slice(0, 16) : "");
        setMaxScore(data.max_score || 100);
        setMaterialId(data.material?.id || "");
      })
      .catch((err) => setError(errorMessage(err, "Yuklashda xatolik")))
      .finally(() => setLoading(false));
  }, [open, sent, lesson.id]);

  async function submit(e) {
    e.preventDefault();
    if (!instructions.trim()) {
      setError("Vazifa matnini kiriting");
      return;
    }
    setSaving(true);
    setError(null);
    try {
      await mentorApi.sendHomework(lesson.id, {
        instructions: instructions.trim(),
        deadlineAt: deadline ? new Date(deadline).toISOString() : null,
        maxScore: Number(maxScore) || 100,
        materialId: materialId || null,
      });
      onSent?.();
      setOpen(false);
    } catch (err) {
      setError(errorMessage(err, "Vazifa yuborishda xatolik"));
    } finally {
      setSaving(false);
    }
  }

  return (
    <>
      <button
        type="button"
        className={`btn btn-sm ${sent ? "btn-ghost" : ""}`}
        onClick={() => setOpen(true)}
      >
        <Send width={14} height={14} />
        {sent ? "Vazifani tahrirlash" : "Vazifa yuborish"}
      </button>

      {open && (
        <div className="hsm-overlay" onMouseDown={() => !saving && setOpen(false)}>
          <div className="card hsm-modal" onMouseDown={(e) => e.stopPropagation()}>
            <div className="row-between">
              <h3 style={{ margin: 0 }}>Vazifa yuborish</h3>
              <button type="button" className="btn btn-ghost btn-sm" onClick={() => setOpen(false)} disabled={saving}>
                <X width={14} height={14} />
              </button>
            </div>
            <p className="small muted mt-1">
              {lesson.title} — yuborilgach, kursga yozilgan barcha o&apos;quvchilarga &quot;Vazifalarim&quot;
              bo&apos;limida ko&apos;rinadi
            </p>

            {loading ? (
              <div className="skeleton mt-3" style={{ height: 160 }} />
            ) : (
              <form onSubmit={submit} className="stack mt-3" style={{ gap: 10 }}>
                <div>
                  <label className="small strong">Vazifa matni</label>
                  <textarea
                    autoFocus
                    value={instructions}
                    onChange={(e) => setInstructions(e.target.value)}
                    placeholder="O'quvchi nima qilishi kerakligini yozing…"
                    rows={4}
                    disabled={saving}
                    style={{ marginTop: 4, marginBottom: 0, resize: "vertical" }}
                  />
                </div>

                <div className="row" style={{ gap: 10 }}>
                  <div className="field" style={{ flex: 1, marginBottom: 0 }}>
                    <label>Muddat (ixtiyoriy)</label>
                    <input
                      type="datetime-local"
                      value={deadline}
                      onChange={(e) => setDeadline(e.target.value)}
                      disabled={saving}
                    />
                  </div>
                  <div className="field" style={{ width: 110, marginBottom: 0 }}>
                    <label>Max ball</label>
                    <input
                      type="number"
                      min={1}
                      value={maxScore}
                      onChange={(e) => setMaxScore(e.target.value)}
                      disabled={saving}
                    />
                  </div>
                </div>

                <div className="field" style={{ marginBottom: 0 }}>
                  <label>Material biriktirish (ixtiyoriy)</label>
                  <select value={materialId} onChange={(e) => setMaterialId(e.target.value)} disabled={saving}>
                    <option value="">Materialsiz — faqat vazifaning o&apos;zi</option>
                    {(lesson.materials || []).map((m) => (
                      <option key={m.id} value={m.id}>
                        {m.kind === "presentation" ? "Taqdimot" : "Vazifa"}: {m.title || m.original_filename}
                      </option>
                    ))}
                  </select>
                </div>

                {error && <div className="alert alert-danger" style={{ marginBottom: 0 }}>{error}</div>}

                <div className="row" style={{ gap: 8, justifyContent: "flex-end" }}>
                  <button type="button" className="btn btn-ghost btn-sm" onClick={() => setOpen(false)} disabled={saving}>
                    Bekor qilish
                  </button>
                  <button type="submit" className="btn btn-sm" disabled={saving}>
                    {saving && <span className="spinner" />}
                    <Send width={14} height={14} />
                    Yuborish
                  </button>
                </div>
              </form>
            )}
          </div>
        </div>
      )}

      <style jsx>{`
        .hsm-overlay {
          position: fixed;
          inset: 0;
          background: rgba(18, 20, 28, 0.45);
          display: flex;
          align-items: center;
          justify-content: center;
          z-index: 100;
          padding: 16px;
        }
        .hsm-modal {
          width: 100%;
          max-width: 460px;
          max-height: 90vh;
          overflow-y: auto;
        }
      `}</style>
    </>
  );
}
