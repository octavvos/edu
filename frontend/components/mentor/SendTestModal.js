"use client";

import { useEffect, useState } from "react";
import { Send, X } from "../Icons";
import { errorMessage, mentorApi } from "../../lib/api";

/**
 * Mentor tanlagan guruh(lar)ga testni jo'natadi. Test faqat shu guruh
 * o'quvchilariga ko'rinadi — kursga yozilganlarning barchasiga emas.
 */
export default function SendTestModal({ lesson, sentGroups = [], onSent }) {
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(null); // yuborilayotgan/bekor qilinayotgan guruh id
  const [error, setError] = useState(null);
  const [groups, setGroups] = useState([]);
  const [existing, setExisting] = useState([]);

  useEffect(() => {
    if (!open) return;
    setLoading(true);
    Promise.all([mentorApi.groups(), mentorApi.testAssignments(lesson.id)])
      .then(([groupsRes, assignRes]) => {
        setGroups(groupsRes.data);
        setExisting(assignRes.data);
      })
      .catch((err) => setError(errorMessage(err, "Yuklashda xatolik")))
      .finally(() => setLoading(false));
  }, [open, lesson.id]);

  function close() {
    if (saving) return;
    setOpen(false);
    setError(null);
  }

  async function send(groupId) {
    setSaving(groupId);
    setError(null);
    try {
      const { data } = await mentorApi.sendTest(lesson.id, groupId);
      setExisting((prev) => [...prev, data]);
      onSent?.();
    } catch (err) {
      setError(errorMessage(err, "Test jo'natishda xatolik"));
    } finally {
      setSaving(null);
    }
  }

  async function unsend(groupId) {
    setSaving(groupId);
    setError(null);
    try {
      await mentorApi.unsendTest(lesson.id, groupId);
      setExisting((prev) => prev.filter((a) => a.group !== groupId));
      onSent?.();
    } catch (err) {
      setError(errorMessage(err, "Bekor qilishda xatolik"));
    } finally {
      setSaving(null);
    }
  }

  return (
    <>
      <button
        type="button"
        className={`btn btn-sm ${sentGroups.length ? "btn-ghost" : ""}`}
        onClick={() => setOpen(true)}
      >
        <Send width={14} height={14} />
        {sentGroups.length ? "Guruhlarni boshqarish" : "Guruhga yuborish"}
      </button>

      {open && (
        <div className="hsm-overlay" onMouseDown={close}>
          <div className="card hsm-modal" onMouseDown={(e) => e.stopPropagation()}>
            <div className="row-between">
              <h3 style={{ margin: 0 }}>Testni guruhga yuborish</h3>
              <button type="button" className="btn btn-ghost btn-sm" onClick={close}>
                <X width={14} height={14} />
              </button>
            </div>
            <p className="small muted mt-1">
              {lesson.title} — test faqat tanlangan guruh o&apos;quvchilariga ko&apos;rinadi
            </p>

            {loading ? (
              <div className="skeleton mt-3" style={{ height: 120 }} />
            ) : groups.length === 0 ? (
              <p className="small dim mt-3">Sizga hech qanday guruh biriktirilmagan.</p>
            ) : (
              <div className="stack mt-3" style={{ gap: 6 }}>
                {groups.map((g) => {
                  const sent = existing.some((a) => a.group === g.id);
                  return (
                    <div key={g.id} className="row-between card-compact" style={{ background: "var(--bg-subtle)" }}>
                      <span className="small strong">{g.name}</span>
                      {sent ? (
                        <button
                          type="button"
                          className="btn btn-ghost btn-sm"
                          onClick={() => unsend(g.id)}
                          disabled={saving === g.id}
                        >
                          {saving === g.id ? <span className="spinner" /> : <X width={13} height={13} />}
                          Bekor qilish
                        </button>
                      ) : (
                        <button
                          type="button"
                          className="btn btn-sm"
                          onClick={() => send(g.id)}
                          disabled={saving === g.id}
                        >
                          {saving === g.id ? <span className="spinner" /> : <Send width={13} height={13} />}
                          Yuborish
                        </button>
                      )}
                    </div>
                  );
                })}
              </div>
            )}

            {error && <div className="alert alert-danger mt-2" style={{ marginBottom: 0 }}>{error}</div>}
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
          max-width: 420px;
          max-height: 90vh;
          overflow-y: auto;
        }
      `}</style>
    </>
  );
}
