"use client";

import { useEffect, useState } from "react";
import { Send, X } from "../Icons";
import { errorMessage, mentorApi } from "../../lib/api";

/**
 * Mentor tanlangan guruhga vazifa jo'natadi: guruh, yo'riqnoma, muddat, ball
 * va (ixtiyoriy) biriktirilgan material. Vazifa faqat o'sha guruh
 * o'quvchilariga ko'rinadi — bitta kursni bir necha guruh baham ko'radi.
 */
export default function HomeworkSendModal({ lesson, sentGroups = [], onSent }) {
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);

  const [groups, setGroups] = useState([]);
  const [groupId, setGroupId] = useState("");
  const [instructions, setInstructions] = useState("");
  const [deadline, setDeadline] = useState("");
  const [maxScore, setMaxScore] = useState(100);
  const [materialId, setMaterialId] = useState("");
  const [existing, setExisting] = useState([]);

  // Guruhlar va shu darsga allaqachon jo'natilgan vazifalar
  useEffect(() => {
    if (!open) return;
    setLoading(true);
    Promise.all([mentorApi.groups(), mentorApi.homework(lesson.id)])
      .then(([groupsRes, hwRes]) => {
        const courseGroups = groupsRes.data;
        setGroups(courseGroups);
        setExisting(hwRes.data);
        setGroupId((prev) => prev || courseGroups[0]?.id || "");
      })
      .catch((err) => setError(errorMessage(err, "Yuklashda xatolik")))
      .finally(() => setLoading(false));
  }, [open, lesson.id]);

  // Guruh almashtirilganda — o'sha guruhga avval jo'natilgan bo'lsa, formani to'ldiramiz
  useEffect(() => {
    if (!groupId) return;
    const previous = existing.find((hw) => hw.group === groupId);
    setInstructions(previous?.instructions || "");
    setDeadline(previous?.deadline_at ? previous.deadline_at.slice(0, 16) : "");
    setMaxScore(previous?.max_score || 100);
    setMaterialId(previous?.material?.id || "");
  }, [groupId, existing]);

  function close() {
    if (saving) return;
    setOpen(false);
    setError(null);
  }

  async function submit(e) {
    e.preventDefault();
    if (!groupId) {
      setError("Guruhni tanlang");
      return;
    }
    if (!instructions.trim()) {
      setError("Vazifa matnini kiriting");
      return;
    }
    setSaving(true);
    setError(null);
    try {
      await mentorApi.sendHomework(lesson.id, {
        groupId,
        instructions: instructions.trim(),
        deadlineAt: deadline ? new Date(deadline).toISOString() : null,
        maxScore: Number(maxScore) || 100,
        materialId: materialId || null,
      });
      onSent?.();
      setOpen(false);
    } catch (err) {
      setError(errorMessage(err, "Vazifa jo'natishda xatolik"));
    } finally {
      setSaving(false);
    }
  }

  const alreadySent = existing.some((hw) => hw.group === groupId);

  return (
    <>
      <button
        type="button"
        className={`btn btn-sm ${sentGroups.length ? "btn-ghost" : ""}`}
        onClick={() => setOpen(true)}
      >
        <Send width={14} height={14} />
        {sentGroups.length ? "Yana jo'natish" : "Vazifa jo'natish"}
      </button>

      {open && (
        <div className="hsm-overlay" onMouseDown={close}>
          <div className="card hsm-modal" onMouseDown={(e) => e.stopPropagation()}>
            <div className="row-between">
              <h3 style={{ margin: 0 }}>Vazifa jo&apos;natish</h3>
              <button type="button" className="btn btn-ghost btn-sm" onClick={close} disabled={saving}>
                <X width={14} height={14} />
              </button>
            </div>
            <p className="small muted mt-1">
              {lesson.title} — vazifa faqat tanlangan guruh o&apos;quvchilariga ko&apos;rinadi
            </p>

            {loading ? (
              <div className="skeleton mt-3" style={{ height: 200 }} />
            ) : (
              <form onSubmit={submit} className="stack mt-3" style={{ gap: 10 }}>
                <div className="field" style={{ marginBottom: 0 }}>
                  <label>Guruh</label>
                  <select value={groupId} onChange={(e) => setGroupId(e.target.value)} disabled={saving}>
                    {groups.map((g) => (
                      <option key={g.id} value={g.id}>
                        {g.name}
                        {existing.some((hw) => hw.group === g.id) ? " — jo'natilgan" : ""}
                      </option>
                    ))}
                  </select>
                </div>

                {alreadySent && (
                  <div className="alert alert-info" style={{ marginBottom: 0 }}>
                    Bu guruhga allaqachon jo&apos;natilgan — saqlasangiz yangilanadi.
                  </div>
                )}

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
                  <label>Taqdimot / material biriktirish (ixtiyoriy)</label>
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
                  <button type="button" className="btn btn-ghost btn-sm" onClick={close} disabled={saving}>
                    Bekor qilish
                  </button>
                  <button type="submit" className="btn btn-sm" disabled={saving}>
                    {saving && <span className="spinner" />}
                    <Send width={14} height={14} />
                    Jo&apos;natish
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
