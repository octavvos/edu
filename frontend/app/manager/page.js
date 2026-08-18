"use client";

import { useCallback, useEffect, useState } from "react";
import AppShell from "../../components/AppShell";
import { Calendar, Plus, Users, X } from "../../components/Icons";
import { catalogApi, errorMessage, managerApi } from "../../lib/api";
import { useAuth } from "../../lib/auth";

const WEEKDAYS = [
  { value: 0, label: "Dushanba" },
  { value: 1, label: "Seshanba" },
  { value: 2, label: "Chorshanba" },
  { value: 3, label: "Payshanba" },
  { value: 4, label: "Juma" },
  { value: 5, label: "Shanba" },
  { value: 6, label: "Yakshanba" },
];

/** Manager paneli: kurs guruhlarini ochish va dars vaqtlarini belgilash. */
export default function ManagerPage() {
  const { user, loading } = useAuth({ roles: ["manager"] });
  const [groups, setGroups] = useState([]);
  const [courses, setCourses] = useState([]);
  const [dataLoading, setDataLoading] = useState(true);
  const [message, setMessage] = useState(null);
  const [creating, setCreating] = useState(false);
  const [scheduleFor, setScheduleFor] = useState(null);

  const load = useCallback(() => {
    return managerApi
      .groups()
      .then(({ data }) => setGroups(data))
      .catch((err) => setMessage({ type: "danger", text: errorMessage(err) }));
  }, []);

  useEffect(() => {
    if (loading) return;
    Promise.all([
      load(),
      catalogApi
        .courses()
        .then(({ data }) => setCourses(data.results || data))
        .catch(() => {}),
    ]).finally(() => setDataLoading(false));
  }, [loading, load]);

  if (loading) return <div className="app-shell"><main><div className="skeleton" style={{ height: 200 }} /></main></div>;

  return (
    <AppShell user={user}>
      <div className="page-head">
        <div>
          <h1>Guruhlarni boshqarish</h1>
          <p>Guruh oching, dars vaqtlarini belgilang va mentor biriktiring</p>
        </div>
        <button className="btn" onClick={() => setCreating((v) => !v)}>
          {creating ? <X width={15} height={15} /> : <Plus width={15} height={15} />}
          {creating ? "Bekor qilish" : "Yangi guruh"}
        </button>
      </div>

      {message && <div className={`alert alert-${message.type}`}>{message.text}</div>}

      {creating && (
        <CreateGroupForm
          courses={courses}
          onCancel={() => setCreating(false)}
          onCreated={async (name) => {
            setCreating(false);
            setMessage({ type: "success", text: `"${name}" guruhi yaratildi` });
            await load();
          }}
          onError={(text) => setMessage({ type: "danger", text })}
        />
      )}

      {dataLoading ? (
        <div className="grid">
          <div className="skeleton" style={{ height: 170 }} />
          <div className="skeleton" style={{ height: 170 }} />
        </div>
      ) : groups.length === 0 ? (
        <div className="card">
          <div className="empty">
            <div className="empty-icon"><Users /></div>
            <h3>Hali guruh yo&apos;q</h3>
            <p>&laquo;Yangi guruh&raquo; tugmasi orqali birinchi guruhni oching.</p>
          </div>
        </div>
      ) : (
        <div className="grid">
          {groups.map((group) => (
            <article key={group.id} className="card card-hover fade-in">
              <div className="row-between" style={{ alignItems: "flex-start" }}>
                <div>
                  <h3>{group.name}</h3>
                  <div className="small muted mt-1">{group.course_title}</div>
                </div>
                <span className={`badge badge-${group.is_active ? "success" : "neutral"}`}>
                  {group.is_active ? "Faol" : "Yopiq"}
                </span>
              </div>

              <div className="row mt-2" style={{ gap: 7 }}>
                <span className="chip">{group.code}</span>
                <span className="chip">
                  <Users width={13} height={13} />
                  {group.active_members_count} / {group.capacity}
                </span>
                <span className="chip">Mentor: {group.mentor_name || "yo'q"}</span>
              </div>

              <div className="mt-2">
                <div className="stat-label mb-2">Dars vaqtlari</div>
                {group.schedules.length ? (
                  <div className="schedule-list">
                    {group.schedules.map((s) => (
                      <div key={s.id} className="schedule-item" style={{ padding: "8px 12px" }}>
                        <span className="schedule-day small">{s.weekday_label}</span>
                        <span className="schedule-time mono small">
                          {s.start_time.slice(0, 5)} – {s.end_time.slice(0, 5)}
                        </span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="small dim">Belgilanmagan</p>
                )}
              </div>

              <button
                className="btn btn-ghost btn-sm mt-2"
                onClick={() => setScheduleFor(scheduleFor === group.id ? null : group.id)}
              >
                <Calendar width={15} height={15} />
                {scheduleFor === group.id ? "Yopish" : "Dars vaqtlarini belgilash"}
              </button>

              {scheduleFor === group.id && (
                <ScheduleEditor
                  group={group}
                  onSaved={async () => {
                    setScheduleFor(null);
                    setMessage({ type: "success", text: `"${group.name}" jadvali yangilandi` });
                    await load();
                  }}
                  onError={(text) => setMessage({ type: "danger", text })}
                />
              )}
            </article>
          ))}
        </div>
      )}
    </AppShell>
  );
}

// ---------------------------------------------------------------------------

function CreateGroupForm({ courses, onCancel, onCreated, onError }) {
  const [form, setForm] = useState({ course_id: "", name: "", code: "", capacity: 25 });
  const [saving, setSaving] = useState(false);

  function update(key, value) {
    setForm((prev) => ({ ...prev, [key]: value }));
  }

  async function submit(e) {
    e.preventDefault();
    setSaving(true);
    try {
      await managerApi.createGroup({ ...form, capacity: Number(form.capacity) });
      onCreated(form.name);
    } catch (err) {
      onError(errorMessage(err, "Guruh yaratishda xatolik"));
    } finally {
      setSaving(false);
    }
  }

  return (
    <form className="card mb-3 fade-in" onSubmit={submit}>
      <div className="card-head">
        <h2>Yangi guruh</h2>
      </div>

      <div className="field">
        <label htmlFor="course">Kurs</label>
        <select
          id="course"
          value={form.course_id}
          onChange={(e) => update("course_id", e.target.value)}
          required
        >
          <option value="">Kursni tanlang…</option>
          {courses.map((c) => (
            <option key={c.id} value={c.id}>
              {c.title || c.slug}
            </option>
          ))}
        </select>
      </div>

      <div className="field-row">
        <div className="field">
          <label htmlFor="name">Guruh nomi</label>
          <input
            id="name"
            value={form.name}
            onChange={(e) => update("name", e.target.value)}
            placeholder="Frontend — kechki"
            required
          />
        </div>
        <div className="field">
          <label htmlFor="code">Kod</label>
          <input
            id="code"
            value={form.code}
            onChange={(e) => update("code", e.target.value.toLowerCase())}
            placeholder="frontend-04"
            pattern="[a-z0-9\-]+"
            required
          />
        </div>
      </div>

      <div className="field" style={{ maxWidth: 180 }}>
        <label htmlFor="capacity">Sig&apos;im</label>
        <input
          id="capacity"
          type="number"
          min={1}
          max={500}
          value={form.capacity}
          onChange={(e) => update("capacity", e.target.value)}
          required
        />
      </div>

      <div className="row">
        <button className="btn" type="submit" disabled={saving}>
          {saving && <span className="spinner" />}
          Guruh ochish
        </button>
        <button className="btn btn-ghost" type="button" onClick={onCancel}>
          Bekor qilish
        </button>
      </div>
    </form>
  );
}

// ---------------------------------------------------------------------------

function ScheduleEditor({ group, onSaved, onError }) {
  const [slots, setSlots] = useState(
    group.schedules.length
      ? group.schedules.map((s) => ({
          weekday: s.weekday,
          start_time: s.start_time.slice(0, 5),
          end_time: s.end_time.slice(0, 5),
          room: s.room || "",
        }))
      : [{ weekday: 0, start_time: "18:00", end_time: "20:00", room: "" }],
  );
  const [saving, setSaving] = useState(false);

  function updateSlot(index, key, value) {
    setSlots((prev) => prev.map((s, i) => (i === index ? { ...s, [key]: value } : s)));
  }

  async function save() {
    setSaving(true);
    try {
      await managerApi.setSchedule(
        group.id,
        slots.map((s) => ({ ...s, weekday: Number(s.weekday) })),
      );
      onSaved();
    } catch (err) {
      onError(errorMessage(err, "Jadvalni saqlashda xatolik"));
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="mt-2 fade-in" style={{ borderTop: "1px solid var(--border)", paddingTop: 14 }}>
      <div className="stack" style={{ gap: 9 }}>
        {slots.map((slot, i) => (
          <div key={i} className="row" style={{ gap: 7, flexWrap: "nowrap" }}>
            <select
              value={slot.weekday}
              onChange={(e) => updateSlot(i, "weekday", e.target.value)}
              style={{ flex: "1 1 130px" }}
            >
              {WEEKDAYS.map((d) => (
                <option key={d.value} value={d.value}>
                  {d.label}
                </option>
              ))}
            </select>
            <input
              type="time"
              value={slot.start_time}
              onChange={(e) => updateSlot(i, "start_time", e.target.value)}
              style={{ flex: "0 1 110px" }}
            />
            <input
              type="time"
              value={slot.end_time}
              onChange={(e) => updateSlot(i, "end_time", e.target.value)}
              style={{ flex: "0 1 110px" }}
            />
            <button
              type="button"
              className="btn btn-danger-ghost btn-sm"
              onClick={() => setSlots((prev) => prev.filter((_, idx) => idx !== i))}
              disabled={slots.length === 1}
              title="O'chirish"
            >
              <X width={14} height={14} />
            </button>
          </div>
        ))}
      </div>

      <div className="row mt-2">
        <button
          type="button"
          className="btn btn-ghost btn-sm"
          onClick={() =>
            setSlots((prev) => [...prev, { weekday: 0, start_time: "18:00", end_time: "20:00", room: "" }])
          }
        >
          <Plus width={14} height={14} /> Vaqt qo&apos;shish
        </button>
        <button type="button" className="btn btn-sm" onClick={save} disabled={saving}>
          {saving && <span className="spinner" />}
          Saqlash
        </button>
      </div>
    </div>
  );
}
