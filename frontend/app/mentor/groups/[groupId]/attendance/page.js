"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import AppShell from "../../../../../components/AppShell";
import { Check, ChevronRight, Users } from "../../../../../components/Icons";
import { useNotify } from "../../../../../components/NotificationProvider";
import { errorMessage, mentorApi } from "../../../../../lib/api";
import { initials, useAuth } from "../../../../../lib/auth";

/** Backend `AttendanceStatus` bilan mos. */
const STATUSES = [
  { value: "present", label: "Keldi", badge: "success" },
  { value: "late", label: "Kechikdi", badge: "warning" },
  { value: "excused", label: "Sababli", badge: "info" },
  { value: "absent", label: "Kelmadi", badge: "danger" },
];

function todayISO() {
  const now = new Date();
  const offset = now.getTimezoneOffset() * 60000;
  return new Date(now - offset).toISOString().slice(0, 10);
}

/** Guruhning kunlik davomati: sana tanlanadi, har bir o'quvchiga holat qo'yiladi. */
export default function GroupAttendancePage() {
  const { groupId } = useParams();
  const { user, loading } = useAuth({ roles: ["mentor"] });
  const notify = useNotify();

  const [group, setGroup] = useState(null);
  const [date, setDate] = useState(todayISO());
  const [sheet, setSheet] = useState([]);
  const [markedDates, setMarkedDates] = useState([]);
  const [summary, setSummary] = useState([]);
  const [draft, setDraft] = useState({});          // student_id -> status
  const [notes, setNotes] = useState({});          // student_id -> note
  const [dataLoading, setDataLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (loading) return;
    mentorApi
      .groups()
      .then(({ data }) => setGroup(data.find((g) => g.id === groupId) || null))
      .catch((err) => notify({ type: "danger", text: errorMessage(err) }));
  }, [loading, groupId, notify]);

  const load = useCallback(
    (forDate) => {
      setDataLoading(true);
      return mentorApi
        .attendance(groupId, forDate)
        .then(({ data }) => {
          setSheet(data.sheet);
          setMarkedDates(data.marked_dates);
          setSummary(data.summary);
          // Belgilanmaganlar standart "Keldi" — odatiy holat, mentor faqat
          // istisnolarni o'zgartiradi.
          setDraft(
            Object.fromEntries(data.sheet.map((r) => [r.student_id, r.status || "present"])),
          );
          setNotes(Object.fromEntries(data.sheet.map((r) => [r.student_id, r.note || ""])));
        })
        .catch((err) => notify({ type: "danger", text: errorMessage(err) }))
        .finally(() => setDataLoading(false));
    },
    [groupId, notify],
  );

  useEffect(() => {
    if (!loading) load(date);
  }, [loading, date, load]);

  async function save() {
    setSaving(true);
    try {
      const records = sheet.map((r) => ({
        student_id: r.student_id,
        status: draft[r.student_id],
        note: notes[r.student_id] || "",
      }));
      await mentorApi.markAttendance(groupId, date, records);
      notify({ type: "success", text: `${records.length} ta o'quvchi davomati saqlandi` });
      await load(date);
    } catch (err) {
      notify({ type: "danger", text: errorMessage(err, "Saqlashda xatolik") });
    } finally {
      setSaving(false);
    }
  }

  if (loading) {
    return <div className="app-shell"><main><div className="skeleton" style={{ height: 200 }} /></main></div>;
  }

  const alreadyMarked = markedDates.includes(date);
  const counts = STATUSES.map((s) => ({
    ...s,
    count: Object.values(draft).filter((v) => v === s.value).length,
  }));

  return (
    <AppShell user={user}>
      <div className="row small muted mb-2" style={{ gap: 4 }}>
        <Link href="/mentor/groups">Guruhlarim</Link>
        <ChevronRight width={13} height={13} />
        <span>{group?.name || "Guruh"}</span>
        <ChevronRight width={13} height={13} />
        <span>Davomat</span>
      </div>

      <div className="page-head">
        <div>
          <h1>Davomat — {group?.name || "…"}</h1>
          <p>Sanani tanlang va har bir o&apos;quvchining holatini belgilang</p>
        </div>
        {alreadyMarked && <span className="badge badge-success">Bu kun uchun olingan</span>}
      </div>

      <div className="card mb-3">
        <div className="row" style={{ gap: 16, alignItems: "flex-end", flexWrap: "wrap" }}>
          <div className="field" style={{ marginBottom: 0, width: 190 }}>
            <label htmlFor="att-date">Sana</label>
            <input
              id="att-date"
              type="date"
              value={date}
              max={todayISO()}
              onChange={(e) => setDate(e.target.value)}
            />
          </div>
          <div className="row" style={{ gap: 7 }}>
            {counts.map((c) => (
              <span key={c.value} className={`badge badge-${c.badge}`}>
                {c.label}: {c.count}
              </span>
            ))}
          </div>
        </div>
      </div>

      {dataLoading ? (
        <div className="skeleton" style={{ height: 240 }} />
      ) : sheet.length === 0 ? (
        <div className="card">
          <div className="empty">
            <div className="empty-icon"><Users /></div>
            <h3>Guruhda o&apos;quvchi yo&apos;q</h3>
            <p>So&apos;rovlarni tasdiqlaganingizdan keyin davomat olish mumkin bo&apos;ladi.</p>
          </div>
        </div>
      ) : (
        <>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>O&apos;quvchi</th>
                  <th style={{ width: 420 }}>Holat</th>
                  <th style={{ width: 220 }}>Izoh</th>
                </tr>
              </thead>
              <tbody>
                {sheet.map((row) => (
                  <tr key={row.student_id}>
                    <td>
                      <div className="row" style={{ gap: 10, flexWrap: "nowrap" }}>
                        <div className="avatar avatar-sm">{initials(row)}</div>
                        <div>
                          <div className="strong">{row.display_name}</div>
                          <div className="dim small">@{row.username}</div>
                        </div>
                      </div>
                    </td>
                    <td>
                      <div className="row" style={{ gap: 5, flexWrap: "nowrap" }}>
                        {STATUSES.map((s) => (
                          <button
                            key={s.value}
                            type="button"
                            className={`btn btn-sm ${draft[row.student_id] === s.value ? "" : "btn-ghost"}`}
                            onClick={() =>
                              setDraft((prev) => ({ ...prev, [row.student_id]: s.value }))
                            }
                          >
                            {s.label}
                          </button>
                        ))}
                      </div>
                    </td>
                    <td>
                      <input
                        value={notes[row.student_id] || ""}
                        onChange={(e) =>
                          setNotes((prev) => ({ ...prev, [row.student_id]: e.target.value }))
                        }
                        placeholder="ixtiyoriy"
                        style={{ marginBottom: 0 }}
                      />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="row mt-3">
            <button className="btn" onClick={save} disabled={saving}>
              {saving ? <span className="spinner" /> : <Check width={15} height={15} />}
              {alreadyMarked ? "Davomatni yangilash" : "Davomatni saqlash"}
            </button>
          </div>

          {summary.length > 0 && (
            <section className="card mt-3">
              <div className="card-head">
                <h2>Umumiy davomat</h2>
              </div>
              <div className="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>O&apos;quvchi</th>
                      <th style={{ width: 90 }}>Keldi</th>
                      <th style={{ width: 90 }}>Kechikdi</th>
                      <th style={{ width: 90 }}>Sababli</th>
                      <th style={{ width: 90 }}>Kelmadi</th>
                      <th style={{ width: 110 }}>Davomat</th>
                    </tr>
                  </thead>
                  <tbody>
                    {summary.map((s) => (
                      <tr key={s.student_id}>
                        <td className="strong">{s.display_name}</td>
                        <td>{s.present}</td>
                        <td>{s.late}</td>
                        <td>{s.excused}</td>
                        <td>{s.absent}</td>
                        <td>
                          {s.total === 0 ? (
                            <span className="dim">—</span>
                          ) : (
                            <span
                              className={`badge badge-${
                                s.attendance_percent >= 80
                                  ? "success"
                                  : s.attendance_percent >= 60
                                    ? "warning"
                                    : "danger"
                              }`}
                            >
                              {s.attendance_percent}%
                            </span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>
          )}

          {markedDates.length > 0 && (
            <div className="card mt-3">
              <div className="stat-label mb-2">Davomat olingan kunlar</div>
              <div className="row" style={{ gap: 6, flexWrap: "wrap" }}>
                {markedDates.map((d) => (
                  <button
                    key={d}
                    className={`btn btn-sm ${d === date ? "" : "btn-ghost"}`}
                    onClick={() => setDate(d)}
                  >
                    {new Date(d).toLocaleDateString("uz-UZ")}
                  </button>
                ))}
              </div>
            </div>
          )}
        </>
      )}
    </AppShell>
  );
}
